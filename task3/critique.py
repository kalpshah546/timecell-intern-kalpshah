"""
Bonus: second-pass critique.
Asks the LLM to audit its own first response for accuracy.
Catches hallucinations and unsupported claims.
"""

import json
from groq import Groq


CRITIQUE_INSTRUCTION = """You are a senior financial auditor reviewing another advisor's
analysis of a portfolio. You have the same source data they had.

Your job: identify inaccuracies, hallucinated numbers, or unsupported claims.
Be strict but fair. If everything checks out, say so.

Return ONLY valid JSON with these exact keys:
{
  "accuracy_score": <integer 1-10>,
  "issues_found": [<list of specific issues; empty list [] if none>],
  "verdict_agrees": <true or false>,
  "recommendation": "<one of: accept, revise, reject>"
}

No markdown fences, no preamble.
"""


def critique_explanation(
    client: Groq,
    explanation: dict,
    source_data: dict,
    model: str,
) -> dict:
    """Run a second LLM call to audit the first explanation."""
    user_msg = f"""ORIGINAL ANALYSIS:
{json.dumps(explanation, indent=2)}

SOURCE DATA THE ADVISOR WAS GIVEN:
{json.dumps(source_data, indent=2, default=str)}

Audit the analysis. Return JSON only."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CRITIQUE_INSTRUCTION},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,  # lower = more consistent audits
    )

    raw = response.choices[0].message.content
    return json.loads(raw)