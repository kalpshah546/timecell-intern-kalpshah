"""
scenario_engine.py
Applies decision changes and stress changes to portfolios deterministically.
Then re-runs the Task 1 risk calculator.

This file contains zero LLM calls. It is pure, testable, deterministic Python.
This separation is the heart of the design: the LLM proposes, the engine disposes.
"""

import copy
import sys
from pathlib import Path

# Reuse Task 1's risk calculator
sys.path.append(str(Path(__file__).parent.parent))
from task1.portfolio_risk_calculator import compute_risk_metrics


def apply_decision(portfolio: dict, decision_changes: list) -> dict:
    """
    Apply LLM-proposed allocation changes to the portfolio.
    Returns a NEW portfolio (does not mutate input).
    """
    new_portfolio = copy.deepcopy(portfolio)

    # Build a lookup for quick mutation
    asset_lookup = {a["name"]: a for a in new_portfolio["assets"]}

    for change in decision_changes:
        name = change["asset"]
        if name not in asset_lookup:
            raise ValueError(f"Decision references unknown asset: {name}")
        asset_lookup[name]["allocation_pct"] = change["new_allocation_pct"]

    # Sanity check: allocations must sum to 100
    total = sum(a["allocation_pct"] for a in new_portfolio["assets"])
    if round(total, 2) != 100:
        raise ValueError(
            f"Decision produces invalid allocations summing to {total}%. "
            f"LLM may have proposed an inconsistent change set."
        )

    return new_portfolio


def apply_stress_change(portfolio: dict, stress_change: dict) -> dict:
    """
    Apply ONE assumption-failure scenario to a portfolio.
    Returns a NEW portfolio (does not mutate input).
    """
    new_portfolio = copy.deepcopy(portfolio)
    asset_lookup = {a["name"]: a for a in new_portfolio["assets"]}

    stress_type = stress_change.get("type")

    if stress_type == "crash_pct":
        # Worsen one asset's crash %
        asset = stress_change.get("asset")
        new_value = stress_change.get("new_value")
        if asset not in asset_lookup:
            raise ValueError(f"Stress change references unknown asset: {asset}")
        asset_lookup[asset]["expected_crash_pct"] = new_value

    elif stress_type == "multi_crash":
        # Worsen multiple assets' crash %s (correlation shock)
        new_values = stress_change.get("new_values", {})
        for asset_name, crash_value in new_values.items():
            if asset_name not in asset_lookup:
                raise ValueError(f"Stress change references unknown asset: {asset_name}")
            asset_lookup[asset_name]["expected_crash_pct"] = crash_value

    elif stress_type == "expenses":
        # Increase monthly expenses
        new_portfolio["monthly_expenses_inr"] = stress_change.get("new_value")

    else:
        raise ValueError(f"Unknown stress_change type: {stress_type}")

    return new_portfolio


def run_scenario(portfolio: dict, stress_change: dict | None = None) -> dict:
    """
    Run the risk calculator on a portfolio (optionally after applying a stress change).
    Returns the severe-scenario metrics for clean comparison.
    """
    if stress_change:
        portfolio = apply_stress_change(portfolio, stress_change)

    full_metrics = compute_risk_metrics(portfolio)
    # We compare on the severe scenario — that's what pre-mortem cares about
    return full_metrics["severe"]