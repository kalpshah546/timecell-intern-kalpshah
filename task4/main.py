"""
main.py
Orchestrates the pre-mortem pipeline:
  1. Parse CLI args + load portfolio
  2. Call LLM to interpret decision and extract assumptions
  3. Apply decision deterministically → baseline metrics
  4. For each assumption, apply stress change → stressed metrics
  5. Compare and report

Entry point for `python main.py <portfolio.json> "<decision>"`
"""

import os
import sys

from dotenv import load_dotenv
from groq import Groq

from input_handler import parse_args, load_portfolio
from assumption_generator import generate_assumptions
from scenario_engine import apply_decision, run_scenario
from comparator import compare_metrics, severity_level
from reporter import print_header, print_assumption, print_summary


def run_premortem(portfolio: dict, decision: str, num_assumptions: int = 5) -> dict:
    """End-to-end pipeline. Returns a dict of all results for downstream use/testing."""
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # Step 1: LLM extracts decision changes + assumptions
    print("→ Calling LLM for assumption extraction...")
    llm_output = generate_assumptions(
        client=client,
        portfolio=portfolio,
        decision=decision,
        num_assumptions=num_assumptions,
    )

    decision_summary = llm_output.get("decision_summary", decision)
    decision_changes = llm_output.get("decision_changes", [])
    assumptions = llm_output.get("assumptions", [])

    # Step 2: Apply decision to get post-decision portfolio
    print("→ Applying decision to portfolio...")
    post_decision_portfolio = apply_decision(portfolio, decision_changes)

    # Step 3: Compute baseline (post-decision, expected crash assumptions)
    print("→ Computing baseline risk under expected crash assumptions...")
    baseline = run_scenario(post_decision_portfolio)

    # Step 4: For each assumption, apply stress + compute new metrics
    print(f"→ Stress-testing {len(assumptions)} assumption(s)...\n")
    print_header(decision_summary)

    summary_rows = []
    for i, assumption in enumerate(assumptions, start=1):
        try:
            stressed = run_scenario(
                post_decision_portfolio,
                stress_change=assumption["stress_change"],
            )
            comparison = compare_metrics(baseline, stressed)
            severity = severity_level(comparison)
            print_assumption(i, assumption, comparison, severity)
            summary_rows.append({
                "assumption": assumption["assumption"],
                "confidence": assumption["confidence"],
                "runway_delta": comparison["runway_delta"],
                "severity": severity,
            })
        except Exception as exc:
            print(f"[warn] Skipping assumption {i} due to error: {exc}")

    # Step 5: Final summary table
    print_summary(summary_rows)

    return {
        "decision_summary": decision_summary,
        "baseline": baseline,
        "assumptions": summary_rows,
    }


def main():
    load_dotenv()

    if "GROQ_API_KEY" not in os.environ:
        print("[error] GROQ_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    try:
        args = parse_args()
        portfolio = load_portfolio(args.portfolio_file)
        run_premortem(portfolio, args.decision, args.num_assumptions)
    except FileNotFoundError as e:
        print(f"[error] {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"[error] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()