from . import bestbuy

# Maps the `store` value in config/products.yaml to a checker module's
# `check(product) -> CheckResult` function. Add new stores here as their
# checker modules are implemented (pokemoncenter, target, walmart, ...).
CHECKERS = {
    "bestbuy": bestbuy.check,
}
