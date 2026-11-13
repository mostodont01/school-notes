import json
import subprocess
from pathlib import Path

import pytest

from notes_app.config import Config, load_config
from notes_app.llm import LLMError, document_schema, format_notes
from notes_app.llm import claude_cli

FIXTURES = Path(__file__).parent / "fixtures"
VALID = json.loads((FIXTURES / "all_elements.json").read_text())


def test_schema_is_clean():
    text = json.dumps(document_schema())
    assert '"discriminator"' not in text and '"title": "Document"' not in text
    assert "blocks" in document_schema()["properties"]


def test_command_is_lean():
    cmd = claude_cli.command(Config(model="opus", effort="low"))
    for flag in ["-p", "--json-schema", "--system-prompt", "--strict-mcp-config", "--no-session-persistence"]:
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--setting-sources") + 1] == ""
    assert cmd[cmd.index("--model") + 1] == "opus"


def fake_claude(monkeypatch, stdout: str, returncode: int = 0):
    calls = {}

    def run(cmd, **kwargs):
        calls["input"] = kwargs["input"]
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="boom")

    monkeypatch.setattr(claude_cli.shutil, "which", lambda _: "/usr/bin/claude")
    monkeypatch.setattr(claude_cli.subprocess, "run", run)
    return calls


def result_line(**fields):
    return json.dumps({"type": "result", **fields})


def test_valid_structured_output(monkeypatch):
    calls = fake_claude(monkeypatch, result_line(subtype="success", is_error=False, structured_output=VALID))
    doc = format_notes("poznamky", Config())
    assert calls["input"] == "poznamky"
    assert len(doc.blocks) == len(VALID["blocks"])


def test_invalid_document_is_rejected(monkeypatch):
    bad = {"title": "", "subject": "", "date": "", "blocks": [{"type": "nope"}]}
    fake_claude(monkeypatch, result_line(subtype="success", structured_output=bad))
    with pytest.raises(LLMError, match="invalid document"):
        format_notes("x", Config())


def test_cli_error_is_reported(monkeypatch):
    fake_claude(monkeypatch, "not json", returncode=1)
    with pytest.raises(LLMError, match="exit 1"):
        format_notes("x", Config())


def test_empty_notes_skip_the_llm(monkeypatch):
    monkeypatch.setattr(claude_cli.subprocess, "run", lambda *a, **k: pytest.fail("called"))
    assert format_notes("  \n", Config()).blocks == []


def test_config_file(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[library]\ndir = "/tmp/x"\n[llm]\nmodel = "sonnet"\n')
    config = load_config(path)
    assert config.model == "sonnet" and str(config.notes_dir) == "/tmp/x"
    assert load_config(tmp_path / "missing.toml").backend == "claude_cli"


def test_other_backends_are_not_available():
    with pytest.raises(LLMError, match="not available"):
        format_notes("x", Config(backend="ollama"))


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_every_required_field_is_still_a_property():
    """Regression: the cleanup once removed fields named 'title'."""
    for node in _walk(document_schema()):
        for name in node.get("required", []):
            assert name in node["properties"], name
