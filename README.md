# GianPokemon — Pokémon TCG Stock Checker

Polls product pages across retailers and pings a Discord channel the moment
something goes from out-of-stock to in-stock. Runs free on GitHub Actions.

## Status

- ✅ Best Buy — via the public `api.bestbuy.com` product API
- ⬜ Pokémon Center — not yet implemented
- ⬜ Target — not yet implemented
- ⬜ Walmart — not yet implemented

## How it works

1. `config/products.yaml` lists the products to track.
2. `main.py` runs each product through the matching module in `checkers/`,
   compares the result to `state.json`, and calls `notify.py` when a product
   flips from out-of-stock to in-stock.
3. `state.json` is committed back to the repo after every run so state
   survives between scheduled runs.
4. `.github/workflows/check.yml` runs `main.py` on a cron schedule.

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

The workflow also needs `contents: write` permission to commit `state.json`
back (already set in `check.yml`); no extra token setup is needed beyond the
default `GITHUB_TOKEN`.

### 4. Local testing

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys, then export them into your shell
python main.py
```

(There's no built-in `.env` loader — either `export`/`set` the two variables
yourself or add `python-dotenv` if you want that convenience.)

## Adding a new store checker

1. Create `checkers/<store>.py` with a `check(product: dict) -> CheckResult`
   function (see `checkers/base.py` for the `CheckResult` shape and shared
   HTTP headers/timeout).
2. Register it in `checkers/__init__.py`'s `CHECKERS` dict.
3. Add products for that store to `config/products.yaml`.

Prefer `requests` + `beautifulsoup4` for HTML parsing. Only reach for a
headless browser (e.g. Playwright) if a site truly requires JS rendering to
reveal availability — that adds real cost to every scheduled run, so treat it
as a last resort.

## Notes on reliability

- Best Buy's API is the most stable of the four and was built first to prove
  the pipeline end-to-end.
- Target and Walmart use bot-protected APIs; GitHub Actions' shared runner
  IPs may get flagged. Expect these to be less reliable than Best Buy even
  once implemented.
- Requests use browser-like headers and a small random jitter (1-3s) between
  checks to avoid hammering sites in a burst.
