"""Backend: the Claude Code CLI, headless (`claude -p`).

Uses the existing Claude Code login, so no API key is involved. The call is
kept lean: no tools, no MCP servers, no settings/CLAUDE.md, no saved session;
only our system prompt, the schema and the notes.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ..config import Config
from . import SYSTEM_PROMPT, LLMError, document_schema_json
from .usage import Usage


def find_claude() -> str | None:
    """The claude binary. Apps started from the menu may not have ~/.local/bin
    in PATH, so also look where the Claude Code installer puts it."""
    found = shutil.which("claude")
    if found:
        return found
    for candidate in (Path.home() / ".local" / "bin" / "claude", Path.home() / ".claude" / "local" / "claude"):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def command(config: Config) -> list[str]:
    cmd = [
        find_claude() or "claude", "-p",
        # stream-json (+ --verbose) also carries the rate_limit_event with the
        # plan's 5-hour and weekly usage; plain json doesn't.
        "--output-format", "stream-json", "--verbose",
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
    if find_claude() is None:
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
    return parse_stream(proc.stdout, proc.returncode, proc.stderr)


def parse_stream(stdout: str, returncode: int = 0, stderr: str = "") -> tuple[dict, Usage]:
    """Read the stream-json lines: the final result and the rate-limit info."""
    result, rate_limit = None, None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "result":
            result = event
        elif event.get("type") == "rate_limit_event":
            rate_limit = event.get("rate_limit_info")
    if result is None:
        detail = (stderr or stdout).strip()[-800:]
        raise LLMError(f"claude failed (exit {returncode}): {detail}")
    if result.get("is_error") or result.get("subtype") != "success":
        raise LLMError(f"claude reported an error: {str(result.get('result', result))[:800]}")
    data = result.get("structured_output")
    if data is None:  # fall back to the text result
        try:
            data = json.loads(result.get("result", ""))
        except json.JSONDecodeError:
            raise LLMError("claude returned no structured output") from None
    return data, Usage.from_stream(result, rate_limit)
