from datetime import datetime
from typing import Optional

# Thresholds are on average minutes spent in-stock before selling out again.
# Shorter windows mean the item is harder to actually catch in stock, which
# is what "rarity" is standing in for here - it's a scarcity/hype estimate,
# not the card game's own rarity tiers.
RARITY_THRESHOLDS_MINUTES = (
    (10, "Ultra Rare"),
    (60, "Rare"),
    (24 * 60, "Uncommon"),
)
DEFAULT_RARITY = "Common"
UNKNOWN_RARITY = "Unknown"


def compute_rarity(events: list) -> dict:
    """events: chronological list of {"ts": iso8601, "in_stock": bool},
    as stored by history.record_transition (strictly alternating, since we
    only log actual flips). Pairs of (in_stock=True, in_stock=False) that
    are adjacent in the list form one completed "it was in stock for X"
    window; average those to estimate rarity."""
    durations_minutes = []

    for i in range(len(events) - 1):
        if events[i]["in_stock"] and not events[i + 1]["in_stock"]:
            start = datetime.fromisoformat(events[i]["ts"])
            end = datetime.fromisoformat(events[i + 1]["ts"])
            durations_minutes.append((end - start).total_seconds() / 60)

    if not durations_minutes:
        return {"label": UNKNOWN_RARITY, "avg_in_stock_minutes": None, "sample_size": 0}

    avg = sum(durations_minutes) / len(durations_minutes)
    label = DEFAULT_RARITY
    for threshold, candidate_label in RARITY_THRESHOLDS_MINUTES:
        if avg < threshold:
            label = candidate_label
            break

    return {
        "label": label,
        "avg_in_stock_minutes": round(avg, 1),
        "sample_size": len(durations_minutes),
    }


def format_distance(nearest_store: Optional[dict]) -> str:
    if not nearest_store:
        return "—"
    miles = nearest_store.get("distance_miles")
    name = nearest_store.get("name", "store")
    if miles is None:
        return name
    return f"{miles:.1f} mi — {name}"
