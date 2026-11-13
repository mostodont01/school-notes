"""Token counts and plan limits reported by `claude -p`.

Each call reports its own token usage, and (as a rate_limit_event) how full
the plan's 5-hour and weekly windows are, as a fraction, with reset times.
Anthropic doesn't publish the limits in tokens, so "how full" is all there is.

The last snapshot is cached in ~/.cache/school-notes/usage.json. Fresher limits
usually come for free from the Claude Code status bar (claude-doom-statusbar),
which keeps a shared snapshot that every running Claude Code session updates.
"""

import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

def usage_path() -> Path:
    """Our own cache of the last call (looked up at call time, so tests can redirect it)."""
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "school-notes" / "usage.json"


def statusbar_path() -> Path:
    """The doom status bar's shared snapshot (same lookup as its statusline.js)."""
    return Path(os.environ.get("DOOMBAR_RATELIMITS")
                or Path(tempfile.gettempdir()) / "mugshot_ratelimits_global.json")


@dataclass
class Window:
    utilization: float      # 0.0 – 1.0, how full the window is
    resets_at: float        # unix time
    status: str = "allowed"

    def used(self, now: float | None = None) -> float:
        """Fullness now: a window that has reset since the snapshot is empty."""
        if (now or time.time()) >= self.resets_at:
            return 0.0
        return max(0.0, min(1.0, self.utilization))


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    five_hour: Window | None = None
    seven_day: Window | None = None
    at: float = field(default_factory=time.time)

    @classmethod
    def from_stream(cls, result: dict | None, rate_limit: dict | None) -> "Usage":
        usage = (result or {}).get("usage") or {}
        windows = (rate_limit or {}).get("unifiedWindows") or {}

        def window(name):
            w = windows.get(name)
            if not w or "utilization" not in w:
                return None
            return Window(float(w["utilization"]), float(w.get("resetsAt", 0)), w.get("status", "allowed"))

        return cls(
            input_tokens=sum(int(usage.get(k, 0) or 0) for k in
                             ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            five_hour=window("five_hour"),
            seven_day=window("seven_day"),
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Usage":
        return cls(
            input_tokens=d.get("input_tokens", 0),
            output_tokens=d.get("output_tokens", 0),
            five_hour=Window(**d["five_hour"]) if d.get("five_hour") else None,
            seven_day=Window(**d["seven_day"]) if d.get("seven_day") else None,
            at=d.get("at", 0),
        )


def save_usage(usage: Usage, path: Path | None = None) -> None:
    path = path or usage_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(usage.to_dict()), encoding="utf-8")
    except OSError:
        pass  # only a display cache


def load_usage(path: Path | None = None) -> Usage | None:
    try:
        return Usage.from_dict(json.loads((path or usage_path()).read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError):
        return None


def describe(usage: Usage, now: float | None = None) -> str:
    """One-line summary for the command line."""
    import datetime as dt
    parts = [f"tokens: {usage.input_tokens:,} in, {usage.output_tokens:,} out"]
    for label, w in (("5 h", usage.five_hour), ("week", usage.seven_day)):
        if w:
            filled = round(w.used(now) * 20)
            reset = dt.datetime.fromtimestamp(w.resets_at).strftime("%a %H:%M")
            parts.append(f"{label} [{'█' * filled}{'░' * (20 - filled)}] resets {reset}")
    return "\n".join(parts)


SAME_WINDOW_S = 60  # resets_at values this close belong to the same window


def fresher(a: Window | None, b: Window | None) -> Window | None:
    """The newer of two readings of one window (the doom bar's rule): a later
    reset time means a newer window; within one window usage only rises."""
    if a is None or b is None:
        return a or b
    if abs(a.resets_at - b.resets_at) > SAME_WINDOW_S:
        return a if a.resets_at > b.resets_at else b
    return a if a.utilization >= b.utilization else b


def load_statusbar_limits(path: Path | None = None) -> tuple[Window | None, Window | None]:
    try:
        data = json.loads((path or statusbar_path()).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None

    def window(name):
        w = data.get(name) if isinstance(data, dict) else None
        if not isinstance(w, dict) or not isinstance(w.get("used_percentage"), (int, float)):
            return None
        return Window(w["used_percentage"] / 100, float(w.get("resets_at") or 0))

    return window("five_hour"), window("seven_day")


def current_usage(cache: Path | None = None, statusbar: Path | None = None) -> Usage | None:
    """Last format's tokens, with the freshest known limits from both sources."""
    usage = load_usage(cache)
    five, week = load_statusbar_limits(statusbar)
    if usage is None and five is None and week is None:
        return None
    usage = usage or Usage(at=0)
    usage.five_hour = fresher(usage.five_hour, five)
    usage.seven_day = fresher(usage.seven_day, week)
    return usage
