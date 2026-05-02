# Task 3 — AI-Powered Portfolio Explainer

Takes a portfolio, runs Task 1's risk math, optionally fetches news context, and asks an LLM to produce a structured plain-English explanation. Both bonuses are implemented: configurable tone (beginner/experienced/expert) and a critique loop with revision.

## Why Groq + Llama 3.3 70B

- **Free tier, no credit card** — generous limits (~30 req/min)
- **OpenAI-compatible API** — provider-agnostic; swapping to Claude or GPT is one file change
- **Sub-second responses** — fast prompt iteration mattered when I was rewriting v1 → v2 → v3
- **Strong JSON mode** — Llama 3.3 70B handles `response_format={"type": "json_object"}` reliably

The brief said *"prompt engineering matters far more than which provider you choose"*. I tested the same prompts on Claude (free trial) and Llama produced equally usable structured output for this task.

## Prompt Iteration Story

The repo's `prompts/` folder contains the actual three versions I worked through.

**v1 — `prompts/v1_naive.md` (failed)**

> "You are a financial advisor. Look at this portfolio and explain its risk."

What broke: no structure, output came back as markdown bullets sometimes, prose other times. The verdict word was inconsistent — "Risky", "High-Risk", "Aggressive". `json.loads()` couldn't be used. Worse, when I asked the LLM for runway numbers, it hallucinated values that looked plausible but didn't match Task 1's actual computation.

**v2 — `prompts/v2_persona.md` (better, still flawed)**

Added an Indian financial-advisor persona, asked for specific fields (summary, doing well, should change, verdict), kept output free-form. Format consistency improved but the LLM still occasionally invented numbers when the portfolio was complex.

**v3 — `prompts/v3_structured.md` (current)**

Three changes that fixed the remaining issues:
1. Pre-compute risk metrics in Python (Task 1's `compute_risk_metrics`) and pass them to the LLM as ground truth. The system prompt explicitly says "Do NOT invent figures."
2. Strict JSON schema with allowed enum values for `verdict` (Aggressive | Balanced | Conservative).
3. Tone is templated, not duplicated. One template, three tone profiles, swapped via a single dict lookup.

This is the v3 in production now and what gets called when you run the explainer.

## Run

```bash
cd task3
python explainer.py example_portfolio/balanced.json
python explainer.py example_portfolio/aggressive.json --tone beginner
python explainer.py example_portfolio/conservative.json --tone expert --no-critique
```

Flags:
- `--tone {beginner|experienced|expert}` — default `experienced`
- `--no-critique` — skips the critique + revision loop (saves API calls during iteration)

## Pipeline

```
portfolio.json
    │
    ▼
compute_risk_metrics()           ← Task 1 (deterministic math)
    │
    ▼
fetch_news_for_portfolio()       ← GDELT, top 5 headlines per asset
    │
    ▼
build_user_message(portfolio, risk, news)
    │
    ▼
Groq call #1: explain (Llama 3.3 70B)
    │
    ▼
Print raw JSON  ✓  (spec required)
    │
    ▼
Groq call #2: critique (different model = stricter audit)
    │
    ├── recommendation = "accept"  → done
    └── recommendation = "revise"  → reviser fixes  → critique again (max 2 revisions)
    │
    ▼
Print final JSON  ✓  + rich-formatted card view
```

## Bonus 1 — Configurable Tone

Three tone profiles in `prompt.py`:

| Tone | Audience | Style |
|---|---|---|
| `beginner` | Never invested before | Plain English, define jargon, analogies, encouraging |
| `experienced` | Few years' experience | Standard vocabulary, direct, pragmatic |
| `expert` | Finance professional | Volatility, correlation, tail risk, technical |

Same template, three style blocks injected. No prompt duplication.

## Bonus 2 — Critique + Revision Loop

`critique.py` calls a second LLM with an auditor system prompt and the same source data the original advisor had. Returns:

```json
{
  "accuracy_score": 1-10,
  "issues_found": ["..."],
  "verdict_agrees": true/false,
  "recommendation": "accept" | "revise" | "reject"
}
```

If recommendation is `revise` or `reject`, `reviser.py` is called with the original output, the critique's `issues_found`, and the source data. It produces a corrected explanation in the same JSON schema, which is then re-critiqued. The loop is capped at 2 revisions — beyond that, you risk the LLM oscillating between two flawed versions, and additional passes have diminishing returns.

Worst case: 1 explanation + 3 critiques + 2 revisions = 6 API calls per run. With Groq's free tier this is fine.

## News Context (Stretch)

`news_fetch.py` queries GDELT's free document API (`api.gdeltproject.org/api/v2/doc/doc`) for the top 5 most recent headlines per asset, last 7 days. No API key. Failed fetches return `[]` and never crash the explainer.

The LLM uses news only in the `news_insight` field — explicitly instructed not to let news bleed into the other fields, since it shouldn't override the deterministic risk math.

## Output: Raw JSON + Pretty Card

The spec requires both. I print the raw API response under `=== RAW API RESPONSE ===`, then the parsed structured output, then a rich-formatted card with:
- Color-coded verdict panel (red Aggressive, yellow Balanced, green Conservative)
- Section panels for Summary, Doing Well, Should Change, News Insight
- Auditor review panel (accuracy score, issues found, recommendation)
- Revision count tag if the loop ran

## What I Tried That Didn't Work

The v1 naive prompt let the LLM compute the math. It produced a perfectly fluent paragraph claiming the portfolio had "47 months of runway" when Task 1's calculator said 71.25. The fluency made the error worse — a CIO reading the output would have no reason to doubt it. The fix was to compute every number deterministically in Python, pass it into the prompt as ground truth, and explicitly tell the model not to invent figures. After this change, factual errors dropped to near zero (the critique pass now mostly catches minor things like rounding inconsistencies — see the example output where it flagged "71.25 months ≈ 5.6 years" when the correct conversion is ~5.94).

I also initially used a single critique pass with no revision. The critique would say "revise" and that information was wasted. Adding the reviser closed the loop — now when the auditor flags an issue, the system actually fixes it.
