from . import bestbuy
from . import pokemoncenter
from . import target
from . import walmart

# Maps the `store` value in config/products.yaml to a checker module's
# `check(product) -> CheckResult` function.
CHECKERS = {
    "bestbuy": bestbuy.check,
    "pokemoncenter": pokemoncenter.check,
    "target": target.check,
    "walmart": walmart.check,
}
