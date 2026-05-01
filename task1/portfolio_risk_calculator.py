def validate_portfolio(portfolio):
    #check for dictionary
    if not isinstance(portfolio, dict):
        raise ValueError(
            f"Portfolio must be a dictionary, got {type(portfolio).__name__}"
        )

    #check for all keys
    required_keys = ["total_value_inr", "monthly_expenses_inr", "assets"]
    for key in required_keys:
        if key not in portfolio:
            raise ValueError(
                f"Portfolio is missing required field: '{key}'\n"
                f"  Required fields are: {required_keys}\n"
                f"  You provided: {list(portfolio.keys())}"
            )

    #check for all fields correct names
    total    = portfolio["total_value_inr"]
    expenses = portfolio["monthly_expenses_inr"]
    assets   = portfolio["assets"]

    if not isinstance(total, (int, float)):
        raise ValueError(
            f"'total_value_inr' must be a number, got {type(total).__name__}: {total!r}"
        )
    if not isinstance(expenses, (int, float)):
        raise ValueError(
            f"'monthly_expenses_inr' must be a number, got {type(expenses).__name__}: {expenses!r}"
        )
    if not isinstance(assets, list):
        raise ValueError(
            f"'assets' must be a list, got {type(assets).__name__}: {assets!r}"
        )

    #check for ranges
    if total < 0:
        raise ValueError(f"'total_value_inr' cannot be negative, got {total}")
    if expenses < 0:
        raise ValueError(f"'monthly_expenses_inr' cannot be negative, got {expenses}")
    if len(assets) == 0:
        raise ValueError("'assets' list cannot be empty")

    #validate for each asset
    required_asset_keys = ["name", "allocation_pct", "expected_crash_pct"]

    for i, asset in enumerate(assets):

        # Must be a dict
        if not isinstance(asset, dict):
            raise ValueError(
                f"Asset at index {i} must be a dictionary, "
                f"got {type(asset).__name__}: {asset!r}"
            )

        # Must have all required keys
        for key in required_asset_keys:
            if key not in asset:
                raise ValueError(
                    f"Asset at index {i} is missing field: '{key}'\n"
                    f"  Required fields: {required_asset_keys}\n"
                    f"  Asset has: {list(asset.keys())}"
                )

        name       = asset["name"]
        alloc      = asset["allocation_pct"]
        crash_pct  = asset["expected_crash_pct"]

        # Name must be a non-empty string
        if not isinstance(name, str) or not name.strip():
            raise ValueError(
                f"Asset at index {i}: 'name' must be a non-empty string, "
                f"got {name!r}"
            )

        # allocation_pct must be a number
        if not isinstance(alloc, (int, float)):
            raise ValueError(
                f"Asset '{name}': 'allocation_pct' must be a number, "
                f"got {type(alloc).__name__}: {alloc!r}"
            )

        # expected_crash_pct must be a number
        if not isinstance(crash_pct, (int, float)):
            raise ValueError(
                f"Asset '{name}': 'expected_crash_pct' must be a number, "
                f"got {type(crash_pct).__name__}: {crash_pct!r}"
            )

        # Value range checks
        if alloc < 0:
            raise ValueError(
                f"Asset '{name}': 'allocation_pct' cannot be negative, got {alloc}"
            )
        if crash_pct > 0:
            raise ValueError(
                f"Asset '{name}': 'expected_crash_pct' must be <= 0 "
                f"(crashes reduce value), got {crash_pct}"
            )

    #allocations must sum to 100
    total_alloc = sum(a["allocation_pct"] for a in assets)
    if round(total_alloc, 2) != 100.0:
        names = [a["name"] for a in assets]
        raise ValueError(
            f"Asset allocations must sum to 100%, got {total_alloc:.2f}%\n"
            f"  Assets: {names}\n"
            f"  Fix: adjust allocations so they add up to exactly 100"
        )


def compute_metrics_for_scenario(portfolio,severity=1.0):
    #compute risk metrics for one crash scenario, severity=1.0 is full crash and 0.5 half crash, where all crash percentage is redueced to half
    total = portfolio["total_value_inr"]
    expenses = portfolio["monthly_expenses_inr"]
    assets = portfolio["assets"]

    post_crash_value = 0
    for a in assets:
        asset_value = total * (a["allocation_pct"] / 100)
        loss = asset_value * (a["expected_crash_pct"] * severity / 100)
        post_crash_value += asset_value + loss
    
    if expenses > 0:
        runway_months = post_crash_value / expenses
    else:
        runway_months = float("inf")

    ruin_test = "PASS" if runway_months > 12 else "FAIL"

    largest_risk_asset = max(
        assets,
        key=lambda a: a["allocation_pct"] * abs(a["expected_crash_pct"] * severity)
    )["name"]

    concentration_warning = any(a["allocation_pct"] > 40 for a in assets)

    return {
        "post_crash_value": round(post_crash_value, 2),
        "runway_months": round(runway_months, 2),
        "ruin_test": ruin_test,
        "largest_risk_asset": largest_risk_asset,
        "concentration_warning": concentration_warning,
    }

def compute_risk_metrics(portfolio):
    #to calculate risk_metrics for both cases when crash is 100% and is 50%
    validate_portfolio(portfolio)
    severe = compute_metrics_for_scenario(portfolio, severity=1.0)
    moderate = compute_metrics_for_scenario(portfolio, severity=0.5)
    return {"severe": severe, "moderate": moderate}

def print_bar_chart(portfolio):
    print("\nAllocation Breakdown")
    print("-" * 40)
    for a in portfolio["assets"]:
        bars = "█" * a["allocation_pct"]
        print(f"{a['name']:<10} {bars} {a['allocation_pct']}%")

def print_report(metrics):
    print("\n=== Portfolio Risk Report ===")
    print(f"{'Metric':<22} {'Severe':>18} {'Moderate':>18}")
    print("-" * 60)
    keys = [
        ("post_crash_value", "Post-crash value (₹)"),
        ("runway_months", "Runway (months)"),
        ("ruin_test", "Ruin test"),
        ("largest_risk_asset", "Largest risk asset"),
        ("concentration_warning", "Concentration warn"),
    ]
    for key, label in keys:
        sev = metrics["severe"][key]
        mod = metrics["moderate"][key]
        if isinstance(sev, float):
            sev = f"{sev:,.2f}"
        if isinstance(mod, float):
            mod = f"{mod:,.2f}"
        print(f"{label:<22} {str(sev):>18} {str(mod):>18}")


if __name__=="__main__":
    portfolio = {
        "total_value_inr": 10_000_000,
        "monthly_expenses_inr": 80_000,
        "assets": [
            {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
        ],
    }

    metrics = compute_risk_metrics(portfolio)
    print_bar_chart(portfolio)
    print_report(metrics)
