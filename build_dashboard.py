import json
from html import escape
from pathlib import Path

BASE_DIR = Path(__file__).parent
STATE_PATH = BASE_DIR / "state.json"
OUTPUT_PATH = BASE_DIR / "docs" / "index.html"

RARITY_COLORS = {
    "Ultra Rare": "#9b59b6",
    "Rare": "#3498db",
    "Uncommon": "#2ecc71",
    "Common": "#95a5a6",
    "Unknown": "#bdc3c7",
}

STORE_DISPLAY_NAMES = {
    "bestbuy": "Best Buy",
    "pokemoncenter": "Pokémon Center",
    "target": "Target",
    "walmart": "Walmart",
}


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def render_card(entry: dict) -> str:
    label = escape(entry.get("label", "Unknown product"))
    store_key = entry.get("store") or ""
    store = escape(STORE_DISPLAY_NAMES.get(store_key, store_key.title()))
    url = escape(entry.get("url", "#"))
    in_stock = entry.get("in_stock", False)
    price = entry.get("price")
    last_checked = escape(entry.get("last_checked", ""))

    rarity = entry.get("rarity") or {"label": "Unknown", "avg_in_stock_minutes": None, "sample_size": 0}
    rarity_label = escape(rarity.get("label", "Unknown"))
    rarity_color = RARITY_COLORS.get(rarity.get("label"), RARITY_COLORS["Unknown"])
    rarity_detail = (
        f"avg {rarity['avg_in_stock_minutes']:.0f} min in stock ({rarity['sample_size']} restocks)"
        if rarity.get("avg_in_stock_minutes") is not None
        else "not enough restock history yet"
    )

    nearest_store = entry.get("nearest_store")
    if nearest_store and nearest_store.get("distance_miles") is not None:
        distance_html = f"<div class=\"distance\">📍 {nearest_store['distance_miles']:.1f} mi — {escape(nearest_store.get('name', 'store'))}</div>"
    else:
        distance_html = ""

    status_class = "in-stock" if in_stock else "out-of-stock"
    status_text = "IN STOCK" if in_stock else "Out of stock"
    price_html = f"<div class=\"price\">{escape(price)}</div>" if price else ""

    return f"""
    <a class="card {status_class}" href="{url}" target="_blank" rel="noopener">
      <div class="card-top">
        <span class="status-badge {status_class}">{status_text}</span>
        <span class="rarity-badge" style="background:{rarity_color}">{rarity_label}</span>
      </div>
      <div class="label">{label}</div>
      <div class="store">{store}</div>
      {price_html}
      {distance_html}
      <div class="rarity-detail">{rarity_detail}</div>
      <div class="last-checked">checked {last_checked}</div>
    </a>
    """


def render(state: dict) -> str:
    entries = list(state.values())
    entries.sort(key=lambda e: (not e.get("in_stock", False), e.get("label", "")))

    cards_html = "\n".join(render_card(e) for e in entries) if entries else (
        '<p class="empty">No products tracked yet. Add some to config/products.yaml.</p>'
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pokemon TCG Stock Tracker</title>
<style>
  :root {{
    --bg: #f5f6fa; --card-bg: #ffffff; --text: #2c2c34; --muted: #767688;
    --border: #e2e2ea; --in-stock: #2ecc71; --out-of-stock: #95a5a6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #16161d; --card-bg: #202029; --text: #e8e8f0; --muted: #9a9aab;
      --border: #33333f;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 2rem 1rem 4rem; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  h1 {{ text-align: center; margin-bottom: 0.25rem; }}
  .subtitle {{ text-align: center; color: var(--muted); margin-bottom: 2rem; font-size: 0.9rem; }}
  .grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem; max-width: 1100px; margin: 0 auto;
  }}
  .card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
    padding: 1rem; text-decoration: none; color: var(--text); display: block;
    transition: transform 0.1s ease;
  }}
  .card:hover {{ transform: translateY(-2px); }}
  .card.in-stock {{ border-color: var(--in-stock); }}
  .card-top {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem; }}
  .status-badge {{
    font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em; padding: 0.2rem 0.5rem;
    border-radius: 999px; color: white;
  }}
  .status-badge.in-stock {{ background: var(--in-stock); }}
  .status-badge.out-of-stock {{ background: var(--out-of-stock); }}
  .rarity-badge {{
    font-size: 0.7rem; font-weight: 700; padding: 0.2rem 0.5rem; border-radius: 999px; color: white;
  }}
  .label {{ font-weight: 600; margin-bottom: 0.2rem; }}
  .store {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 0.4rem; }}
  .price {{ font-weight: 600; margin-bottom: 0.2rem; }}
  .distance {{ font-size: 0.85rem; color: var(--muted); margin-bottom: 0.2rem; }}
  .rarity-detail {{ font-size: 0.75rem; color: var(--muted); margin-top: 0.4rem; }}
  .last-checked {{ font-size: 0.7rem; color: var(--muted); margin-top: 0.4rem; }}
  .empty {{ text-align: center; color: var(--muted); }}
</style>
</head>
<body>
  <h1>Pokemon TCG Stock Tracker</h1>
  <p class="subtitle">Auto-updated by GitHub Actions. Rarity is an estimate from restock history, not the card game's own rarity tiers.</p>
  <div class="grid">
    {cards_html}
  </div>
</body>
</html>
"""


def main() -> None:
    state = load_state()
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(render(state), encoding="utf-8")


if __name__ == "__main__":
    main()
