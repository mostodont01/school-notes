"""User settings from ~/.config/school-notes/config.toml (outside the repo).

Example:

    [library]
    dir = "~/School/Notes"

    [llm]
    backend = "claude_cli"   # or "ollama"
    model = "opus"           # optional; claude_cli: alias or model id
    effort = "medium"        # optional; claude_cli only
    timeout = 300

    [ollama]
    url = "http://desktop:11434"   # e.g. the desktop PC over Tailscale
    model = "qwen3:8b"
"""

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "school-notes" / "config.toml"


@dataclass
class Config:
    notes_dir: Path = Path("~/School/Notes").expanduser()
    backend: str = "claude_cli"
    model: str = ""
    effort: str = "medium"
    timeout: float = 300
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen3:8b"


def load_config(path: Path = CONFIG_PATH) -> Config:
    config = Config()
    if path.exists():
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        llm, ollama = data.get("llm", {}), data.get("ollama", {})
        if "dir" in data.get("library", {}):
            config.notes_dir = Path(data["library"]["dir"]).expanduser()
        config.backend = llm.get("backend", config.backend)
        config.model = llm.get("model", config.model)
        config.effort = llm.get("effort", config.effort)
        config.timeout = float(llm.get("timeout", config.timeout))
        config.ollama_url = ollama.get("url", config.ollama_url)
        config.ollama_model = ollama.get("model", config.ollama_model)
    return config
