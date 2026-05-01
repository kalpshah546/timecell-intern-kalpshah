"""
AI-Powered Portfolio Explainer
Composes Task 1 (risk math) + GDELT (news) + Groq (Llama 3.3 70B) into an
explanation pipeline with self-critique and self-revision.

Architectural decision: math runs in Python, narrative runs in the LLM.
LLMs hallucinate numbers; deterministic code does not.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Reuse Task 1's risk calculator
sys.path.append(str(Path(__file__).parent.parent))
from task1.portfolio_risk_calculator import compute_risk_metrics

from prompt import build_system_instruction, build_user_message
from critique import critique_explanation
from reviser import revise_explanation
from news_fetch import fetch_news_for_portfolio
from formatter import print_explanation_card


load_dotenv()
MODEL1 = "llama-3.3-70b-versatile"   # explanation + revision
MODEL2 = "openai/gpt-oss-120b"       # critique (different model = stricter audit)

MAX_REVISIONS = 2
REVISION_TRIGGERS = {"revise", "reject"}


def _call_explainer(
    client: Groq,
    system_instruction: str,
    user_message: str,
) -> tuple[str, dict]:
    """Single LLM call for the explanation. Returns (raw_text, parsed_dict)."""
    response = client.chat.completions.create(
        model=MODEL1,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=1024,
    )
    raw_text = response.choices[0].message.content
    parsed = json.loads(raw_text)
    return raw_text, parsed


def explain_portfolio(
    portfolio: dict,
    tone: str = "experienced",
    run_critique: bool = True,
) -> dict:
    """End-to-end pipeline: math → news → LLM → critique → optional revision loop."""

    # 1. Initialize Groq client
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    # 2. Compute risk metrics deterministically (NOT via LLM)
    print("→ Computing risk metrics...")
    risk = compute_risk_metrics(portfolio)

    # 3. Fetch news context (degrades gracefully on failure)
    print("→ Fetching recent news...")
    news = fetch_news_for_portfolio(portfolio)

    # 4. Build prompts
    system_instruction = build_system_instruction(tone=tone)
    user_message = build_user_message(portfolio, risk, news)

    source_data = {"portfolio": portfolio, "risk": risk, "news": news}

    # 5. Initial explanation call
    print(f"→ Calling Groq (model={MODEL1}, tone={tone})...")
    try:
        raw_text, explanation = _call_explainer(client, system_instruction, user_message)
    except json.JSONDecodeError as e:
        print(f"[error] JSON parse failed on initial call: {e}")
        return {"error": "parse_failure"}

    # 6. Print raw response (required by spec)
    print("\n=== RAW API RESPONSE ===")
    print(raw_text)

    # Validate verdict
    valid_verdicts = {"Aggressive", "Balanced", "Conservative"}
    if explanation.get("verdict") not in valid_verdicts:
        print(f"[warn] Invalid verdict: {explanation.get('verdict')}")

    revision_history = []
    final_critique = None

    # 7. Critique + revision loop
    if run_critique:
        current_explanation = explanation
        attempts = 0

        while True:
            print(f"\n→ Running critique pass (attempt {attempts + 1})...")
            try:
                critique = critique_explanation(
                    client=client,
                    explanation=current_explanation,
                    source_data=source_data,
                    model=MODEL2,
                )
            except Exception as exc:
                print(f"[warn] Critique failed: {exc}")
                final_critique = None
                break

            print("\n=== CRITIQUE ===")
            print(json.dumps(critique, indent=2))

            recommendation = critique.get("recommendation", "accept")
            final_critique = critique

            if recommendation not in REVISION_TRIGGERS or attempts >= MAX_REVISIONS:
                if attempts >= MAX_REVISIONS and recommendation in REVISION_TRIGGERS:
                    print(f"\n[info] Max revisions ({MAX_REVISIONS}) reached. "
                          f"Accepting current version.")
                break

            print(f"\n→ Critique flagged issues. Running revision pass {attempts + 1}/"
                  f"{MAX_REVISIONS}...")
            try:
                revised = revise_explanation(
                    client=client,
                    original_explanation=current_explanation,
                    critique=critique,
                    source_data=source_data,
                    model=MODEL1,
                )
                revision_history.append({
                    "attempt": attempts + 1,
                    "previous": current_explanation,
                    "critique": critique,
                    "revised": revised,
                })
                current_explanation = revised
                attempts += 1
            except Exception as exc:
                print(f"[warn] Revision failed: {exc}. Keeping previous version.")
                break

        explanation = current_explanation

    # 8. Final structured output
    # print("\n=== FINAL STRUCTURED OUTPUT ===")
    # print(json.dumps(explanation, indent=2))

    # 9. Pretty card view
    print_explanation_card(
        explanation=explanation,
        critique=final_critique,
        revision_count=len(revision_history),
    )

    return {
        "tone": tone,
        "model": MODEL1,
        "explanation": explanation,
        "critique": final_critique,
        "revision_history": revision_history,
        "risk_metrics": risk,
        "news": news,
    }


def main():
    parser = argparse.ArgumentParser(description="AI Portfolio Explainer")
    parser.add_argument("portfolio_file", help="Path to portfolio JSON file")
    parser.add_argument(
        "--tone",
        choices=["beginner", "experienced", "expert"],
        default="experienced",
        help="Audience tone for the explanation",
    )
    parser.add_argument(
        "--no-critique",
        action="store_true",
        help="Skip the critique + revision loop (saves API calls)",
    )
    args = parser.parse_args()

    with open(args.portfolio_file) as f:
        portfolio = json.load(f)

    explain_portfolio(
        portfolio=portfolio,
        tone=args.tone,
        run_critique=not args.no_critique,
    )


if __name__ == "__main__":
    main()