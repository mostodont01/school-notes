"""LLM backends: raw notes -> validated Document.

Every backend gets the same system prompt (prompt.md) and the same JSON
schema (exported from notes_app.schema), and every result is validated with
Pydantic, so the renderer only ever sees a valid Document.
"""

import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from ..config import Config, load_config
from ..schema import Document
from .usage import Usage, load_usage, save_usage

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.md").read_text(encoding="utf-8")


class LLMError(RuntimeError):
    """The backend failed or returned something that is not a valid Document."""


def _strip(node, in_properties: bool = False):
    """Drop schema annotations that only add noise for the model ("title",
    "discriminator"). Keys of a "properties" map are field names, not
    annotations, so a field called "title" is kept."""
    if isinstance(node, dict):
        return {
            k: _strip(v, in_properties=(k == "properties" and not in_properties))
            for k, v in node.items()
            if in_properties or k not in ("title", "discriminator")
        }
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def document_schema() -> dict:
    return _strip(Document.model_json_schema())


def document_schema_json() -> str:
    return json.dumps(document_schema(), ensure_ascii=False, separators=(",", ":"))


def validate(data: dict | str) -> Document:
    try:
        if isinstance(data, str):
            return Document.model_validate_json(data)
        return Document.model_validate(data)
    except ValidationError as e:
        raise LLMError(f"The model returned an invalid document:\n{e}") from e


@dataclass
class LLMResult:
    document: Document
    usage: Usage | None  # tokens and plan limits, when the backend reports them


def structure_notes(raw: str, config: Config | None = None) -> LLMResult:
    """Structure raw notes with the configured backend."""
    config = config or load_config()
    if not raw.strip():
        return LLMResult(Document(title="", subject="", date="", blocks=[]), None)
    if config.backend != "claude_cli":
        raise LLMError(f"Backend {config.backend!r} is not available (only 'claude_cli' for now)")
    from .claude_cli import run
    data, usage = run(raw, config)
    if usage:
        # Keep the last known limits if this reply didn't include them.
        previous = load_usage()
        if previous and usage.five_hour is None:
            usage.five_hour, usage.seven_day = previous.five_hour, previous.seven_day
        save_usage(usage)
    return LLMResult(validate(data), usage)


def format_notes(raw: str, config: Config | None = None) -> Document:
    return structure_notes(raw, config).document
