import json
import logging
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from checkers import CHECKERS
from notify import send_discord_alert

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config" / "products.yaml"
STATE_PATH = BASE_DIR / "state.json"

JITTER_MIN_SECONDS = 1
JITTER_MAX_SECONDS = 3


def load_config() -> list[dict]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("products", [])


def load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)
        f.write("\n")


def main() -> None:
    products = load_config()
    state = load_state()

    for i, product in enumerate(products):
        store = product.get("store")
        label = product.get("label", product.get("url", "unknown product"))
        url = product.get("url")

        checker = CHECKERS.get(store)
        if checker is None:
            logger.warning("No checker implemented for store '%s' (%s); skipping", store, label)
            continue

        if not url:
            logger.warning("Product '%s' missing 'url'; skipping", label)
            continue

        if i > 0:
            time.sleep(random.uniform(JITTER_MIN_SECONDS, JITTER_MAX_SECONDS))

        result = checker(product)

        if result.error:
            logger.error("Check failed for %s (%s): %s", label, store, result.error)
            continue

        previous = state.get(url, {})
        was_in_stock = previous.get("in_stock", False)

        logger.info("%s [%s]: in_stock=%s (was %s)", label, store, result.in_stock, was_in_stock)

        if result.in_stock and not was_in_stock:
            logger.info("Transition detected -> sending Discord alert for %s", label)
            send_discord_alert(label=label, store=store, url=url, price=result.price)

        state[url] = {
            "in_stock": result.in_stock,
            "price": result.price,
            "last_checked": datetime.now(timezone.utc).isoformat(),
        }

    save_state(state)


if __name__ == "__main__":
    main()
