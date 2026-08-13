from dataclasses import dataclass
from typing import Optional

# Shared browser-like headers so plain `requests` calls don't get trivially
# fingerprinted as a bot by store WAFs.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15  # seconds


@dataclass
class CheckResult:
    in_stock: bool
    price: Optional[str] = None
    error: Optional[str] = None
    # {"name": str, "distance_miles": float} for the closest physical store
    # carrying the item, when the checker supports store-level lookup and a
    # home_zip was configured. None otherwise.
    nearest_store: Optional[dict] = None
