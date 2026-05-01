

import math
import pytest
from portfolio_risk_calculator import compute_risk_metrics, validate_portfolio


def test_portfolio_not_dict():
    with pytest.raises(ValueError):
        compute_risk_metrics("not a dict")

def test_missing_keys():
    p = {"total_value_inr": 1000}
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_invalid_types():
    p = base_portfolio()
    p["total_value_inr"] = "1000"
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

    p = base_portfolio()
    p["monthly_expenses_inr"] = "bad"
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

    p = base_portfolio()
    p["assets"] = "not a list"
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_negative_values():
    p = base_portfolio()
    p["total_value_inr"] = -100
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

    p = base_portfolio()
    p["monthly_expenses_inr"] = -100
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_asset_not_dict():
    p = base_portfolio()
    p["assets"][0] = "bad"
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_missing_asset_fields():
    p = base_portfolio()
    del p["assets"][0]["name"]
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_invalid_asset_name():
    p = base_portfolio()
    p["assets"][0]["name"] = ""
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_allocation_not_number():
    p = base_portfolio()
    p["assets"][0]["allocation_pct"] = "bad"
    with pytest.raises(ValueError):
        compute_risk_metrics(p)

def test_crash_not_number():
    p = base_portfolio()
    p["assets"][0]["expected_crash_pct"] = "bad"
    with pytest.raises(ValueError):
        compute_risk_metrics(p)
def test_largest_risk_asset_changes():
    p = base_portfolio()
    p["assets"][1]["expected_crash_pct"] = -90  
    result = compute_risk_metrics(p)

    assert result["severe"]["largest_risk_asset"] == "NIFTY50"

def test_print_functions(capsys):
    p = base_portfolio()
    result = compute_risk_metrics(p)

    from portfolio_risk_calculator import print_bar_chart, print_report

    print_bar_chart(p)
    print_report(result)

    captured = capsys.readouterr()
    assert "Portfolio Risk Report" in captured.out
def base_portfolio():
    return {
        "total_value_inr": 10_000_000,
        "monthly_expenses_inr": 80_000,
        "assets": [
            {"name": "BTC",     "allocation_pct": 30, "expected_crash_pct": -80},
            {"name": "NIFTY50", "allocation_pct": 40, "expected_crash_pct": -40},
            {"name": "GOLD",    "allocation_pct": 20, "expected_crash_pct": -15},
            {"name": "CASH",    "allocation_pct": 10, "expected_crash_pct": 0},
        ],
    }


def test_severe_post_crash_value():
    result = compute_risk_metrics(base_portfolio())
    # Manual: 6L + 24L + 17L + 10L = 57L
    assert result["severe"]["post_crash_value"] == 5_700_000.00


def test_moderate_is_better_than_severe():
    result = compute_risk_metrics(base_portfolio())
    assert result["moderate"]["post_crash_value"] > result["severe"]["post_crash_value"]
    assert result["moderate"]["runway_months"] > result["severe"]["runway_months"]


def test_ruin_test_pass():
    result = compute_risk_metrics(base_portfolio())
    assert result["severe"]["ruin_test"] == "PASS"


def test_largest_risk_asset_is_btc():
    result = compute_risk_metrics(base_portfolio())
    assert result["severe"]["largest_risk_asset"] == "BTC"


def test_concentration_warning_false_at_exactly_40():
    # for > and >=
    result = compute_risk_metrics(base_portfolio())
    assert result["severe"]["concentration_warning"] is False


def test_concentration_warning_true_above_40():
    p = base_portfolio()
    p["assets"][1]["allocation_pct"] = 45
    p["assets"][3]["allocation_pct"] = 5  # rebalance to keep sum = 100
    result = compute_risk_metrics(p)
    assert result["severe"]["concentration_warning"] is True


def test_zero_expenses_gives_infinite_runway():
    p = base_portfolio()
    p["monthly_expenses_inr"] = 0
    result = compute_risk_metrics(p)
    assert math.isinf(result["severe"]["runway_months"])


def test_all_cash_portfolio_no_loss():
    p = {
        "total_value_inr": 1_000_000,
        "monthly_expenses_inr": 50_000,
        "assets": [{"name": "CASH", "allocation_pct": 100, "expected_crash_pct": 0}],
    }
    result = compute_risk_metrics(p)
    assert result["severe"]["post_crash_value"] == 1_000_000
    assert result["severe"]["concentration_warning"] is True  # 100 > 40


def test_ruin_test_fails_when_runway_short():
    p = base_portfolio()
    p["monthly_expenses_inr"] = 1_000_000  # ₹10L/month — burns through fast
    result = compute_risk_metrics(p)
    assert result["severe"]["ruin_test"] == "FAIL"


def test_allocations_must_sum_to_100():
    p = base_portfolio()
    p["assets"][0]["allocation_pct"] = 25  # now sums to 95
    with pytest.raises(ValueError):
        compute_risk_metrics(p)


def test_negative_allocation_rejected():
    p = base_portfolio()
    p["assets"][0]["allocation_pct"] = -10
    with pytest.raises(ValueError):
        compute_risk_metrics(p)


def test_positive_crash_pct_rejected():
    p = base_portfolio()
    p["assets"][0]["expected_crash_pct"] = 20  # crashes are losses, not gains
    with pytest.raises(ValueError):
        compute_risk_metrics(p)


def test_empty_assets_rejected():
    p = base_portfolio()
    p["assets"] = []
    with pytest.raises(ValueError):
        compute_risk_metrics(p)