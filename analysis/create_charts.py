"""Create the static figures used in the portfolio case study."""

from __future__ import annotations

import math
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS = ROOT / "chart_runtime"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from analyze_survey import read_rows, split_selections


CHART_DIR = ROOT / "docs" / "images"
INK = "#173B3A"
MUTED = "#647572"
GREEN = "#5F8D78"
GREEN_LIGHT = "#BFD1C5"
ORANGE = "#D95D39"
ORANGE_LIGHT = "#EDB39F"
GRID = "#DCE4DF"
PAPER = "#FBFAF5"


def setup() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 13,
            "axes.titlesize": 21,
            "axes.titleweight": "bold",
            "axes.labelcolor": MUTED,
            "axes.edgecolor": GRID,
            "xtick.color": MUTED,
            "ytick.color": INK,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
        }
    )
    CHART_DIR.mkdir(parents=True, exist_ok=True)


def finish(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


def chart_expectations(rows: list[dict[str, str]]) -> None:
    order = [
        "Not close to expectations",
        "Close, but below expectations",
        "Met expectations",
        "Exceeded expectations",
    ]
    counts = Counter(row["income_expectation"] for row in rows)
    values = [counts[label] for label in order]
    colors = [ORANGE, ORANGE_LIGHT, GREEN, GREEN_LIGHT]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    bars = ax.barh(order, values, color=colors, edgecolor=INK, linewidth=0.8)
    ax.set_title("Income relative to expectations", loc="left", color=INK, pad=32)
    ax.text(0, 1.035, "2022 self-reported survey; 51 usable responses", transform=ax.transAxes, color=MUTED)
    ax.set_xlabel("Respondents")
    ax.set_xlim(0, 25)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(value + 0.45, bar.get_y() + bar.get_height() / 2, f"{value}  ({value / len(rows):.1%})", va="center", color=INK, fontweight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(0.01, 0.01, "Source: original survey; percentages use the 51 nonblank responses.", color=MUTED, fontsize=10)
    fig.subplots_adjust(left=0.29, right=0.93, top=0.82, bottom=0.16)
    finish(fig, CHART_DIR / "income-expectations.png")


def chart_retention(rows: list[dict[str, str]]) -> None:
    counts = Counter(option for row in rows for option in split_selections(row["retention_priorities"]))
    ranked = counts.most_common()
    labels = [label for label, _ in reversed(ranked)]
    values = [value for _, value in reversed(ranked)]

    fig, ax = plt.subplots(figsize=(11, 7.1))
    bars = ax.barh(labels, values, color=GREEN, edgecolor=INK, linewidth=0.8)
    ax.set_title("Driver-selected retention priorities", loc="left", color=INK, pad=32)
    ax.text(0, 1.035, "Multiple selections allowed; 51 respondents", transform=ax.transAxes, color=MUTED)
    ax.set_xlabel("Respondents selecting each option")
    ax.set_xlim(0, 48)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(value + 0.6, bar.get_y() + bar.get_height() / 2, f"{value}  ({value / len(rows):.1%})", va="center", color=INK, fontweight="bold")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(0.01, 0.01, "Source: original survey. Percentages do not sum to 100% because respondents could choose several options.", color=MUTED, fontsize=10)
    fig.subplots_adjust(left=0.39, right=0.93, top=0.84, bottom=0.14)
    finish(fig, CHART_DIR / "retention-priorities.png")


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    proportion = successes / total
    denominator = 1 + z**2 / total
    center = (proportion + z**2 / (2 * total)) / denominator
    margin = z * math.sqrt((proportion * (1 - proportion) + z**2 / (4 * total)) / total) / denominator
    return center - margin, center + margin


def chart_tenure(rows: list[dict[str, str]]) -> None:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[row["driver_tenure"]].append(row)

    labels = [">5 years", "3-5 years", "1-3 years", "<1 year"]
    totals = [len(groups[label]) for label in labels]
    successes = [
        sum(row["income_expectation"] in {"Met expectations", "Exceeded expectations"} for row in groups[label])
        for label in labels
    ]
    proportions = [success / total for success, total in zip(successes, totals)]
    intervals = [wilson_interval(success, total) for success, total in zip(successes, totals)]
    errors = [
        [proportion - low for proportion, (low, _) in zip(proportions, intervals)],
        [high - proportion for proportion, (_, high) in zip(proportions, intervals)],
    ]

    fig, ax = plt.subplots(figsize=(11, 6.2))
    y = range(len(labels))
    ax.errorbar(proportions, y, xerr=errors, fmt="o", color=INK, ecolor=GREEN, elinewidth=4, capsize=7, markersize=10, markerfacecolor=ORANGE, markeredgecolor=INK)
    ax.set_yticks(list(y), [f"{label}  (n={total})" for label, total in zip(labels, totals)])
    ax.set_title("Income expectations by driver tenure", loc="left", color=INK, pad=32)
    ax.text(0, 1.035, "Share reporting income that met or exceeded expectations; 95% Wilson intervals", transform=ax.transAxes, color=MUTED)
    ax.set_xlabel("Share of respondents")
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for yi, proportion in zip(y, proportions):
        ax.text(
            proportion + 0.015,
            yi,
            f"{proportion:.1%}",
            va="center",
            color=INK,
            fontweight="bold",
            bbox={"facecolor": PAPER, "edgecolor": "none", "pad": 1.5},
        )
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(0.01, 0.01, "Source: original survey. Wide overlapping intervals reflect the small tenure groups; this chart does not establish a tenure effect.", color=MUTED, fontsize=10)
    fig.subplots_adjust(left=0.24, right=0.95, top=0.82, bottom=0.16)
    finish(fig, CHART_DIR / "expectations-by-tenure.png")


def main() -> None:
    setup()
    rows = read_rows()
    chart_expectations(rows)
    chart_retention(rows)
    chart_tenure(rows)
    print(f"Wrote three charts to {CHART_DIR}")


if __name__ == "__main__":
    main()

