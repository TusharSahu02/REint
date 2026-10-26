from __future__ import annotations

import numpy as np
import pandas as pd

MIN_POSITIVE_SAMPLES = 30


def over_forecast_buffer(
    errors: pd.Series, q: float = 90.0, min_n: int = MIN_POSITIVE_SAMPLES
) -> tuple[float | None, int]:
    """P-q of errors where error > 0 (forecast above actual).

    errors = forecast - actual. Returns (buffer_mw or None if too few samples, count of positives).
    """
    pos = errors.dropna()
    pos = pos[pos > 0]
    if len(pos) < min_n:
        return None, int(len(pos))
    return float(np.percentile(pos, q)), int(len(pos))
