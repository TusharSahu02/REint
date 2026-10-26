from __future__ import annotations

import json
from datetime import date, time, timedelta
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.forecast_selection import expand_hourly_to_half_hourly, select_decision_forecast
from app.services.metrics import summarize

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def _read_parquets() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_parquet(DATA_DIR / "actuals.parquet"),
        pd.read_parquet(DATA_DIR / "forecasts.parquet"),
    )


def _json(text: str) -> dict:
    parsed = json.loads(text)
    json.dumps(parsed, allow_nan=False)  # no NaN leaks in responses
    return parsed


def _ok(client: TestClient, url: str) -> dict:
    response = client.get(url)
    assert response.status_code == 200, response.text
    return _json(response.text)


def _all_delivery_days() -> list[date]:
    start = date(2026, 1, 2)
    return [start + timedelta(days=i) for i in range(31)]


def test_health_matches_parquet(client: TestClient) -> None:
    body = _ok(client, "/api/health")
    actuals, forecasts = _read_parquets()
    assert body["status"] == "ok"
    assert body["counts"]["actuals"] == len(actuals)
    assert body["counts"]["forecasts"] == len(forecasts)
    assert body["data_range"]["start"] == actuals["start_time"].min().date().isoformat()
    assert body["data_range"]["end"] == actuals["start_time"].max().date().isoformat()


def test_decision_forecast_jan_15(client: TestClient) -> None:
    body = _ok(client, "/api/decision-forecast?date=2026-01-15")
    cutoff = pd.Timestamp("2026-01-14T09:00:00Z")
    assert body["delivery_date"] == "2026-01-15"
    assert len(body["rows"]) == 48
    assert body["summary"]["n_slots"] == 48
    for row in body["rows"]:
        assert "missing_forecast" not in row["flags"]
        publish = pd.Timestamp(row["publish_time"])
        assert publish <= cutoff, row
    assert body["summary"]["latest_publish_time_used"] == max(
        row["publish_time"] for row in body["rows"]
    )


def test_cutoff_change_changes_publish_times(client: TestClient) -> None:
    at_9 = _ok(client, "/api/decision-forecast?date=2026-01-15")
    at_6 = _ok(client, "/api/decision-forecast?date=2026-01-15&cutoff=06:00")
    times_9 = {row["publish_time"] for row in at_9["rows"]}
    times_6 = {row["publish_time"] for row in at_6["rows"]}
    assert times_9 != times_6
    cutoff_6 = pd.Timestamp("2026-01-14T06:00:00Z")
    for row in at_6["rows"]:
        assert pd.Timestamp(row["publish_time"]) <= cutoff_6


def test_boundary_dates(client: TestClient) -> None:
    assert client.get("/api/decision-forecast?date=2026-01-02").status_code == 200
    assert client.get("/api/decision-forecast?date=2026-02-01").status_code == 200
    assert client.get("/api/decision-forecast?date=2026-01-01").status_code == 400
    assert client.get("/api/decision-forecast?date=2026-02-02").status_code == 400


def test_buffer_basis(client: TestClient) -> None:
    first = _ok(client, "/api/decision-forecast?date=2026-01-02")["summary"]
    assert first["buffer_basis"] == "full_period_fallback"
    assert first["suggested_buffer_mw"] is not None
    assert first["buffer_sample_size"] > 0

    late = _ok(client, "/api/decision-forecast?date=2026-01-30")["summary"]
    assert late["buffer_basis"] == "expanding_window"
    assert late["suggested_buffer_mw"] is not None
    assert late["buffer_sample_size"] >= 30


def test_accuracy_decision_full_range(client: TestClient) -> None:
    body = _ok(client, "/api/accuracy")
    assert body["basis"] == "decision"
    assert body["overall"]["n"] == 1488
    assert body["naive_overall"] is not None
    assert body["naive_overall"]["n"] == 1488
    assert body["naive_overall"]["mae_mw"] < body["overall"]["mae_mw"]
    assert len(body["by_day"]) == 31
    assert len(body["by_hour_of_day"]) == 24
    assert set(body["by_day"][0]) == {"delivery_date", "mae_mw", "naive_mae_mw", "bias_mw", "n"}
    assert all(day["n"] == 48 for day in body["by_day"])
    assert all(hour["hour"] in range(24) for hour in body["by_hour_of_day"])


def test_accuracy_all_horizons(client: TestClient) -> None:
    body = _ok(client, "/api/accuracy?start=2026-01-02&end=2026-02-01&basis=all_horizons")
    assert body["basis"] == "all_horizons"
    assert body["naive_overall"] is None
    assert body["by_horizon"], "by_horizon must not be empty"
    assert all(bucket["n"] > 0 for bucket in body["by_horizon"])
    assert body["overall"]["n"] > 0


def test_by_horizon_excludes_negative_horizons(client: TestClient) -> None:
    body = _ok(client, "/api/accuracy?start=2026-01-02&end=2026-02-01")
    actuals, forecasts = _read_parquets()
    expanded = expand_hourly_to_half_hourly(forecasts)  # verified step-hold rule
    window = (expanded["start_time"] >= pd.Timestamp("2026-01-02T00:00Z")) & (
        expanded["start_time"] < pd.Timestamp("2026-02-02T00:00Z")
    )
    joined = expanded[window].merge(
        actuals[["start_time", "actual_mw"]], on="start_time", how="inner"
    )
    horizon = (joined["start_time"] - joined["publish_time"]).dt.total_seconds() / 3600
    kept = joined[(horizon >= 0) & joined["forecast_mw"].notna() & joined["actual_mw"].notna()]
    assert sum(bucket["n"] for bucket in body["by_horizon"]) == len(kept)


def test_decision_overall_matches_independent_summarize(client: TestClient) -> None:
    body = _ok(client, "/api/accuracy")
    actuals, forecasts = _read_parquets()
    expanded = expand_hourly_to_half_hourly(forecasts)
    joined_days = []
    for day in _all_delivery_days():
        sel = select_decision_forecast(expanded, day, time(9, 0))
        joined_days.append(
            sel.merge(actuals[["start_time", "actual_mw"]], on="start_time", how="left")
        )
    joined = pd.concat(joined_days, ignore_index=True)
    summary = summarize(joined)
    assert summary["n"] == 1488
    assert summary["mae_mw"] == body["overall"]["mae_mw"]
    assert summary["bias_mw"] == body["overall"]["bias_mw"]


def test_bad_dates_and_cutoff_and_range(client: TestClient) -> None:
    assert client.get("/api/decision-forecast?date=2026-13-01").status_code == 400
    assert client.get("/api/decision-forecast?date=nonsense").status_code == 400
    assert client.get("/api/accuracy?start=2026-01-40").status_code == 400
    assert client.get("/api/decision-forecast?date=2026-01-15&cutoff=9:00").status_code == 400
    assert client.get("/api/decision-forecast?date=2026-01-15&cutoff=25:00").status_code == 400
    assert client.get("/api/accuracy?start=2026-02-01&end=2026-01-02").status_code == 400
    for url in (
        "/api/decision-forecast?date=2026-13-01",
        "/api/accuracy?start=2026-01-40",
        "/api/accuracy?start=2026-02-01&end=2026-01-02",
    ):
        body = _json(client.get(url).text)
        assert "detail" in body
