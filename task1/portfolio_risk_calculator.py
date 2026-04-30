def validate_portfolio(portfolio):
    #check if portfolio is valid and raise ValueError if not
    total=portfolio["total_value_inr"]
    expenses=portfolio["monthly_expenses_inr"]
    assets=portfolio["assets"]

    if total < 0:
        raise ValueError("total_value_inr cannot be negative")
    if expenses < 0:
        raise ValueError("monthly_expenses_inr cannot be negative")
    if not assets:
        raise ValueError("assets list cannot be empty")
    
    for a in assets:
        if a["allocation_pct"] < 0:
            raise ValueError(f"{a['name']} has negative allocation")
        if a["expected_crash_pct"] > 0:
            raise ValueError(f"{a['name']} crash_pct must be <= 0")
        
    total_alloc = sum(a["allocation_pct"] for a in assets)
    if round(total_alloc, 2) != 100:
        raise ValueError(f"Allocations sum to {total_alloc}%, must be 100%")


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
