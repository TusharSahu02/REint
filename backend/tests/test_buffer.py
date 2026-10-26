from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.buffer import MIN_POSITIVE_SAMPLES, over_forecast_buffer


def test_too_few_positives_returns_none_with_count() -> None:
    errors = pd.Series([5.0] * (MIN_POSITIVE_SAMPLES - 1) + [-2.0, np.nan])
    buffer, count = over_forecast_buffer(errors)
    assert buffer is None
    assert count == MIN_POSITIVE_SAMPLES - 1


def test_p90_matches_numpy_percentile() -> None:
    values = np.linspace(1.0, 40.0, 40)  # 40 known positive errors
    errors = pd.Series(np.concatenate([values, [-1.0, -2.0]]))
    buffer, count = over_forecast_buffer(errors)
    assert count == 40
    assert buffer == pytest_like(np.percentile(values, 90.0))


def pytest_like(x: float) -> float:
    return float(x)  # exact equality via same percentile call


def test_zero_and_negative_errors_excluded() -> None:
    errors = pd.Series([100.0] * MIN_POSITIVE_SAMPLES + [0.0, -5.0])
    buffer, count = over_forecast_buffer(errors)
    assert count == MIN_POSITIVE_SAMPLES
    assert buffer == pytest_like(100.0)
