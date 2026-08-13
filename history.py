import json
from pathlib import Path

HISTORY_PATH = Path(__file__).parent / "history.json"

# How many transition events to keep per product. Each event is a
# stock-status flip, not a poll, so this covers a long span of real time.
MAX_EVENTS_PER_PRODUCT = 40


def load_history() -> dict:
    if not HISTORY_PATH.exists():
        return {}
    with open(HISTORY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_history(history: dict) -> None:
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, sort_keys=True)
        f.write("\n")


def record_transition(history: dict, url: str, in_stock: bool, timestamp: str) -> None:
    """Append a stock-status flip. Call only when status actually changed
    from the previous poll - a log of every poll would swamp the scarcity
    signal with noise."""
    events = history.setdefault(url, [])
    events.append({"ts": timestamp, "in_stock": in_stock})
    del events[:-MAX_EVENTS_PER_PRODUCT]
