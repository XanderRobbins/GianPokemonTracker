import os
import logging
from datetime import datetime, timezone

import requests

from checkers.base import REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


def send_discord_alert(label: str, store: str, url: str, price: str | None = None) -> None:
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL is not set; skipping notification for %s", label)
        return

    fields = [{"name": "Store", "value": store.title(), "inline": True}]
    if price:
        fields.append({"name": "Price", "value": price, "inline": True})

    embed = {
        "title": f"🚨 In Stock: {label}",
        "url": url,
        "color": 0x2ECC71,
        "fields": fields,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    try:
        resp = requests.post(webhook_url, json={"embeds": [embed]}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to send Discord notification for %s", label)
