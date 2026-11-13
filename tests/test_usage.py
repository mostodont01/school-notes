import json
import time

from notes_app.llm.claude_cli import parse_stream
from notes_app.llm.usage import (Usage, Window, current_usage, describe, fresher,
                                 load_statusbar_limits, save_usage)

NOW = 1_794_560_000.0
STREAM = "\n".join(json.dumps(e) for e in [
    {"type": "system", "subtype": "init"},
    {"type": "rate_limit_event", "rate_limit_info": {"unifiedWindows": {
        "five_hour": {"utilization": 0.18, "resetsAt": NOW + 3600, "status": "allowed"},
        "seven_day": {"utilization": 0.31, "resetsAt": NOW + 86400, "status": "allowed"}}}},
    {"type": "result", "subtype": "success", "is_error": False,
     "structured_output": {"word": "kočka"},
     "usage": {"input_tokens": 2, "cache_creation_input_tokens": 1074,
               "cache_read_input_tokens": 100, "output_tokens": 53}},
])


def test_parse_stream_tokens_and_limits():
    data, usage = parse_stream(STREAM)
    assert data == {"word": "kočka"}
    assert (usage.input_tokens, usage.output_tokens) == (1176, 53)
    assert usage.five_hour.utilization == 0.18 and usage.seven_day.utilization == 0.31


def test_window_resets_to_empty():
    w = Window(0.9, resets_at=NOW)
    assert w.used(NOW - 1) == 0.9 and w.used(NOW + 1) == 0.0


def test_fresher_follows_the_doombar_rule():
    old = Window(0.9, NOW)
    new = Window(0.1, NOW + 5 * 3600)                   # next window
    assert fresher(old, new) is new
    assert fresher(Window(0.2, NOW), Window(0.3, NOW + 10)) .utilization == 0.3  # same window: higher
    assert fresher(None, old) is old


def test_statusbar_snapshot(tmp_path):
    bar = tmp_path / "bar.json"
    bar.write_text(json.dumps({"five_hour": {"used_percentage": 19, "resets_at": NOW + 3600},
                               "seven_day": {"used_percentage": 31, "resets_at": NOW + 86400}}))
    five, week = load_statusbar_limits(bar)
    assert five.utilization == 0.19 and week.utilization == 0.31
    assert load_statusbar_limits(tmp_path / "missing.json") == (None, None)


def test_current_usage_merges_cache_and_statusbar(tmp_path):
    cache, bar = tmp_path / "usage.json", tmp_path / "bar.json"
    save_usage(Usage(500, 80, Window(0.10, NOW + 3600), Window(0.30, NOW + 86400)), cache)
    bar.write_text(json.dumps({"five_hour": {"used_percentage": 25, "resets_at": NOW + 3600}}))
    usage = current_usage(cache, bar)
    assert usage.input_tokens == 500
    assert usage.five_hour.utilization == 0.25      # status bar is fresher
    assert usage.seven_day.utilization == 0.30      # only the cache knows it
    assert current_usage(tmp_path / "none.json", tmp_path / "none2.json") is None


def test_describe_draws_bars():
    text = describe(Usage(1000, 200, Window(0.5, NOW + 60), None), now=NOW)
    assert "1,000 in" in text and "██████████░░░░░░░░░░" in text
