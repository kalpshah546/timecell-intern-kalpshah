<div align="center">

# timecell-intern-kalpshah

**Timecell AI Engineering Internship · Summer 2026**

A four-task submission built on one principle: *the LLM should never touch the math.*

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Groq](https://img.shields.io/badge/LLM-Llama_3.3_70B_via_Groq-orange)](https://groq.com/)
[![Status](https://img.shields.io/badge/Status-Submitted-success)]()

**Author:** Kalp Shah  
**Walkthrough:** [Loom (5 min)](https://www.loom.com/share/844660c065224b6a87ca4a914be93590)

</div>

## The Core Idea

> "Crash survival, runway, portfolio math — computed in code, not guessed by a language model."
> — timecell.ai

Every task in this repo respects that line. The LLM explains, critiques, and narrates. It never produces a number. Tasks 3 and 4 both import Task 1's calculator as their source of truth, so nothing gets hallucinated and every output is traceable to its inputs.

## System Architecture

```
              ┌──────────────────────────────────────┐
              │             TASK 1                   │
              │   Portfolio Risk Calculator          │
              │   Pure Python · deterministic math   │
              │   compute_risk_metrics()             │
              └──────────────────┬───────────────────┘
                                 │
                                 │  (imported as ground truth)
                                 │
            ┌────────────────────┼────────────────────┐
            │                                         │
            ▼                                         ▼
┌──────────────────────┐               ┌─────────────────────────┐
│       TASK 2         │               │         TASK 3          │
│  Market Data Fetch   │               │   AI Portfolio          │
│                      │               │   Explainer             │
│  yfinance +          │               │                         │
│  CoinGecko           │               │   Groq · Llama 3.3 70B  │
│  rich CLI table      │               │   GNews context         │
│  latency + status +  │               │   tone control          │
│  summary line        │               │   critique + revision   │
└──────────────────────┘               └────────────┬────────────┘
                                                    │
                                                    │  (LLM patterns reused)
                                                    │
                                                    ▼
                                       ┌─────────────────────────┐
                                       │         TASK 4          │
                                       │  "What Breaks This?"    │
                                       │  Pre-mortem engine      │
                                       │                         │
                                       │  LLM proposes shocks    │
                                       │  Engine scores them     │
                                       │  (reuses Task 1)        │
                                       └─────────────────────────┘
```

The arrows matter. Task 1 is the foundation. Task 3 reuses its math. Task 4 reuses both Task 1's math and Task 3's prompt-engineering patterns.

## Tasks at a Glance

| # | Task | Points | Built With |
|---|------|--------|------------|
| 1 | Portfolio Risk Calculator | 30 | Pure Python, pytest |
| 2 | Live Market Data Fetcher | 20 | yfinance, CoinGecko, rich |
| 3 | AI-Powered Portfolio Explainer | 30 | Groq, GNews, rich |
| 4 | "What Breaks This?" Pre-mortem | 20 | Groq + Task 1 calculator |

Each task has its own `README.md` inside its folder.

## Sample Outputs

**Task 1 — Risk Calculator**

```
Allocation Breakdown
BTC        ██████████████████████████████ 30%
NIFTY50    ████████████████████████████████████████ 40%
GOLD       ████████████████████ 20%
CASH       ██████████ 10%

=== Portfolio Risk Report ===
Metric                             Severe           Moderate
Post-crash value (₹)         5,700,000.00       7,850,000.00
Runway (months)                     71.25              98.12
Ruin test                            PASS               PASS
Largest risk asset                    BTC                BTC
Concentration warn                  False              False
```

**Task 2 — Live Market Fetcher**

```
                   Asset Prices — 2026-05-02 14:32:11 IST
╭──────────────┬──────────────┬──────────┬─────────────┬──────────┬──────────╮
│ Asset        │     Price    │ Currency │  24h Change │ Latency  │  Status  │
├──────────────┼──────────────┼──────────┼─────────────┼──────────┼──────────┤
│ NIFTY 50     │  ₹22,500.50  │   INR    │  ▲ 1.12%    │  340 ms  │    OK    │
│ Gold (COMEX) │   $2,341.20  │   USD    │  ▼ 0.45%    │  280 ms  │    OK    │
│ Bitcoin      │  $62,341.20  │   USD    │  ▲ 2.45%    │  180 ms  │    OK    │
╰──────────────┴──────────────┴──────────┴─────────────┴──────────┴──────────╯
Summary: 3/3 assets fetched successfully.
```

**Task 3 — AI Explainer**

```
╭─────────────────────────── Verdict ───────────────────────────╮
│  BALANCED                                                     │
╰───────────────────────────────────────────────────────────────╯
╭──────────────────────────── Summary ──────────────────────────╮
│ Your portfolio holds 30% BTC, 40% NIFTY50, 20% GOLD, 10% CASH.│
│ Even in a severe crash scenario, you'd retain ₹57L which      │
│ covers 71 months of expenses — well above the 12-month        │
│ ruin threshold. Risk is moderate but BTC dominates the tail.  │
╰───────────────────────────────────────────────────────────────╯
╭───────────────────── What You're Doing Well ──────────────────╮
│ A 71-month runway means you have ~6 years of buffer even if   │
│ markets crash hard. That's exceptional.                       │
╰───────────────────────────────────────────────────────────────╯
╭──────────────────────── What to Change ───────────────────────╮
│ BTC at 30% accounts for 67% of your crash-scenario losses.    │
│ Consider trimming to 20% — runway only drops from 71 to 65    │
│ months but tail risk becomes far more manageable.             │
╰───────────────────────────────────────────────────────────────╯
╭──────────────────────── Auditor Review ───────────────────────╮
│ Accuracy: 9/10  ·  Verdict agrees: ✓  ·  Recommendation: accept│
╰───────────────────────────────────────────────────────────────╯
```

**Task 4 — Pre-mortem Engine**

```
╭────────────────── WHAT BREAKS THIS? ─────────────────╮
│  Decision: Increase BTC from 30% to 45%              │
╰──────────────────────────────────────────────────────╯

BTC's max drawdown stays within historical bounds (-80%)
Confidence: 65%   |   Severity if wrong: HIGH
IF WRONG:
→ BTC crash worsens to -95%
→ Runway: 71.3 → 14.2 months (-57.1)
→ Post-crash value: ₹5,700,000 → ₹1,140,000 (-4,560,000)
→ Ruin test: PASS → FAIL

NIFTY moves uncorrelated with BTC during shocks
Confidence: 80%   |   Severity if wrong: MEDIUM
IF WRONG:
→ BTC crash to -80%, NIFTY crash to -55% (joint shock)
→ Runway: 71.3 → 28.4 months (-42.9)
→ Ruin test: PASS (unchanged)

[... 3 more assumptions ...]

                        Summary
┌───┬────────────────────────────────────────┬────────────┬──────────┬──────────┐
│ # │ Assumption                             │ Confidence │ Severity │ Runway Δ │
├───┼────────────────────────────────────────┼────────────┼──────────┼──────────┤
│ 1 │ BTC max drawdown stays within bounds   │   65%      │   HIGH   │  -57.1   │
│ 2 │ NIFTY uncorrelated with BTC            │   80%      │  MEDIUM  │  -42.9   │
│ 3 │ Indian regulators don't ban crypto     │   90%      │   HIGH   │  -38.0   │
│ 4 │ Liquidity holds for forced exits       │   70%      │  MEDIUM  │  -12.5   │
│ 5 │ Monthly expenses stay at ₹80K          │   75%      │   LOW    │   -3.2   │
└───┴────────────────────────────────────────┴────────────┴──────────┴──────────┘
```

## Quick Start

```bash
git clone https://github.com/kalpshah546/timecell-intern-kalpshah
cd timecell-intern-kalpshah

python -m venv venv
source venv/Scripts/activate    # Windows Git Bash
# source venv/bin/activate      # macOS/Linux

pip install -r requirements.txt

cp task3/.env.example task3/.env
cp task4/.env.example task4/.env
# Paste your free Groq key into both .env files
```

Each task's README has its own run commands.

## Design Decisions

**Why Groq + Llama 3.3 70B?**
Free tier, no credit card, sub-second responses. The architecture is provider-agnostic — swapping in Claude or Gemini is one line in `assumption_generator.py` or `explainer.py`.

**Why does the LLM never compute numbers?**
Early versions of Task 4 had the LLM calculate runway directly. It produced plausible-looking but non-reproducible numbers — fluent and wrong is more dangerous than obviously wrong. The fix: the LLM only proposes structured stress changes like `{"asset": "BTC", "new_value": -95}`, and a deterministic engine applies them through Task 1's calculator. Every number is now auditable. This ended up being the most important architectural decision in the whole project.

**Why GNews instead of GDELT?**
GDELT timed out consistently in early testing. Yahoo Finance RSS rate-limited on burst requests. GNews is reliable, returns English-only articles, and the free tier (100 req/day) is more than enough for a portfolio of 3–5 assets.

## What I'd Build Next

**Cross-asset correlation modeling** in Task 4. Today each stress is independent; in real shocks BTC and NIFTY move together. A correlation matrix would let one assumption trigger plausible joint moves.

**Base-rate-calibrated confidence scores.** Task 4's confidence percentages are LLM judgments. Better: ground them in historical drawdown frequency.

**Multi-decision comparison.** A CIO often weighs two paths against each other. Right now you'd run the tool twice and compare manually. A side-by-side mode is the obvious next feature.

## The Hardest Part

Task 4 broke and got rebuilt twice. The first version let the LLM do the math — fast to write, wrong in practice. The second version separated concerns properly: LLM for judgment, Python for arithmetic. Getting that boundary right took longer than building any individual feature, but it's also what makes the output actually trustworthy.

## Repository Structure

```
timecell-intern-kalpshah/
├── README.md
├── requirements.txt
│
├── task1/                             # Risk Calculator
│   ├── README.md
│   ├── portfolio_risk_calculator.py
│   └── test_calculator.py
│
├── task2/                             # Market Data Fetcher
│   ├── README.md
│   ├── data_fetcher.py
│   └── test_fetcher.py
│
├── task3/                             # AI Explainer
│   ├── README.md
│   ├── explainer.py
│   ├── prompt.py
│   ├── critique.py
│   ├── reviser.py
│   ├── news_fetch.py
│   ├── formatter.py
│   ├── prompts/
│   └── example_portfolio/
│
└── task4/                             # Pre-mortem Engine
    ├── README.md
    ├── main.py
    ├── input_handler.py
    ├── assumption_generator.py
    ├── scenario_engine.py
    ├── comparator.py
    ├── reporter.py
    └── example_scenario/
```

<div align="center">

*Built in 72 hours. Math in code, narrative in LLM, every number traceable.*

</div>
