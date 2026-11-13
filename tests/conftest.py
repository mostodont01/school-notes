import os

# Qt tests run headless (also in CI).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


import pytest


@pytest.fixture(autouse=True)
def _isolated_caches(tmp_path, monkeypatch):
    """Tests never touch the real usage cache or status bar snapshot."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("DOOMBAR_RATELIMITS", str(tmp_path / "no-statusbar.json"))
