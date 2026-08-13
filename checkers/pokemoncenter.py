import re

import requests
from bs4 import BeautifulSoup

from .base import CheckResult, DEFAULT_HEADERS, REQUEST_TIMEOUT

OUT_OF_STOCK_PHRASES = ("sold out", "notify me", "out of stock", "coming soon")
PRICE_RE = re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?")


def check(product: dict, home_zip: str | None = None) -> CheckResult:
    url = product.get("url")
    if not url:
        return CheckResult(in_stock=False, error="product config missing 'url'")

    try:
        resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return CheckResult(in_stock=False, error=f"request failed: {exc}")

    soup = BeautifulSoup(resp.text, "html.parser")

    add_to_cart = soup.find(
        lambda tag: tag.name in ("button", "a")
        and tag.get_text(strip=True).lower() in ("add to cart", "buy now")
    )
    blocked = soup.find(
        lambda tag: tag.name in ("button", "a", "span", "div")
        and tag.get_text(strip=True).lower() in OUT_OF_STOCK_PHRASES
    )

    if add_to_cart and not blocked:
        in_stock = True
    elif blocked:
        in_stock = False
    else:
        # Page markup didn't match either pattern (site redesign, layout
        # change, etc.) - report as unavailable rather than guess.
        return CheckResult(
            in_stock=False,
            error="could not determine stock state from page markup (site layout may have changed)",
        )

    price = None
    price_tag = soup.find(attrs={"class": re.compile("price", re.I)})
    if price_tag:
        match = PRICE_RE.search(price_tag.get_text())
        if match:
            price = match.group(0)

    return CheckResult(in_stock=in_stock, price=price)
