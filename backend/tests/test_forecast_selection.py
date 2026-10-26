from __future__ import annotations

from datetime import date, time, timezone

import pandas as pd
import pytest

from app.services.forecast_selection import (
    cutoff_utc_for,
    expand_hourly_to_half_hourly,
    select_decision_forecast,
    select_naive_forecast,
)

CUTOFF_LON = time(9, 0)
DELIVERY = date(2026, 1, 15)
CUTOFF = cutoff_utc_for(DELIVERY, CUTOFF_LON)  # 2026-01-14T09:00:00Z (January = GMT)
SLOT = pd.Timestamp("2026-01-15T00:30Z")


def hourly_fixture() -> pd.DataFrame:
    """24 hourly rows for 2026-01-15, two publish cycles: 07:30Z (on time), 12:30Z (late)."""
    start_times = pd.date_range(pd.Timestamp("2026-01-15T00:00Z"), periods=24, freq="1h")
    rows = []
    for publish, base in (
        (pd.Timestamp("2026-01-14T07:30Z"), 100.0),
        (pd.Timestamp("2026-01-15T12:30Z"), 200.0),
    ):
        for st in start_times:
            rows.append({"start_time": st, "publish_time": publish, "forecast_mw": base})
    return pd.DataFrame(rows)


def test_expansion_doubles_and_shares_fields() -> None:
    fx = hourly_fixture()
    expanded = expand_hourly_to_half_hourly(fx)
    assert len(expanded) == 2 * len(fx)
    on_hour = expanded[expanded["start_time"].dt.minute == 0].reset_index(drop=True)
    half_hour = expanded[expanded["start_time"].dt.minute == 30].reset_index(drop=True)
    assert (half_hour["start_time"] - on_hour["start_time"] == pd.Timedelta(minutes=30)).all()
    assert (half_hour["publish_time"] == on_hour["publish_time"]).all()
    assert (half_hour["forecast_mw"] == on_hour["forecast_mw"]).all()


def test_expansion_rejects_half_hour_rows() -> None:
    fx = expand_hourly_to_half_hourly(hourly_fixture())
    with pytest.raises(ValueError, match="expected hourly forecasts"):
        expand_hourly_to_half_hourly(fx)


def test_cutoff_boundary_exact_cutoff_wins() -> None:
    rows = pd.DataFrame(
        {
            "start_time": [SLOT] * 3,
            "publish_time": [
                CUTOFF - pd.Timedelta(seconds=1),
                CUTOFF,
                CUTOFF + pd.Timedelta(seconds=1),
            ],
            "forecast_mw": [10.0, 20.0, 30.0],
        }
    )
    out = select_decision_forecast(rows, DELIVERY, CUTOFF_LON)
    chosen = out[out["start_time"] == SLOT].iloc[0]
    assert chosen["publish_time"] == pd.Timestamp(CUTOFF)
    assert chosen["forecast_mw"] == 20.0


def test_late_publish_never_monetizes() -> None:
    rows = pd.DataFrame(
        {
            "start_time": [SLOT],
            "publish_time": [CUTOFF + pd.Timedelta(seconds=1)],
            "forecast_mw": [30.0],
        }
    )
    out = select_decision_forecast(rows, DELIVERY, CUTOFF_LON)
    chosen = out[out["start_time"] == SLOT].iloc[0]
    assert chosen["missing_forecast"]
    assert pd.isna(chosen["forecast_mw"])


def test_slot_with_no_eligible_forecast_is_missing() -> None:
    fx = hourly_fixture().loc[lambda d: d["publish_time"] > CUTOFF]
    out = select_decision_forecast(fx, DELIVERY, CUTOFF_LON)
    assert len(out) == 48
    assert out["missing_forecast"].all()
    assert out["forecast_mw"].isna().all()


def test_full_day_48_slots_no_missing() -> None:
    expanded = expand_hourly_to_half_hourly(hourly_fixture())
    out = select_decision_forecast(expanded, DELIVERY, CUTOFF_LON)
    assert len(out) == 48
    assert not out["missing_forecast"].any()


def test_naive_picks_latest_overall_and_differs() -> None:
    expanded = expand_hourly_to_half_hourly(hourly_fixture())
    decision = select_decision_forecast(expanded, DELIVERY, CUTOFF_LON)
    naive = select_naive_forecast(expanded, DELIVERY)
    assert (naive["publish_time"] == pd.Timestamp("2026-01-15T12:30Z")).all()
    assert (decision["publish_time"] == pd.Timestamp("2026-01-14T07:30Z")).all()
    assert not naive.equals(decision)


def test_cutoff_utc_conversion() -> None:
    expected = pd.Timestamp("2026-01-14T09:00:00Z").to_pydatetime()
    assert cutoff_utc_for(DELIVERY, CUTOFF_LON) == expected
    assert cutoff_utc_for(DELIVERY, CUTOFF_LON).tzinfo is timezone.utc
