"""Backend: the Claude Code CLI, headless (`claude -p`).

Uses the existing Claude Code login, so no API key is involved. The call is
kept lean: no tools, no MCP servers, no settings/CLAUDE.md, no saved session;
only our system prompt, the schema and the notes.
"""

import json
import shutil
import subprocess
import tempfile

from ..config import Config
from . import SYSTEM_PROMPT, LLMError, document_schema_json


def command(config: Config) -> list[str]:
    cmd = [
        "claude", "-p",
        "--output-format", "json",
        "--json-schema", document_schema_json(),
        "--system-prompt", SYSTEM_PROMPT,
        "--tools", "",
        "--strict-mcp-config",
        "--setting-sources", "",
        "--disable-slash-commands",
        "--no-session-persistence",
    ]
    if config.model:
        cmd += ["--model", config.model]
    if config.effort:
        cmd += ["--effort", config.effort]
    return cmd


def run(raw: str, config: Config) -> dict:
    if shutil.which("claude") is None:
        raise LLMError("The 'claude' command was not found. Install Claude Code and log in.")
    # Run in an empty directory so no project files or CLAUDE.md are picked up.
    with tempfile.TemporaryDirectory(prefix="school-notes-llm-") as cwd:
        try:
            proc = subprocess.run(
                command(config), input=raw, cwd=cwd, capture_output=True,
                text=True, timeout=config.timeout,
            )
        except subprocess.TimeoutExpired:
            raise LLMError(f"claude did not answer within {config.timeout:.0f} s") from None
    try:
        reply = json.loads(proc.stdout)
    except json.JSONDecodeError:
        detail = (proc.stderr or proc.stdout).strip()[-800:]
        raise LLMError(f"claude failed (exit {proc.returncode}): {detail}") from None
    if reply.get("is_error") or reply.get("subtype") != "success":
        raise LLMError(f"claude reported an error: {str(reply.get('result', reply))[:800]}")
    data = reply.get("structured_output")
    if data is None:  # fall back to the text result
        try:
            data = json.loads(reply.get("result", ""))
        except json.JSONDecodeError:
            raise LLMError("claude returned no structured output") from None
    return data
