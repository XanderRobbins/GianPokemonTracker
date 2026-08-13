import logging
import os
import requests

from .base import CheckResult, DEFAULT_HEADERS, REQUEST_TIMEOUT

API_URL = "https://api.bestbuy.com/v1/products(sku={sku})"
STORES_URL = "https://api.bestbuy.com/v1/products/{sku}/stores.json"

logger = logging.getLogger(__name__)


def check(product: dict, home_zip: str | None = None) -> CheckResult:
    api_key = os.environ.get("BESTBUY_API_KEY")
    if not api_key:
        return CheckResult(in_stock=False, error="BESTBUY_API_KEY is not set")

    sku = product.get("sku")
    if not sku:
        return CheckResult(in_stock=False, error="product config missing 'sku'")

    url = API_URL.format(sku=sku)
    params = {
        "apiKey": api_key,
        "format": "json",
        "show": "sku,name,salePrice,onlineAvailability,inStoreAvailability,url",
    }

    try:
        resp = requests.get(url, params=params, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return CheckResult(in_stock=False, error=f"request failed: {exc}")

    try:
        data = resp.json()
    except ValueError as exc:
        return CheckResult(in_stock=False, error=f"invalid JSON response: {exc}")

    products = data.get("products") or []
    if not products:
        return CheckResult(in_stock=False, error=f"no product found for sku {sku}")

    item = products[0]
    in_stock = bool(item.get("onlineAvailability"))
    price = item.get("salePrice")
    price_str = f"${price:.2f}" if isinstance(price, (int, float)) else None

    nearest_store = None
    if home_zip:
        nearest_store = _find_nearest_store(sku, home_zip, api_key)

    return CheckResult(in_stock=in_stock, price=price_str, nearest_store=nearest_store)


def _find_nearest_store(sku: str, home_zip: str, api_key: str) -> dict | None:
    """Best-effort: per Best Buy's Stores API, sorted by distance from
    home_zip. Not verified against a live API key during development (none
    was available) - if Best Buy's response shape has drifted from the
    documented one, this just logs and returns None rather than breaking
    the main stock check.
    """
    params = {
        "apiKey": api_key,
        "format": "json",
        "show": "name,city,state,distance",
        "sort": "distance.asc",
        "pageSize": 1,
    }
    # area() is a positional filter in Best Buy's query syntax, not a
    # normal key=value pair - append it directly to the querystring rather
    # than passing it through requests' params dict (which would encode it
    # as area(...)= and break the filter).
    url = f"{STORES_URL.format(sku=sku)}?area({home_zip},100)"

    try:
        resp = requests.get(
            url,
            params=params,
            headers=DEFAULT_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        stores = data.get("stores") or []
        if not stores:
            return None
        store = stores[0]
        return {"name": store.get("name", "store"), "distance_miles": store.get("distance")}
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.warning("Best Buy nearest-store lookup failed for sku %s: %s", sku, exc)
        return None
