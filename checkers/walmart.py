import json
import re

import requests
from bs4 import BeautifulSoup

from .base import CheckResult, DEFAULT_HEADERS, REQUEST_TIMEOUT

# Walmart embeds product/availability state in a __NEXT_DATA__ script tag on
# the product page itself. This avoids calling their separate APIs, which
# throw a PerimeterX "Robot or human?" challenge page for most datacenter-IP
# requests (confirmed during dev) - expect this checker to be unreliable
# from shared runners like GitHub Actions. See README.
NEXT_DATA_ID = "__NEXT_DATA__"


def _find_product_node(node):
    """__NEXT_DATA__'s shape shifts between Walmart page versions, so walk
    the tree looking for the first dict with an availabilityStatus key
    instead of hardcoding a path."""
    if isinstance(node, dict):
        if "availabilityStatus" in node and "priceInfo" in node:
            return node
        for value in node.values():
            found = _find_product_node(value)
            if found:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_product_node(item)
            if found:
                return found
    return None


def check(product: dict, home_zip: str | None = None) -> CheckResult:
    url = product.get("url")
    if not url:
        return CheckResult(in_stock=False, error="product config missing 'url'")

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return CheckResult(in_stock=False, error=f"request failed: {exc}")

    if not resp.ok:
        return CheckResult(in_stock=False, error=f"unexpected status {resp.status_code}")

    if re.search(r"robot or human", resp.text, re.I):
        return CheckResult(in_stock=False, error="blocked by Walmart bot protection")

    soup = BeautifulSoup(resp.text, "html.parser")
    script_tag = soup.find("script", id=NEXT_DATA_ID)
    if not script_tag or not script_tag.string:
        return CheckResult(in_stock=False, error="__NEXT_DATA__ not found (page layout may have changed)")

    try:
        data = json.loads(script_tag.string)
    except ValueError as exc:
        return CheckResult(in_stock=False, error=f"invalid __NEXT_DATA__ JSON: {exc}")

    item = _find_product_node(data)
    if item is None:
        return CheckResult(in_stock=False, error="could not locate product data in __NEXT_DATA__")

    in_stock = item.get("availabilityStatus") == "IN_STOCK"
    price = item.get("priceInfo", {}).get("currentPrice", {}).get("price")
    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else None

    return CheckResult(in_stock=in_stock, price=price_str)
