"""
reporter.py
Pretty-prints the pre-mortem analysis as a readable CLI report.
Uses rich panels and colored severity tags.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


CONSOLE = Console()

SEVERITY_COLORS = {
    "CRITICAL": "bold red",
    "HIGH": "red",
    "MEDIUM": "yellow",
    "LOW": "green",
}


def _confidence_color(confidence: float) -> str:
    """Lower confidence = more concerning = warmer color."""
    if confidence < 0.5:
        return "red"
    if confidence < 0.7:
        return "yellow"
    return "green"


def print_header(decision_summary: str) -> None:
    """Print the top banner."""
    CONSOLE.print()
    CONSOLE.print(Panel(
        Text(decision_summary, style="bold white"),
        title="[bold cyan]WHAT BREAKS THIS?[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))


def print_assumption(
    index: int,
    assumption: dict,
    comparison: dict,
    severity: str,
) -> None:
    """Print one assumption block with its stress impact."""
    sev_color = SEVERITY_COLORS.get(severity, "white")
    conf_color = _confidence_color(assumption["confidence"])
    confidence_pct = int(assumption["confidence"] * 100)

    # Header line
    header = Text()
    header.append(f"\n{index}. ", style="bold")
    header.append(assumption["assumption"], style="bold white")

    # Body
    body = Text()
    body.append(f"   Confidence: ", style="dim")
    body.append(f"{confidence_pct}%", style=f"bold {conf_color}")
    body.append(f"   |   Severity if wrong: ", style="dim")
    body.append(severity, style=f"bold {sev_color}")
    body.append("\n\n")

    body.append(f"   Why it matters: ", style="dim")
    body.append(f"{assumption.get('rationale', 'n/a')}\n\n")

    body.append(f"   IF WRONG:\n", style="bold yellow")

    # Stress description
    sc = assumption["stress_change"]
    if sc["type"] == "crash_pct":
        body.append(
            f"     → {sc['asset']} crash worsens to {sc['new_value']}%\n",
            style="white",
        )
    elif sc["type"] == "multi_crash":
        for asset, val in sc.get("new_values", {}).items():
            body.append(f"     → {asset} crash worsens to {val}%\n", style="white")
    elif sc["type"] == "expenses":
        body.append(
            f"     → Monthly expenses rise to ₹{sc['new_value']:,}\n",
            style="white",
        )

    # Numerical deltas
    body.append(
        f"     → Runway: {comparison['runway_baseline']:.1f} → "
        f"{comparison['runway_stressed']:.1f} months "
        f"({comparison['runway_delta']:+.1f})\n",
        style="white",
    )
    body.append(
        f"     → Post-crash value: ₹{comparison['post_crash_baseline']:,.0f} → "
        f"₹{comparison['post_crash_stressed']:,.0f} "
        f"({comparison['post_crash_delta']:+,.0f})\n",
        style="white",
    )

    if comparison["ruin_test_changed"]:
        body.append(
            f"     → Ruin test: {comparison['ruin_test_baseline']} → "
            f"{comparison['ruin_test_stressed']}  ⚠\n",
            style="bold red",
        )
    else:
        body.append(
            f"     → Ruin test: {comparison['ruin_test_stressed']} (unchanged)\n",
            style="dim",
        )

    CONSOLE.print(header)
    CONSOLE.print(body)


def print_summary(rows: list) -> None:
    """Print the final summary table."""
    table = Table(
        title="\nSummary",
        title_style="bold cyan",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", justify="right")
    table.add_column("Assumption", overflow="fold", max_width=50)
    table.add_column("Confidence", justify="center")
    table.add_column("Severity", justify="center")
    table.add_column("Runway Δ", justify="right")

    for i, row in enumerate(rows, start=1):
        sev_color = SEVERITY_COLORS.get(row["severity"], "white")
        conf_color = _confidence_color(row["confidence"])

        table.add_row(
            str(i),
            row["assumption"][:80],
            Text(f"{int(row['confidence']*100)}%", style=conf_color),
            Text(row["severity"], style=sev_color),
            f"{row['runway_delta']:+.1f}",
        )

    CONSOLE.print(table)
    CONSOLE.print()