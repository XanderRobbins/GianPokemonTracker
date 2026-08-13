import os
import requests

from .base import CheckResult, DEFAULT_HEADERS, REQUEST_TIMEOUT

API_URL = "https://api.bestbuy.com/v1/products(sku={sku})"


def check(product: dict) -> CheckResult:
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

    return CheckResult(in_stock=in_stock, price=price_str)
