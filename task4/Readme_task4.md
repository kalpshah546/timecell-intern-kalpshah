# Task 4 — "What Breaks This?" Engine

A pre-mortem CLI for portfolio decisions.


Timecell's homepage asks:

> *"Show me the assumption you'd have to be wrong about for this to be the wrong call."*

This tool answers exactly that question. You give it a portfolio and a proposed decision in plain English. It returns the load-bearing assumptions, each with a confidence score and a deterministic simulation of what happens to runway, post-crash value, and ruin test if that assumption fails.

## How It Fits Timecell's Four Pillars

| Pillar | How this tool delivers it |
|---|---|
| **Math** | Every number on screen comes from Task 1's `compute_risk_metrics`. The LLM never produces numbers. |
| **Conviction** | Each assumption carries an explicit confidence percentage (0–100%). Color-coded in the output. |
| **Coverage** | First-class support for BTC and Indian equity (the assets in the example portfolios). No "US 60/40" baked in. |
| **Traceability** | Every output line references its input — which asset changed, by how much, computed against which baseline. The LLM proposes; the engine logs exactly what it did. |

## Architecture

The engine is built on one core decision: **the LLM is the creative layer; the engine is the audit layer. They check each other.**

```
                   user decision (NL) + portfolio
                              │
                              ▼
                ┌─────────────────────────────────┐
                │   assumption_generator (LLM)    │  proposes:
                │                                 │  - decision_changes
                │   ONE Groq call returns:        │  - 5 assumptions
                │   - structured allocation       │  - stress_change spec
                │     changes                     │     for each
                │   - 5 assumptions w/ confidence │
                │   - stress_change instructions  │
                └────────────────┬────────────────┘
                                 │
                                 ▼
                ┌─────────────────────────────────┐
                │   scenario_engine (PURE)        │  enforces:
                │                                 │  - sum(allocations) == 100
                │   apply_decision()              │  - assets exist
                │   apply_stress_change()         │  - typed stress changes
                │   run_scenario() →              │  reuses Task 1
                │     compute_risk_metrics()      │
                └────────────────┬────────────────┘
                                 │
                                 ▼
                ┌─────────────────────────────────┐
                │   comparator (PURE)             │  computes:
                │   compare_metrics()             │  - runway delta
                │   severity_level()              │  - ruin-test flip
                │                                 │  - severity bucket
                └────────────────┬────────────────┘
                                 │
                                 ▼
                ┌─────────────────────────────────┐
                │   reporter (rich)               │  prints:
                │                                 │  - per-assumption block
                │   print_assumption()            │  - severity-colored
                │   print_summary()               │  - summary table
                └─────────────────────────────────┘
```

If the LLM hallucinates an unrealistic confidence ("99% confident BTC won't drop below -80%"), the human reading the output catches it. If the LLM proposes a structurally invalid stress change (sum doesn't equal 100, asset doesn't exist), the engine refuses to run it. Each layer guards against the other's failure modes.

## Run

```bash
cd task4
python main.py example_scenario/portfolio_balanced.json "increase BTC from 30% to 45%"
```

Other example decisions:

```bash
python main.py example_scenario/portfolio_balanced.json "move 20% from gold into Indian equity"
python main.py example_scenario/portfolio_balanced.json "reduce cash to 5% and add real estate"
```

Flags:
- `--num-assumptions N` — default 5

## Sample Output Shape

```
WHAT BREAKS THIS?
Decision: Increase BTC from 30% to 45% by reducing CASH and NIFTY50

1. BTC's max drawdown stays within historical bounds (-80%)
   Confidence: 65%   |   Severity if wrong: HIGH
   Why it matters: A 45% allocation makes the portfolio binary on BTC's worst-case path.
   IF WRONG:
     → BTC crash worsens to -95%
     → Runway: 71.3 → 14.2 months (-57.1)
     → Post-crash value: ₹5,700,000 → ₹1,140,000 (-4,560,000)
     → Ruin test: PASS → FAIL  ⚠

2. ...

Summary
┌───┬────────────────────────────────────────────────────┬────────────┬──────────┬──────────┐
│ # │ Assumption                                          │ Confidence │ Severity │ Runway Δ │
├───┼────────────────────────────────────────────────────┼────────────┼──────────┼──────────┤
│ 1 │ BTC's max drawdown stays within historical bounds  │ 65%        │ HIGH     │ -57.1    │
│ 2 │ Indian equity provides uncorrelated cushion        │ 80%        │ MEDIUM   │ -22.4    │
│ 3 │ ...                                                 │            │          │          │
└───┴────────────────────────────────────────────────────┴────────────┴──────────┴──────────┘
```

## Another options and why I chose this idea : 



**Monte Carlo simulator** — quantitatively respectable: simulate 10,000 random crash scenarios, output survival probability, have the LLM narrate. The problem is every quant-leaning candidate will think of it. It's the obvious move from the brief. It also doesn't engage with Timecell's actual product philosophy — it's just statistics with a chat layer on top.

**Multi-custodian price aggregator** — would integrate yfinance, Indian broker APIs, crypto exchange APIs into a unified portfolio view. Addepar already has 650+ direct custodian feeds, Masttro has 10,000+ users across 35 countries. That's a game I can't credibly win in 8 hours of build time, and it's the wrong domain for Timecell — they explicitly position against the dashboard model.


## Limitations

- **No cross-asset correlation.** Each stress change is independent. In real shocks, BTC and NIFTY don't crash independently — a 2008-style event hits both. Adding a correlation matrix would let one assumption trigger plausible joint moves.
- **Confidence scores are LLM judgments, not statistical.** The LLM says "65% confident BTC stays within historical drawdown" based on its training. Better: ground that in actual base rates from historical price data.
- **Single-decision only.** A CIO often weighs two paths against each other ("increase BTC vs. add real estate"). Right now you'd run the tool twice and compare manually. A multi-decision mode is the obvious next feature.
- **Expense-shock stress is coarse.** The LLM can propose `expenses` stress, but it's a single new value, not a model of inflation or one-time medical events.

