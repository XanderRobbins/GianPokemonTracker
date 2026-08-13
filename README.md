# GianPokemon — Pokémon TCG Stock Checker

Polls product pages across retailers, pings a Discord channel the moment
something goes from out-of-stock to in-stock, and publishes a live dashboard.
Runs free on GitHub Actions + GitHub Pages.

## Status

- ✅ Best Buy — via the public `api.bestbuy.com` product API. Most reliable
  of the four; no bot protection encountered. The nearest-physical-store
  distance lookup (`_find_nearest_store` in `checkers/bestbuy.py`) is built
  against Best Buy's documented Stores API shape but wasn't verified live
  (no API key was available during dev) — it fails closed (logs a warning,
  omits distance from the dashboard) rather than breaking the stock check
  if the response shape doesn't match, but double check it once you have a
  real key and a real SKU.
- ⚠️ Pokémon Center — HTML parsing implemented, but the site is behind
  Incapsula and returned a bot-challenge page (not real markup) in testing.
  Fails gracefully (logged + skipped) rather than reporting wrong stock
  state, but expect it to rarely succeed from a datacenter IP.
- ⚠️ Target — implemented against the RedSky fulfillment API, but that API
  returned a CAPTCHA challenge in testing, even with realistic
  Referer/Origin headers. Same graceful-failure behavior as above.
- ⚠️ Walmart — implemented via the `__NEXT_DATA__` JSON embedded in product
  pages (avoids their more aggressively-protected search/API endpoints).
  Walmart's search page returned a PerimeterX "Robot or human?" challenge
  in testing; individual product pages were not confirmed to work with a
  real SKU. Same graceful-failure behavior as above.

## How it works

1. `config/products.yaml` lists the products to track (and your `home_zip`,
   optional, for distance scoring).
2. `main.py` runs each product through the matching module in `checkers/`,
   compares the result to `state.json`, and calls `notify.py` when a product
   flips from out-of-stock to in-stock.
3. Every time a product's stock status *flips*, `history.py` logs the event
   to `history.json`. `scoring.py` turns that history into a "rarity" label
   (`Common` → `Ultra Rare`) based on how long the item typically stays in
   stock before selling out again — more of a scarcity/hype estimate than
   the card game's own rarity tiers.
4. `build_dashboard.py` renders `state.json` into `docs/index.html` — a
   static page with a card per product: stock status, price, rarity badge,
   and (Best Buy only, see below) distance to the nearest carrying store.
5. `state.json`, `history.json`, and `docs/index.html` are committed back to
   the repo after every run so everything survives between scheduled runs.
6. `.github/workflows/check.yml` runs the whole pipeline on a cron schedule.
   GitHub Pages serves `docs/index.html` at a stable URL — see
   [Dashboard](#dashboard) below for the one-time setup.

## Adding a product to track

Edit `config/products.yaml`:

```yaml
products:
  - store: bestbuy
    label: "Pokemon TCG Scarlet & Violet Booster Box"
    url: "https://www.bestbuy.com/site/.../REPLACE.p?skuId=1234567"
    sku: "1234567"
```

- `store` must match a key in `checkers/__init__.py` (`CHECKERS`). Products
  for stores without a checker yet are skipped with a warning, not an error.
- `url` doubles as the state key — don't change it once tracking has started,
  or it'll be treated as a new product.
- `sku` is required for the `bestbuy` checker (find it in the product URL or
  Best Buy's page details).

Also set `home_zip` at the top level of `config/products.yaml` (a real US zip
code, not the placeholder) if you want distance-to-nearest-store scores on
the dashboard. Leave the placeholder in place to skip distance scoring
entirely — nothing else depends on it.

## Dashboard

`docs/index.html` is regenerated every run and committed back, so if GitHub
Pages is pointed at it, you get a live URL that always reflects the latest
check — no server to keep running yourself.

**One-time setup:** in the repo, go to Settings → Pages → under "Build and
deployment," set Source to "Deploy from a branch," Branch to `main` /
`/docs`, then Save. After the next workflow run commits a `docs/index.html`,
the page will be live at `https://<your-username>.github.io/<repo-name>/`.

Each card shows: stock status, price (if the store's API/page exposes one),
a rarity badge, and — for Best Buy only, since it's the only store with a
reliable public per-store inventory API — distance to the nearest physical
store currently carrying the item, when `home_zip` is set.

## Setup

### 1. Best Buy API key

Sign up for a free key at https://developer.bestbuy.com/. No approval wait —
keys are issued instantly.

### 2. Discord webhook

In Discord: channel settings → Integrations → Webhooks → New Webhook → copy
the URL.

### 3. GitHub Actions secrets

In the repo: Settings → Secrets and variables → Actions → New repository
secret. Add:

- `BESTBUY_API_KEY`
- `DISCORD_WEBHOOK_URL`

The workflow also needs `contents: write` permission to commit `state.json`,
`history.json`, and `docs/index.html` back (already set in `check.yml`); no
extra token setup is needed beyond the default `GITHUB_TOKEN`.

### 4. Local testing

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys, then export them into your shell
python main.py
```

(There's no built-in `.env` loader — either `export`/`set` the two variables
yourself or add `python-dotenv` if you want that convenience.)

## Adding a new store checker

1. Create `checkers/<store>.py` with a
   `check(product: dict, home_zip: str | None = None) -> CheckResult`
   function (see `checkers/base.py` for the `CheckResult` shape and shared
   HTTP headers/timeout). `home_zip` only matters if you're adding
   distance-to-store scoring for that store; otherwise just accept and
   ignore it.
2. Register it in `checkers/__init__.py`'s `CHECKERS` dict.
3. Add products for that store to `config/products.yaml`.

Prefer `requests` + `beautifulsoup4` for HTML parsing. Only reach for a
headless browser (e.g. Playwright) if a site truly requires JS rendering to
reveal availability — that adds real cost to every scheduled run, so treat it
as a last resort.

## Notes on reliability

- Best Buy's API is the most stable of the four and was built first to prove
  the pipeline end-to-end.
- Pokémon Center, Target, and Walmart are all confirmed (not just suspected)
  to run bot protection that blocks plain HTTP requests some or most of the
  time: Pokémon Center returns an Incapsula challenge page, Target's API
  returns a CAPTCHA response, and Walmart's search returned a PerimeterX
  challenge. All three checkers degrade to a logged error + skip rather than
  reporting incorrect stock state when this happens — but treat alerts from
  these three as "best effort," and lean on Best Buy as the reliable one.
  Realistically these will likely need to run less frequently, from a
  non-datacenter IP, or with a headless browser to be trustworthy — Playwright
  is the natural next step if that's worth the added GitHub Actions compute
  cost to you.
- Requests use browser-like headers and a small random jitter (1-3s) between
  checks to avoid hammering sites in a burst.
