"""Build a 2026 Monday manifest from the official MLB schedule feed."""

from __future__ import annotations

import csv
import datetime as dt
import json
import urllib.parse
import urllib.request
from pathlib import Path


TEAM_ID = 112  # Chicago Cubs
START_DATE = dt.date(2026, 4, 6)
END_DATE = dt.date(2026, 9, 21)
SCHEDULE_API = "https://statsapi.mlb.com/api/v1/schedule"
OUTPUT = Path("config/chicago_monday_panel_dates.csv")


def mondays(start: dt.date, end: dt.date) -> list[dt.date]:
    date = start + dt.timedelta(days=(7 - start.weekday()) % 7)
    values = []
    while date <= end:
        values.append(date)
        date += dt.timedelta(days=7)
    return values


def fetch_schedule() -> dict:
    query = urllib.parse.urlencode(
        {
            "sportId": 1,
            "teamId": TEAM_ID,
            "startDate": START_DATE.isoformat(),
            "endDate": END_DATE.isoformat(),
            "hydrate": "venue",
        }
    )
    request = urllib.request.Request(
        f"{SCHEDULE_API}?{query}",
        headers={"User-Agent": "uber-driver-market-study/1.0"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.load(response)


def games_by_date(schedule: dict) -> dict[str, list[dict]]:
    return {item["date"]: item.get("games", []) for item in schedule.get("dates", [])}


def classify(date: dt.date, games: list[dict]) -> dict[str, str]:
    home_games = [
        game
        for game in games
        if game.get("teams", {}).get("home", {}).get("team", {}).get("id") == TEAM_ID
    ]
    if home_games:
        game = home_games[0]
        opponent = game["teams"]["away"]["team"]["name"]
        start = game.get("gameDate", "")
        return {
            "group": "event",
            "note": f"Cubs home game vs {opponent}; UTC start {start}",
            "cubs_home_game": "1",
            "opponent": opponent,
            "game_start_utc": start,
        }
    game_note = "Cubs away or not scheduled"
    if games:
        opponent = games[0]["teams"]["home"]["team"]["name"]
        game_note = f"Cubs away at {opponent}"
    return {
        "group": "control",
        "note": f"{game_note}; requires weather and competing-event screen",
        "cubs_home_game": "0",
        "opponent": "",
        "game_start_utc": "",
    }


def main() -> None:
    schedule = fetch_schedule()
    indexed = games_by_date(schedule)
    rows = []
    for date in mondays(START_DATE, END_DATE):
        row = classify(date, indexed.get(date.isoformat(), []))
        rows.append(
            {
                "date": date.isoformat(),
                **row,
                "weather_status": "pending",
                "competing_event_status": "pending",
                "schedule_source": f"https://www.mlb.com/schedule/{date.isoformat()}",
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    event_count = sum(row["group"] == "event" for row in rows)
    print(
        f"Saved {len(rows)} Mondays ({event_count} home-game dates) to {OUTPUT}.",
        flush=True,
    )


if __name__ == "__main__":
    main()
