import requests

from .base import CheckResult, DEFAULT_HEADERS, REQUEST_TIMEOUT

# Target's frontend calls this API with a key that's public (embedded in
# every page's JS bundle, not a secret), but the endpoint is behind bot
# protection that returns a CAPTCHA challenge for most datacenter-IP
# requests (confirmed against GitHub Actions-like requests during dev) -
# expect this checker to fail often from shared runners. See README.
FULFILLMENT_URL = "https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1"
DEFAULT_API_KEY = "9f36aeafbe60771e321a7cc95a78140772ab3e96"


def check(product: dict) -> CheckResult:
    tcin = product.get("sku") or product.get("tcin")
    if not tcin:
        return CheckResult(in_stock=False, error="product config missing 'sku' (Target TCIN)")

    store_id = product.get("store_id", "3991")  # arbitrary default store for pricing context

    headers = dict(DEFAULT_HEADERS)
    headers["Accept"] = "application/json"
    headers["Origin"] = "https://www.target.com"
    headers["Referer"] = product.get("url", "https://www.target.com/")

    params = {
        "key": DEFAULT_API_KEY,
        "tcin": tcin,
        "store_id": store_id,
        "pricing_store_id": store_id,
    }

    try:
        resp = requests.get(FULFILLMENT_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        return CheckResult(in_stock=False, error=f"request failed: {exc}")

    if resp.status_code == 403:
        return CheckResult(in_stock=False, error="blocked by Target bot protection (403/CAPTCHA)")
    if not resp.ok:
        return CheckResult(in_stock=False, error=f"unexpected status {resp.status_code}")

    try:
        data = resp.json()
        item = data["data"]["product"]
        shipping = item["fulfillment"]["shipping_options"]
        in_stock = shipping.get("availability_status") == "IN_STOCK"
        price = item.get("price", {}).get("current_retail")
        price_str = f"${price:.2f}" if isinstance(price, (int, float)) else None
    except (ValueError, KeyError, TypeError) as exc:
        return CheckResult(in_stock=False, error=f"unexpected response shape: {exc}")

    return CheckResult(in_stock=in_stock, price=price_str)
