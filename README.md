# timecell-intern-kalpshah

Submission for the Timecell AI engineering internship test — Summer 2026.

**Author:** Kalp Shah  
**Loom walkthrough:**(https://www.loom.com/share/844660c065224b6a87ca4a914be93590)

---

## What This Is

Four tasks, one coherent system. The core idea I kept coming back to while building this: the LLM should never touch the math. It explains, critiques, and narrates — but every number on screen comes from deterministic Python. Tasks 3 and 4 both import Task 1's calculator as their source of truth, so nothing gets hallucinated and everything is traceable.

---

## Architecture

```
                ┌──────────────────────────────────┐
                │         Task 1                   │
                │ Portfolio Risk Calculator        │
                │ Pure Python · deterministic math │
                │  compute_risk_metrics()          │
                └──────────────┬───────────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
              ▼                                 ▼
   ┌─────────────────────┐         ┌─────────────────────────┐
   │      Task 2         │         │        Task 3           │
   │  Market Data Fetch  │         │   AI Portfolio          │
   │  yfinance +         │         │   Explainer             │
   │  CoinGecko          │         │   Groq + Llama 3.3 70B  │
   │  rich CLI table     │         │   News (GNews) +        │
   └─────────────────────┘         │   tone + critique +     │
                                   │   revision loop         │
                                   └────────────┬────────────┘
                                                │
                                                ▼
                                   ┌─────────────────────────┐
                                   │        Task 4           │
                                   │  "What Breaks This?"    │
                                   │  Pre-mortem engine      │
                                   │  LLM proposes,          │
                                   │  engine disposes        │
                                   └─────────────────────────┘
```

---

## Tasks at a Glance

| Task | What It Does |
|------|--------------|
| 1 | Computes 5 risk metrics + severe/moderate crash scenarios + CLI bar chart |
| 2 | Fetches BTC, NIFTY 50, GOLD live with rich-formatted output |
| 3 | LLM explainer with tone control, live news context, critique + revision loop |
| 4 | Pre-mortem stress-tester, LLM proposes shocks, deterministic engine scores them |

Each task has its own README with run commands and sample output.

---

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

---

## Design Decisions

**Why Groq + Llama 3.3 70B?**  
Free tier, no credit card, sub-second responses. The architecture is provider-agnostic — swapping in Claude or Gemini is one line in `assumption_generator.py` or `explainer.py`.

**Why does the LLM never compute numbers?**  
Early versions of Task 4 had the LLM calculate runway directly — it produced plausible-looking but non-reproducible numbers. The fix: LLM only proposes structured stress changes like `{"asset": "BTC", "new_value": -95}`, and a deterministic engine applies them through Task 1's calculator. Every number is now auditable. This ended up being the most important architectural decision in the whole project.

**Why GNews for news context?**  
GDELT timed out consistently. Yahoo Finance RSS rate-limited on burst requests. GNews is reliable, returns English-only articles, and the free tier (100 req/day) is more than enough for a portfolio of 3–5 assets.

---

## The Hardest Part

Task 4 broke and got rebuilt twice. The first version let the LLM do the math — fast to write, wrong in practice. The second version separated concerns properly: LLM for judgment, Python for arithmetic. Getting that boundary right took longer than building any individual feature, but it's also what makes the output actually trustworthy.

---

## What I'd Build Next

- **Correlation modeling in Task 4.** Right now each stress change is independent. In real crashes, BTC and NIFTY don't fall independently — a correlation matrix would let one assumption trigger realistic joint moves across assets.

- **Historically grounded confidence scores.** Task 4's confidence percentages are LLM estimates. Better to anchor them in base rates — how often has BTC actually exceeded -80% drawdown in a 12-month window?

- **Side-by-side decision comparison.** Task 4 stress-tests one decision at a time. A more useful tool would take two portfolio allocations and return a comparative failure profile — useful when you're weighing two real options.

---

## Repository Structure

```
timecell-intern-kalpshah/
├── README.md
├── requirements.txt
├── task1/
│   ├── README.md
│   ├── portfolio_risk_calculator.py
│   └── test_calculator.py
├── task2/
│   ├── README.md
│   ├── data_fetcher.py
│   └── test_fetcher.py
├── task3/
│   ├── README.md
│   ├── explainer.py          # main entry
│   ├── prompt.py             # tone-aware prompt builder
│   ├── critique.py           # auditor pass
│   ├── reviser.py            # revision loop
│   ├── news_fetch.py         # GNews context
│   ├── formatter.py          # rich card output
│   ├── prompts/              # v1, v2, v3 prompt iterations
│   └── example_portfolio/
└── task4/
    ├── README.md
    ├── main.py
    ├── input_handler.py
    ├── assumption_generator.py
    ├── scenario_engine.py
    ├── comparator.py
    ├── reporter.py
    └── example_scenario/
```
