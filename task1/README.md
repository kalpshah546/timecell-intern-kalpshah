# Task 1 — Portfolio Risk Calculator

Computes risk metrics for a portfolio under crash scenarios. Pure Python, no external dependencies for the math itself.

## What It Computes

Given a portfolio (total value, monthly expenses, list of assets each with `allocation_pct` and `expected_crash_pct`), `compute_risk_metrics(portfolio)` returns both a severe scenario (full expected crash) and a moderate scenario (50% of expected crash):

| Metric | Meaning |
|---|---|
| `post_crash_value` | Total INR remaining after the crash |
| `runway_months` | How many months post-crash value covers monthly expenses |
| `ruin_test` | "PASS" if runway > 12 months, else "FAIL" |
| `largest_risk_asset` | Asset with highest `allocation × |crash|` score |
| `concentration_warning` | True if any single asset > 40% of portfolio |

The bonus moderate scenario is implemented via a `severity` multiplier (1.0 for severe, 0.5 for moderate), keeping the math in one function rather than duplicating it.

## Run

```bash
cd task1
python portfolio_risk_calculator.py
```

Example output:

```
Allocation Breakdown
----------------------------------------
BTC        ██████████████████████████████ 30%
NIFTY50    ████████████████████████████████████████ 40%
GOLD       ████████████████████ 20%
CASH       ██████████ 10%

=== Portfolio Risk Report ===
Metric                             Severe           Moderate
------------------------------------------------------------
Post-crash value (₹)         5,700,000.00       7,850,000.00
Runway (months)                     71.25              98.12
Ruin test                            PASS               PASS
Largest risk asset                    BTC                BTC
Concentration warn                  False              False
```

The CLI bar chart uses Unicode `█` blocks — no plotting libraries.

## Tests

```bash
pytest -v
```

Covers happy path, edge cases (zero expenses → infinite runway, all-cash portfolio, exact-40% boundary for concentration warning), and validation rejections (negative allocation, allocations not summing to 100, empty assets list, positive crash percentage).

## Edge Cases Handled

| Case | Behavior |
|---|---|
| Allocations don't sum to 100 | Validation raises `ValueError` |
| `monthly_expenses_inr = 0` | Runway returns `float('inf')` |
| Negative `total_value_inr` | Validation rejects |
| Empty `assets` list | Validation rejects |
| Negative `allocation_pct` | Validation rejects |
| Positive `expected_crash_pct` | Validation rejects (crashes are losses, not gains) |
| Single asset at 100% | Computes correctly; concentration warning fires |

## What I Tried That Didn't Work

Initially I duplicated the math function for the moderate scenario — copy-pasted the loop with hardcoded `* 0.5`. After writing it I noticed the only difference was the multiplier, so I refactored into one function with a `severity` parameter. This collapsed two functions into one, made adding new severity levels trivial, and meant any math fix automatically applies to both scenarios.

I also tried Pydantic for input validation. It was overkill for a single function with a known schema — plain `validate_portfolio()` with explicit `raise ValueError` calls is shorter and equally clear, and avoids dragging Pydantic into a module that has no other use for it.

## AI Usage Note

I used Claude to brainstorm edge cases (specifically the zero-expenses → infinite-runway case and the exact-40% boundary for concentration warning) and to review my math against the spec. I wrote every line of the calculator myself and tested each case manually before adding `pytest` cases.
