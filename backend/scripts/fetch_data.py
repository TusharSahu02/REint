"""Fetch the Elexon BMRS snapshot for January 2026 decisions.

Writes backend/data/actuals.parquet and backend/data/forecasts.parquet.
Uses only API parameters verified in docs/DOMAIN_AND_ASSUMPTIONS.md ("Verified API facts").
"""

from __future__ import annotations

import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

WINDFOR_START = datetime(2025, 12, 28, tzinfo=timezone.utc)
WINDFOR_END = datetime(2026, 2, 1, tzinfo=timezone.utc)
ACTUALS_END = datetime(2026, 2, 2, tzinfo=timezone.utc)  # keep start_time < ACTUALS_END (delivery days 2 Jan .. 1 Feb)
FUELHH_FIRST = date(2026, 1, 1)
FUELHH_LAST = date(2026, 2, 1)  # settlement-date filter end (inclusive at the API)

RETRIES = 3
BACKOFF_S = 2.0
SLEEP_BETWEEN_CALLS_S = 0.3


def get_with_retry(client: httpx.Client, path: str, params: dict[str, str]) -> list[dict]:
    last_err: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = client.get(path, params=params, timeout=60.0)
            resp.raise_for_status()
            rows = resp.json()
            if not isinstance(rows, list):
                if isinstance(rows, dict) and isinstance(rows.get("data"), list):
                    rows = rows["data"]
                else:
                    raise ValueError(f"Unexpected response shape: {type(rows)}")
            return rows
        except (httpx.HTTPError, ValueError) as err:
            last_err = err
            wait = BACKOFF_S * attempt
            print(f"  attempt {attempt}/{RETRIES} failed: {err}; retrying in {wait:.0f}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"Fetch failed after {RETRIES} attempts: GET {path} {params}: {last_err}")


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_windfor(client: httpx.Client) -> pd.DataFrame:
    rows: list[dict] = []
    day = WINDFOR_START
    while day < WINDFOR_END:
        chunk_rows = get_with_retry(
            client,
            "/datasets/WINDFOR/stream",
            {"publishDateTimeFrom": iso(day), "publishDateTimeTo": iso(day + timedelta(days=1))},
        )
        rows.extend(chunk_rows)
        print(f"  WINDFOR publish-day {day:%Y-%m-%d}: {len(chunk_rows)} rows", flush=True)
        day += timedelta(days=1)
        time.sleep(SLEEP_BETWEEN_CALLS_S)
    df = pd.DataFrame(
        {
            "start_time": pd.to_datetime([r.get("startTime") for r in rows], errors="coerce", utc=True),
            "publish_time": pd.to_datetime([r.get("publishTime") for r in rows], errors="coerce", utc=True),
            "forecast_mw": pd.to_numeric([r.get("generation") for r in rows], errors="coerce").astype("float64"),
        }
    )
    n_raw = len(df)
    df = df.dropna(subset=["start_time", "publish_time", "forecast_mw"]).drop_duplicates()
    print(f"WINDFOR: {n_raw} raw rows -> {len(df)} after dropna/naive-dedup", flush=True)
    return df.sort_values(["start_time", "publish_time"]).reset_index(drop=True)


def fetch_fuelhh(client: httpx.Client) -> pd.DataFrame:
    rows = get_with_retry(
        client,
        "/datasets/FUELHH/stream",
        {
            "settlementDateFrom": FUELHH_FIRST.isoformat(),
            "settlementDateTo": FUELHH_LAST.isoformat(),
            "fuelType": "WIND",
        },
    )
    wind_rows = [r for r in rows if r.get("fuelType") == "WIND"]
    print(f"  FUELHH: {len(rows)} rows fetched, {len(wind_rows)} with fuelType=WIND", flush=True)
    cuts = [
        pd.Timestamp(FUELHH_FIRST.isoformat(), tz="UTC"),
        pd.Timestamp(ACTUALS_END.isoformat().replace("T", " "), tz="UTC"),
    ]
    df = pd.DataFrame(
        {
            "start_time": pd.to_datetime([r.get("startTime") for r in wind_rows], errors="coerce", utc=True),
            "publish_time": pd.to_datetime([r.get("publishTime") for r in wind_rows], errors="coerce", utc=True),
            "generation": pd.to_numeric([r.get("generation") for r in wind_rows], errors="coerce").astype("float64"),
        }
    )
    kept = df[(df["start_time"] >= cuts[0]) & (df["start_time"] < cuts[1])]
    n_out = len(kept)
    kept = kept.dropna(subset=["start_time", "generation"]).drop_duplicates()
    print(f"FUELHH WIND: {len(wind_rows)} rows fetched -> {n_out} in fetch window -> {len(kept)} after dropna/naive-dedup", flush=True)
    return kept[["start_time", "generation"]].sort_values("start_time").reset_index(drop=True)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with httpx.Client(base_url=BASE_URL) as client:
        forecasts = fetch_windfor(client)
        actuals = fetch_fuelhh(client)
    forecasts.to_parquet(DATA_DIR / "forecasts.parquet", index=False)
    actuals.rename(columns={"generation": "actual_mw"})[["start_time", "actual_mw"]].to_parquet(
        DATA_DIR / "actuals.parquet", index=False
    )
    print(f"actuals.parquet rows: {len(actuals)}")
    print(f"forecasts.parquet rows: {len(forecasts)}")
    print(f"wrote parquet files to {DATA_DIR}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as err:
        print(f"ERROR: {err}", file=sys.stderr)
        sys.exit(1)
