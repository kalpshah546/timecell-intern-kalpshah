"""
assumption_generator.py
Single LLM call that does two jobs:
  1. Interprets the user's natural-language decision into structured allocation changes
  2. Generates the top N load-bearing assumptions, each with:
     - a confidence score (0-1)
     - a concrete stress_change that can be applied deterministically by the engine

Design principle: the LLM produces *instructions*, not numbers. The engine applies
those instructions and computes the math. This mirrors Timecell's philosophy:
math in code, narrative in LLM.
"""

import json
import os
from groq import Groq


SYSTEM_INSTRUCTION = """You are a senior risk analyst at a family office.
Your job is to perform a pre-mortem on a proposed portfolio decision.

You will be given:
- A current portfolio (allocations and expected crash percentages per asset)
- A proposed decision in natural language

Your output MUST be valid JSON with this EXACT shape:

{
  "decision_summary": "<one sentence restating the decision in concrete terms>",
  "decision_changes": [
    {"asset": "<asset name>", "new_allocation_pct": <number>},
    ...
  ],
  "assumptions": [
    {
      "assumption": "<one-sentence statement that must hold true for this decision to be sound>",
      "confidence": <float between 0 and 1, your confidence that this assumption holds>,
      "rationale": "<one sentence explaining why this assumption matters>",
      "stress_change": {
        "type": "<one of: crash_pct, multi_crash, expenses>",
        "asset": "<asset name, only for type=crash_pct>",
        "assets": ["<list of asset names>", "..."],
        "new_value": <number — new crash % or new monthly expense>,
        "new_values": {"<asset>": <number>, "...": <number>}
      }
    }
  ]
}

Stress change types:
- "crash_pct": worsen ONE asset's expected_crash_pct. Use "asset" and "new_value" (negative %).
- "multi_crash": worsen MULTIPLE assets' crash %s simultaneously (correlation shock).
                 Use "assets" and "new_values" dict.
- "expenses": increase monthly_expenses_inr. Use "new_value" (positive integer in INR).

Rules:
- decision_changes must list every asset whose allocation changes.
- All asset allocations after applying decision_changes must sum to 100.
- Each stress_change must use exactly the fields its type requires; omit the others.
- Generate the most LOAD-BEARING assumptions — the ones that would cause the
  biggest material harm if wrong. Not generic platitudes.
- Confidence reflects how likely the assumption is to hold in the real world,
  NOT how confident you are in your phrasing.

Return ONLY JSON. No markdown, no preamble."""


def generate_assumptions(
    client: Groq,
    portfolio: dict,
    decision: str,
    num_assumptions: int = 5,
    model: str = "llama-3.3-70b-versatile",
) -> dict:
    """Call the LLM to interpret the decision and generate stress assumptions."""
    user_msg = f"""CURRENT PORTFOLIO:
{json.dumps(portfolio, indent=2)}

PROPOSED DECISION:
{decision}

Generate exactly {num_assumptions} load-bearing assumptions. Return JSON only."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=2048,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)