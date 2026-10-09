"""Create the cross-city extension figures used in the portfolio report."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS = ROOT / "chart_runtime"
if LOCAL_DEPS.exists():
    sys.path.insert(0, str(LOCAL_DEPS))

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.ticker import PercentFormatter


IMAGE_DIR = ROOT / "docs" / "images"
CHICAGO = ROOT / "data" / "derived" / "chicago_spatial_event_phases.csv"
NYC = ROOT / "data" / "derived" / "nyc_yankee_driver_cycle_estimates.csv"
NYC_STRATEGY = ROOT / "data" / "derived" / "nyc_surge_spillover_estimates.csv"
INK = "#173B3A"
MUTED = "#647572"
GREEN = "#5F8D78"
GREEN_LIGHT = "#BFD1C5"
ORANGE = "#D95D39"
YELLOW = "#E9B949"
GRID = "#DCE4DF"
PAPER = "#FBFAF5"
WHITE = "#FFFFFF"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def setup() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 12,
            "axes.titlesize": 20,
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
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def finish(fig: plt.Figure, filename: str) -> None:
    fig.savefig(IMAGE_DIR / filename, dpi=180, bbox_inches="tight", pad_inches=0.3)
    plt.close(fig)


def chicago_event_demand() -> None:
    rows = read_rows(CHICAGO)
    phases = ["pregame_2h", "game_first_2h", "game_late_post_2h", "extended_postgame"]
    phase_labels = ["Pregame", "First 2 hours", "Late / postgame", "Extended postgame"]
    zones = ["core", "inner_ring", "outer_ring"]
    zone_labels = ["Lake View core", "Inner ring", "Outer ring"]
    colors = [ORANGE, GREEN, GREEN_LIGHT]
    lookup = {(row["zone"], row["phase"]): float(row["clock_matched_pickup_uplift"]) for row in rows}

    x = np.arange(len(phases))
    width = 0.23
    fig, ax = plt.subplots(figsize=(12, 6.8))
    for index, (zone, label, color) in enumerate(zip(zones, zone_labels, colors)):
        values = [lookup[(zone, phase)] for phase in phases]
        bars = ax.bar(
            x + (index - 1) * width,
            values,
            width,
            label=label,
            color=color,
            edgecolor=INK,
            linewidth=0.7,
        )
        for bar, value in zip(bars, values):
            offset = 0.035 if value >= 0 else -0.065
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + offset,
                f"{value:.1%}",
                ha="center",
                va="bottom" if value >= 0 else "top",
                color=INK,
                fontsize=10,
                fontweight="bold",
            )
    ax.axhline(0, color=INK, linewidth=1)
    ax.set_xticks(x, phase_labels)
    ax.set_ylim(-0.2, 1.65)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylabel("Pickup change versus clock-matched controls")
    ax.set_title("Chicago event demand concentrated in the venue core", loc="left", color=INK, pad=30)
    ax.text(
        0,
        1.03,
        "Median clean-weather event-date change; eight Cubs home-game Mondays in 2026",
        transform=ax.transAxes,
        color=MUTED,
    )
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=3, loc="upper left")
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Source: City of Chicago TNP trips. Pickup counts are normalized per community area; comparison is descriptive, not causal.",
        color=MUTED,
        fontsize=9.5,
    )
    fig.subplots_adjust(top=0.81, bottom=0.17)
    finish(fig, "chicago-event-demand-by-zone.png")


def nyc_complete_clock() -> None:
    rows = read_rows(NYC)
    phases = ["pregame_2h", "game_first_2h", "game_late_post_2h"]
    phase_labels = ["Pregame", "First 2 hours", "Late / postgame"]
    zones = ["core", "one_mile_ring"]
    zone_labels = ["Stadium core", "One-mile ring"]
    lookup = {(row["zone_group"], row["phase"]): row for row in rows}

    labels = []
    occupied = []
    full_cycle = []
    for zone, zone_label in zip(zones, zone_labels):
        for phase, phase_label in zip(phases, phase_labels):
            row = lookup[(zone, phase)]
            labels.append(f"{zone_label} | {phase_label}")
            occupied.append(float(row["median_occupied_pay_rate_change"]))
            full_cycle.append(float(row["median_cycle_pay_rate_change"]))

    y = np.arange(len(labels))
    height = 0.34
    fig, ax = plt.subplots(figsize=(12, 7.2))
    occupied_bars = ax.barh(
        y - height / 2,
        occupied,
        height,
        label="Passenger-onboard clock",
        color=GREEN_LIGHT,
        edgecolor=INK,
        linewidth=0.7,
    )
    cycle_bars = ax.barh(
        y + height / 2,
        full_cycle,
        height,
        label="Request-to-drop-off clock",
        color=ORANGE,
        edgecolor=INK,
        linewidth=0.7,
    )
    ax.axvline(0, color=INK, linewidth=1)
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlim(-0.06, 0.29)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Event change versus weekday-matched controls")
    ax.set_title("The complete driver clock can change the answer", loc="left", color=INK, pad=48)
    ax.text(
        0,
        1.075,
        "Median change across three Yankee Stadium event/control pairs, April 2025",
        transform=ax.transAxes,
        color=MUTED,
    )
    for bars, values in ((occupied_bars, occupied), (cycle_bars, full_cycle)):
        for bar, value in zip(bars, values):
            ax.text(
                value + (0.006 if value >= 0 else -0.006),
                bar.get_y() + bar.get_height() / 2,
                f"{value:+.1%}",
                va="center",
                ha="left" if value >= 0 else "right",
                color=INK,
                fontsize=10,
                fontweight="bold",
            )
    ax.annotate(
        "Direction reverses",
        xy=(-0.0158, 5 + height / 2),
        xytext=(0.075, 5.35),
        arrowprops={"arrowstyle": "->", "color": INK, "linewidth": 1.2},
        color=INK,
        fontweight="bold",
    )
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.legend(
        frameon=False,
        ncol=2,
        loc="lower left",
        bbox_to_anchor=(0, 1.005),
        borderaxespad=0,
    )
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Source: NYC TLC HVFHV trips. Driver pay excludes expenses and completed trip cycles exclude idle time before a request.",
        color=MUTED,
        fontsize=9.5,
    )
    fig.subplots_adjust(left=0.25, top=0.73, bottom=0.15)
    finish(fig, "nyc-complete-driver-clock.png")


def measurement_coverage() -> None:
    rows = ["2022 survey", "Chicago TNP trips", "Chicago Traffic Tracker", "NYC TLC HVFHV"]
    columns = ["Online idle", "Request to arrival", "Arrival to pickup", "Passenger trip", "Driver pay"]
    values = np.array(
        [
            [0.5, 0.0, 0.0, 0.5, 0.5],
            [0.0, 0.0, 0.0, 1.0, 0.0],
            [0.0, 0.5, 0.0, 0.5, 0.0],
            [0.0, 1.0, 1.0, 1.0, 1.0],
        ]
    )
    cell_labels = [
        ["Self-report", "Not available", "Not available", "Self-report", "Self-report"],
        ["Not available", "Not available", "Not available", "Observed", "Not available"],
        ["Not available", "Proxy", "Not available", "Proxy", "Not available"],
        ["Not available", "Observed", "Observed", "Observed", "Observed"],
    ]
    cmap = ListedColormap(["#EDF0ED", YELLOW, GREEN])
    fig, ax = plt.subplots(figsize=(12, 5.7))
    ax.imshow(values, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(np.arange(len(columns)), columns)
    ax.set_yticks(np.arange(len(rows)), rows)
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False, length=0, pad=10)
    for row_index in range(len(rows)):
        for column_index in range(len(columns)):
            value = values[row_index, column_index]
            label = cell_labels[row_index][column_index]
            ax.text(
                column_index,
                row_index,
                label,
                ha="center",
                va="center",
                color=WHITE if value == 1 else INK,
                fontsize=9.5,
                fontweight="bold" if value else "normal",
            )
    ax.set_title("No single source observes the entire driver work cycle", loc="left", color=INK, pad=48)
    ax.text(
        0,
        1.13,
        "Measurement coverage used in the portfolio extension",
        transform=ax.transAxes,
        color=MUTED,
    )
    ax.set_xticks(np.arange(-0.5, len(columns), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(rows), 1), minor=True)
    ax.grid(which="minor", color=PAPER, linewidth=4)
    ax.tick_params(which="minor", bottom=False, left=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(
        0.01,
        0.01,
        "Observed means directly represented in the source. Proxy/self-report means informative but not equivalent to timestamped operational measurement.",
        color=MUTED,
        fontsize=9.5,
    )
    fig.subplots_adjust(left=0.18, right=0.98, top=0.69, bottom=0.15)
    finish(fig, "cross-city-measurement-coverage.png")


def nyc_spillover_strategy() -> None:
    rows = read_rows(NYC_STRATEGY)
    order = ["stadium_bound", "spillover_local", "spillover_away", "core_departure"]
    labels = ["Stadium-bound", "Spillover local", "Spillover away", "Core departure"]
    lookup = {row["strategy"]: row for row in rows}
    fare = [float(lookup[key]["implied_event_passenger_fare_premium"]) for key in order]
    pay = [float(lookup[key]["implied_event_pay_premium"]) for key in order]
    volume = [float(lookup[key]["trip_volume_change"]) for key in order]
    cycle = [float(lookup[key]["cycle_time_change"]) for key in order]
    x = np.arange(len(order))
    width = 0.34

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.6), sharex=True)
    panels = (
        (axes[0], fare, pay, "Adjusted price and pay", "Passenger base fare", "Reported driver pay"),
        (axes[1], volume, cycle, "Demand and cycle time", "Trip volume", "Complete-cycle time"),
    )
    for ax, first, second, title, first_label, second_label in panels:
        first_bars = ax.bar(
            x - width / 2,
            first,
            width,
            label=first_label,
            color=GREEN_LIGHT,
            edgecolor=INK,
            linewidth=0.7,
        )
        second_bars = ax.bar(
            x + width / 2,
            second,
            width,
            label=second_label,
            color=ORANGE,
            edgecolor=INK,
            linewidth=0.7,
        )
        ax.axhline(0, color=INK, linewidth=1)
        ax.set_title(title, loc="left", color=INK, fontsize=15, pad=16)
        ax.set_xticks(x, labels, rotation=20, ha="right")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.legend(frameon=False, loc="upper right")
        for bars, values in ((first_bars, first), (second_bars, second)):
            for bar, value in zip(bars, values):
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    value + (0.012 if value >= 0 else -0.012),
                    f"{value:+.1%}",
                    ha="center",
                    va="bottom" if value >= 0 else "top",
                    color=INK,
                    fontsize=9.5,
                    fontweight="bold",
                )
    axes[0].set_ylim(-0.09, 0.08)
    axes[1].set_ylim(-0.14, 0.52)
    fig.suptitle(
        "NYC did not reproduce a Nashville-style pregame premium",
        x=0.07,
        ha="left",
        color=INK,
        fontsize=20,
        fontweight="bold",
    )
    fig.text(
        0.07,
        0.88,
        "Three Yankee Stadium event evenings versus nine same-weekday controls, April 2025",
        color=MUTED,
        fontsize=12,
    )
    fig.text(
        0.01,
        0.01,
        "Source: NYC TLC HVFHV. Premiums are model-implied, not platform-reported surge; capacity excludes idle and repositioning.",
        color=MUTED,
        fontsize=9.5,
    )
    fig.subplots_adjust(top=0.78, bottom=0.22, wspace=0.2)
    finish(fig, "nyc-surge-spillover-strategy.png")


def main() -> None:
    setup()
    chicago_event_demand()
    nyc_complete_clock()
    measurement_coverage()
    nyc_spillover_strategy()
    print(f"Wrote four extension charts to {IMAGE_DIR}.")


if __name__ == "__main__":
    main()
