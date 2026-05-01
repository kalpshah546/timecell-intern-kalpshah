"""
formatter.py
Pretty-prints the explainer output using rich panels.
Keeps the raw JSON dump (spec requirement) but adds a human-friendly card view.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


CONSOLE = Console()

VERDICT_COLORS = {
    "Aggressive": "red",
    "Balanced": "yellow",
    "Conservative": "green",
}


def _verdict_panel(verdict: str, revision_count: int = 0) -> Panel:
    color = VERDICT_COLORS.get(verdict, "white")
    label = Text(verdict.upper(), style=f"bold {color}")
    if revision_count > 0:
        label.append(f"  [Revised {revision_count} time(s)]", style="dim italic")
    return Panel(label, title="Verdict", border_style=color, padding=(0, 2))


def _section_panel(title: str, body: str, border: str = "cyan") -> Panel:
    return Panel(
        Text(body or "—", style="white"),
        title=title,
        border_style=border,
        padding=(0, 2),
    )


def _critique_panel(critique: dict) -> Panel:
    score = critique.get("accuracy_score", 0)
    if score >= 8:
        score_color = "green"
    elif score >= 5:
        score_color = "yellow"
    else:
        score_color = "red"

    rec = critique.get("recommendation", "—")
    agrees = "✓" if critique.get("verdict_agrees") else "✗"
    issues = critique.get("issues_found", [])

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Accuracy", Text(f"{score}/10", style=f"bold {score_color}"))
    table.add_row("Verdict agrees", agrees)
    table.add_row("Recommendation", rec)

    if issues:
        issues_text = "\n".join(f"• {i}" for i in issues)
    else:
        issues_text = "None"
    table.add_row("Issues found", issues_text)

    return Panel(table, title="Auditor Review", border_style="bright_black", padding=(0, 1))


def print_explanation_card(
    explanation: dict,
    critique: dict | None = None,
    revision_count: int = 0,
) -> None:
    """Render the explainer output as a clean rich card."""
    verdict = explanation.get("verdict", "Unknown")

    CONSOLE.print()
    CONSOLE.print(_verdict_panel(verdict, revision_count))
    CONSOLE.print(_section_panel("Summary", explanation.get("summary", "")))
    CONSOLE.print(_section_panel(
        "What You're Doing Well",
        explanation.get("doing_well", ""),
        border="green",
    ))
    CONSOLE.print(_section_panel(
        "What to Change",
        explanation.get("should_change", ""),
        border="yellow",
    ))

    news_insight = explanation.get("news_insight")
    if news_insight:
        CONSOLE.print(_section_panel(
            "News Insight",
            news_insight,
            border="magenta",
        ))

    if critique:
        CONSOLE.print(_critique_panel(critique))