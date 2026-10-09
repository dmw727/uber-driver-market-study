"""Validate a Chicago TNP trip dataset before analytical extraction."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


API_ROOT = "https://data.cityofchicago.org"


def fetch_json(url: str, timeout: int = 90) -> Any:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "uber-driver-market-study/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Chicago API returned HTTP {error.code}: {detail}") from error


def attempt(label: str, url: str, timeout: int = 90) -> tuple[Any | None, str | None]:
    try:
        return fetch_json(url, timeout=timeout), None
    except (RuntimeError, TimeoutError, urllib.error.URLError) as error:
        return None, f"{label}: {error}"


def query_url(dataset_id: str, **parameters: str) -> str:
    encoded = urllib.parse.urlencode(parameters)
    return f"{API_ROOT}/resource/{dataset_id}.json?{encoded}"


def validate(dataset_id: str, include_global_count: bool = False) -> dict[str, Any]:
    metadata = fetch_json(f"{API_ROOT}/api/views/{dataset_id}")
    fields = [column["fieldName"] for column in metadata.get("columns", [])]

    required = {
        "trip_id",
        "trip_start_timestamp",
        "trip_seconds",
        "trip_miles",
        "pickup_community_area",
        "dropoff_community_area",
        "fare",
        "tip",
    }
    missing_required = sorted(required.difference(fields))

    # Separate aggregates are used because Socrata rejects some mixed aggregate
    # expressions even when each expression is valid on its own.
    warnings: list[str] = []
    row_count = None
    if include_global_count:
        row_count, error = attempt(
            "unrestricted row count",
            query_url(dataset_id, **{"$select": "count(*) as row_count"}),
            timeout=20,
        )
        if error:
            warnings.append(error)

    earliest, error = attempt(
        "earliest timestamp",
        query_url(
            dataset_id,
            **{
                "$select": "trip_start_timestamp",
                "$order": "trip_start_timestamp asc",
                "$limit": "1",
            },
        ),
        timeout=30,
    )
    if error:
        warnings.append(error)

    latest, error = attempt(
        "latest timestamp",
        query_url(
            dataset_id,
            **{
                "$select": "trip_start_timestamp",
                "$order": "trip_start_timestamp desc",
                "$limit": "1",
            },
        ),
        timeout=30,
    )
    if error:
        warnings.append(error)
    sample = fetch_json(query_url(dataset_id, **{"$limit": "5"}))

    return {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_id": dataset_id,
        "dataset_name": metadata.get("name"),
        "rows_updated_at_unix": metadata.get("rowsUpdatedAt"),
        "schema": fields,
        "missing_required_fields": missing_required,
        "row_count": int(row_count[0]["row_count"]) if row_count else None,
        "earliest_trip_start": earliest[0].get("trip_start_timestamp") if earliest else None,
        "latest_trip_start": latest[0].get("trip_start_timestamp") if latest else None,
        "validation_warnings": warnings,
        "sample_rows": sample,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-id", default="8bbv-3wbe")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-global-count", action="store_true")
    args = parser.parse_args()

    result = validate(args.dataset_id, include_global_count=args.include_global_count)
    rendered = json.dumps(result, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
