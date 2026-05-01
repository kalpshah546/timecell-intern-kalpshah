"""
Builds prompts for the LLM.
Kept separate from API calls so prompts can be iterated without touching network code.
"""

import json


SYSTEM_INSTRUCTION = """You are a friendly but honest Indian financial advisor.
Your audience is a {tone_audience}.

Communication style:
{tone_style}

You are given the client's portfolio AND pre-computed risk metrics
(post-crash value, runway in months, ruin test, largest risk asset, concentration warning).
Both severe and moderate crash scenarios are provided.

Your task: explain the portfolio's risk in plain English. Return ONLY valid JSON
with these EXACT keys (no markdown fences, no preamble, no trailing text):

{{
  "summary": "<3-4 sentence plain-English summary of the portfolio's risk level>",
  "doing_well": "<one specific thing the investor is doing well, citing actual numbers from the data>",
  "should_change": "<one specific thing to change AND the reason why, citing actual numbers>",
  "verdict": "<exactly one of: Aggressive, Balanced, Conservative>"
}}

Strict rules:
- Cite real numbers from the data (allocations, runway months, post-crash value).
- Do NOT invent figures. If something is not in the data, do not mention it.
- Keep total response under 250 words.
- The "verdict" field must be exactly one of the three allowed values.
"""


TONE_PROFILES = {
    "beginner": {
        "audience": "complete beginner who has never invested before",
        "style": (
            "- Use simple, everyday English\n"
            "- Avoid jargon; if you must use a term, define it in parentheses\n"
            "- Use relatable analogies (e.g., 'like keeping all your eggs in one basket')\n"
            "- Be warm and encouraging, not alarming"
        ),
    },
    "experienced": {
        "audience": "investor with a few years of experience",
        "style": (
            "- Use standard financial vocabulary (allocation, drawdown, runway)\n"
            "- Be direct and pragmatic\n"
            "- Skip basic definitions"
        ),
    },
    "expert": {
        "audience": "sophisticated investor or finance professional",
        "style": (
            "- Use precise financial terminology\n"
            "- Reference concepts like volatility, correlation, tail risk\n"
            "- Be technical and quantitative"
        ),
    },
}


def build_system_instruction(tone: str = "experienced") -> str:
    """Pick the right tone profile and inject into the system template."""
    profile = TONE_PROFILES.get(tone, TONE_PROFILES["experienced"])
    return SYSTEM_INSTRUCTION.format(
        tone_audience=profile["audience"],
        tone_style=profile["style"],
    )


def build_user_message(portfolio: dict, risk_metrics: dict) -> str:
    """Bundle portfolio + computed metrics into a clean user message."""
    return f"""Here is the client's portfolio and risk analysis:

PORTFOLIO:
{json.dumps(portfolio, indent=2)}

RISK METRICS (severe = full expected crash, moderate = half crash):
{json.dumps(risk_metrics, indent=2)}

Now produce the JSON explanation as instructed."""