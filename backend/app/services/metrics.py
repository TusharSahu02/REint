from __future__ import annotations

import numpy as np
import pandas as pd


def summarize(df: pd.DataFrame) -> dict:
    """df needs columns forecast_mw and actual_mw. Error = forecast - actual.

    Slots missing either value are excluded from metrics and counted.
    """
    n_missing_forecast = int(df["forecast_mw"].isna().sum())
    n_missing_actual = int(df["actual_mw"].isna().sum())
    valid = df.dropna(subset=["forecast_mw", "actual_mw"])
    base = {
        "n": int(len(valid)),
        "n_missing_forecast": n_missing_forecast,
        "n_missing_actual": n_missing_actual,
    }
    if valid.empty:
        return {
            **base,
            "bias_mw": None,
            "mae_mw": None,
            "rmse_mw": None,
            "nmae_pct": None,
            "p50_abs_error_mw": None,
            "p90_abs_error_mw": None,
            "p95_abs_error_mw": None,
        }
    err = valid["forecast_mw"] - valid["actual_mw"]
    abs_err = err.abs()
    mean_actual = float(valid["actual_mw"].mean())
    mae = float(abs_err.mean())
    return {
        **base,
        "bias_mw": float(err.mean()),
        "mae_mw": mae,
        "rmse_mw": float(np.sqrt((err**2).mean())),
        "nmae_pct": (mae / mean_actual * 100) if mean_actual > 0 else None,
        "p50_abs_error_mw": float(np.percentile(abs_err, 50)),
        "p90_abs_error_mw": float(np.percentile(abs_err, 90)),
        "p95_abs_error_mw": float(np.percentile(abs_err, 95)),
    }
