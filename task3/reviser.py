"""
reviser.py
Second-chance pass: when the critique flags issues, ask the LLM to fix them.
Takes original explanation + critique + source data, returns a corrected explanation
in the same JSON schema as the original.
"""

import json
from groq import Groq


REVISION_INSTRUCTION = """You are the same friendly Indian financial advisor as before.
A senior auditor reviewed your previous analysis and flagged specific issues.

Your job: produce a CORRECTED version of your analysis that fixes every issue raised,
while keeping anything that was correct intact.

Return ONLY valid JSON with these EXACT keys (no markdown, no preamble):

{
  "summary": "<3-4 sentence plain-English summary of risk level>",
  "doing_well": "<one specific thing the investor is doing well, citing real numbers>",
  "should_change": "<one specific thing to change AND why, citing real numbers>",
  "verdict": "<exactly one of: Aggressive, Balanced, Conservative>",
  "news_insight": "<one sentence on how recent news might affect this portfolio>"
}

Strict rules:
- Address every issue in the auditor's "issues_found" list.
- Cite ONLY real numbers from the source data. Do NOT invent figures.
- Keep total response under 250 words.
"""


def revise_explanation(
    client: Groq,
    original_explanation: dict,
    critique: dict,
    source_data: dict,
    model: str,
) -> dict:
    """Run a corrective LLM call. Returns a new explanation dict."""
    user_msg = f"""YOUR PREVIOUS ANALYSIS:
{json.dumps(original_explanation, indent=2)}

ISSUES THE AUDITOR FOUND:
{json.dumps(critique.get("issues_found", []), indent=2)}

AUDITOR'S RECOMMENDATION: {critique.get("recommendation", "revise")}

SOURCE DATA YOU WERE GIVEN:
{json.dumps(source_data, indent=2, default=str)}

Produce a corrected JSON analysis that addresses every issue raised."""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": REVISION_INSTRUCTION},
            {"role": "user", "content": user_msg},
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=1024,
    )

    raw = response.choices[0].message.content
    return json.loads(raw)