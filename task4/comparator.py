"""
comparator.py
Computes the delta between a baseline metric set and a stressed metric set.
Pure data transformation — no IO, no LLM.
"""


def compare_metrics(baseline: dict, stressed: dict) -> dict:
    """
    Compute the differences between baseline and stressed risk metrics.
    Returns a dict that's easy for the reporter to render.
    """
    runway_baseline = baseline["runway_months"]
    runway_stressed = stressed["runway_months"]

    return {
        "runway_baseline": runway_baseline,
        "runway_stressed": runway_stressed,
        "runway_delta": round(runway_stressed - runway_baseline, 2),
        "post_crash_baseline": baseline["post_crash_value"],
        "post_crash_stressed": stressed["post_crash_value"],
        "post_crash_delta": round(
            stressed["post_crash_value"] - baseline["post_crash_value"], 2
        ),
        "ruin_test_baseline": baseline["ruin_test"],
        "ruin_test_stressed": stressed["ruin_test"],
        "ruin_test_changed": baseline["ruin_test"] != stressed["ruin_test"],
        "largest_risk_baseline": baseline["largest_risk_asset"],
        "largest_risk_stressed": stressed["largest_risk_asset"],
    }


def severity_level(comparison: dict) -> str:
    """
    Classify how bad the stress is.
    Used by the reporter for color-coding.
    """
    if comparison["ruin_test_changed"] and comparison["ruin_test_stressed"] == "FAIL":
        return "CRITICAL"

    runway_drop = comparison["runway_baseline"] - comparison["runway_stressed"]
    if runway_drop > 24:
        return "HIGH"
    elif runway_drop > 6:
        return "MEDIUM"
    return "LOW"