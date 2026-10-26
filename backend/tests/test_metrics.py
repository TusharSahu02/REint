from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from app.services.metrics import summarize


def base_fixture() -> pd.DataFrame:
    return pd.DataFrame({"forecast_mw": [10.0, 20.0, 30.0], "actual_mw": [8.0, 25.0, 30.0]})


def test_hand_fixture_matches_definition() -> None:
    result = summarize(base_fixture())
    assert result["n"] == 3
    assert result["n_missing_forecast"] == 0
    assert result["n_missing_actual"] == 0
    assert result["bias_mw"] == pytest.approx(-1.0)
    assert result["mae_mw"] == pytest.approx(7 / 3)
    assert result["rmse_mw"] == pytest.approx(math.sqrt(29 / 3))
    assert result["p50_abs_error_mw"] == pytest.approx(2.0)
    assert result["p90_abs_error_mw"] == pytest.approx(4.4)
    assert result["p95_abs_error_mw"] == pytest.approx(4.7)


def test_missing_rows_excluded_and_counted() -> None:
    df = pd.concat(
        [
            base_fixture(),
            pd.DataFrame({"forecast_mw": [np.nan, 15.0], "actual_mw": [9.0, np.nan]}),
        ],
        ignore_index=True,
    )
    result = summarize(df)
    assert result["n"] == 3
    assert result["n_missing_forecast"] == 1
    assert result["n_missing_actual"] == 1
    assert result["mae_mw"] == pytest.approx(7 / 3)
    assert result["bias_mw"] == pytest.approx(-1.0)


def test_nmae_none_when_mean_actual_zero() -> None:
    df = pd.DataFrame({"forecast_mw": [1.0, 2.0, 3.0], "actual_mw": [0.0, 0.0, 0.0]})
    result = summarize(df)
    assert result["nmae_pct"] is None
    assert result["mae_mw"] == pytest.approx(2.0)


def test_all_empty_when_nothing_valid() -> None:
    df = pd.DataFrame({"forecast_mw": [np.nan], "actual_mw": [np.nan]})
    result = summarize(df)
    assert result["n"] == 0
    assert result["bias_mw"] is None
    assert result["mae_mw"] is None
