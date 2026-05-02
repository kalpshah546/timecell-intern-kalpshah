"""
input_handler.py
Loads portfolio JSON and parses CLI arguments.
Validation lives here so the rest of the pipeline can trust its inputs.
"""

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """Define and parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="What Breaks This? — Stress-test a portfolio decision.",
    )
    parser.add_argument(
        "portfolio_file",
        type=str,
        help="Path to portfolio JSON file",
    )
    parser.add_argument(
        "decision",
        type=str,
        help="Decision to stress test (e.g. 'increase BTC from 30%% to 45%%')",
    )
    parser.add_argument(
        "--num-assumptions",
        type=int,
        default=5,
        help="Number of assumptions to extract (default: 5)",
    )
    return parser.parse_args()


def load_portfolio(path: str) -> dict:
    """Load and validate a portfolio JSON file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Portfolio file not found: {path}")

    with open(p) as f:
        portfolio = json.load(f)

    # Light validation; full math validation happens in compute_risk_metrics
    required_keys = {"total_value_inr", "monthly_expenses_inr", "assets"}
    missing = required_keys - portfolio.keys()
    if missing:
        raise ValueError(f"Portfolio missing keys: {missing}")

    if not portfolio["assets"]:
        raise ValueError("Portfolio has no assets")

    return portfolio