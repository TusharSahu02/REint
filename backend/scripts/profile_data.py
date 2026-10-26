"""Profile the fetched snapshot parquet files and print the M1 statistics."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTUAL_WINDOW = (pd.Timestamp("2026-01-01", tz="UTC"), pd.Timestamp("2026-02-02", tz="UTC"))
TZ = "Europe/London"
CUTOFF_LOCAL_TIME = datetime.strptime("09:00", "%H:%M").time()


def fmt(df: pd.DataFrame, cols: list[str]) -> str:
    return df[cols].head(5).to_string(index=False)


def coverage_check(forecasts: pd.DataFrame) -> None:
    """Standalone check: latest publish cycle <= cutoff per delivery day covers how many hourly slots."""
    print("\n== coverage check (per delivery day) ==")
    zone = ZoneInfo(TZ)
    shorts: list[str] = []
    full = 0
    delivery = date(2026, 1, 2)
    while delivery <= date(2026, 2, 1):
        cutoff = datetime.combine(delivery - timedelta(days=1), CUTOFF_LOCAL_TIME, tzinfo=zone).astimezone(ZoneInfo("UTC"))
        chosen = forecasts[forecasts["publish_time"] <= pd.Timestamp(cutoff)]
        if chosen.empty:
            print(f"  D={delivery} cutoff={cutoff:%Y-%m-%T}Z: NO PUBLISH CYCLE <= cutoff")
            shorts.append(delivery.isoformat())
        else:
            latest = chosen["publish_time"].max()
            cycle = chosen[chosen["publish_time"] == latest]
            local_day_start = datetime.combine(delivery, datetime.min.time(), tzinfo=zone)
            local_day_end = datetime.combine(delivery + timedelta(days=1), datetime.min.time(), tzinfo=zone)
            slot_stamps = pd.date_range(
                local_day_start.astimezone(ZoneInfo("UTC")),
                local_day_end.astimezone(ZoneInfo("UTC")),
                freq="1h",
                inclusive="left",
            )
            covered = int(cycle["start_time"].isin(slot_stamps).sum())
            status = "OK" if covered == 24 else "SHORT"
            print(f"  D={delivery} cutoff={cutoff:%Y-%m-%d %H:%MZ}: publish={latest} covered={covered}/24 {status}")
            if covered == 24:
                full += 1
            else:
                shorts.append(delivery.isoformat())
        delivery += timedelta(days=1)
    print(f"summary: {full} of 31 days full coverage (24/24)")
    if shorts:
        print(f"days below 24/24: {shorts}")
    else:
        print("days below 24/24: none")


def main() -> None:
    actuals: pd.DataFrame = pd.read_parquet(DATA_DIR / "actuals.parquet")
    forecasts: pd.DataFrame = pd.read_parquet(DATA_DIR / "forecasts.parquet")

    for name, df in (("actuals", actuals), ("forecasts", forecasts)):
        print(f"== {name} ==")
        print(f"rows: {len(df)}")
        print("dtypes:", df.dtypes.astype(str).to_dict())
        if "publish_time" in df.columns:
            print(f"start_time min/max: {df.start_time.min()} / {df.start_time.max()}")
            print(f"publish_time min/max: {df.publish_time.min()} / {df.publish_time.max()}")
        else:
            print(f"start_time min/max: {df.start_time.min()} / {df.start_time.max()}")

    valid = forecasts.dropna(subset=["publish_time"])
    publish_counts = valid.publish_time.value_counts()
    distinct_publish = valid.publish_time.nunique()
    sorted_publish = valid.publish_time.sort_values().unique()
    gaps = pd.Series(sorted_publish).diff().dropna().dt.total_seconds() / 3600
    print("\n== forecasts: publish cadence ==")
    print(f"distinct publish_time values: {distinct_publish}")
    print(f"gap hours between consecutive distinct publish times: "
          f"min {gaps.min():.2f}, median {gaps.median():.2f}, max {gaps.max():.2f}")
    print("gap frequency (hours -> count):", gaps.value_counts().sort_index().to_dict())
    print(f"typical rows per publish cycle: min {publish_counts.min()}, "
          f"median {publish_counts.median()}, max {publish_counts.max()}")

    horizons = (valid.start_time - valid.publish_time).dt.total_seconds() / 3600
    print("\n== forecasts: horizon hours (start_time - publish_time) ==")
    print(f"min {horizons.min():.2f}, median {horizons.median():.2f}, max {horizons.max():.2f}")

    dup_pairs = int(forecasts.duplicated(subset=["start_time", "publish_time"]).sum())
    print(f"\nforecasts duplicate (start_time, publish_time) pairs (beyond first): {dup_pairs}")

    slots = pd.date_range(ACTUAL_WINDOW[0], ACTUAL_WINDOW[1], freq="30min", inclusive="left")
    have = pd.DatetimeIndex(actuals.start_time)
    missing = slots.difference(have)
    print("\n== actuals: slot coverage ==")
    print(f"expected slots {ACTUAL_WINDOW[0]} .. {ACTUAL_WINDOW[1]} (exclusive): {len(slots)}")
    print(f"missing slots in window: {len(missing)}")
    if len(missing):
        print("first missing:", list(map(str, missing[:5])))

    print("\n== sample rows ==")
    print("-- actuals (5) --")
    print(fmt(actuals, ["start_time", "actual_mw"]))
    print("-- forecasts (5) --")
    print(fmt(forecasts, ["start_time", "publish_time", "forecast_mw"]))

    coverage_check(forecasts)


if __name__ == "__main__":
    main()
