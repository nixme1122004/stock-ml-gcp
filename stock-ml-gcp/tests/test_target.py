import numpy as np
import pandas as pd
import pytest

from src.features.target import create_future_return_target


def test_future_return_target_uses_only_prices_after_prediction_date() -> None:
    frame = pd.DataFrame({"Close": [100.0, 102.0, 98.0, 101.0, 105.0, 99.0]})

    result = create_future_return_target(frame, horizon_days=2, buy_threshold=0.02, sell_threshold=-0.02)

    assert result.loc[0, "future_return"] == pytest.approx(-0.02)
    assert result.loc[0, "target_signal"] == "SELL"
    assert result.loc[1, "target_signal"] == "HOLD"
    assert result.loc[2, "target_signal"] == "BUY"
    assert result.loc[4:, "future_return"].isna().all()
    assert result.loc[4:, "target_signal"].isna().all()


def test_target_threshold_boundaries_are_inclusive() -> None:
    frame = pd.DataFrame({"Close": [100.0, 102.0, 98.0, 100.0]})

    result = create_future_return_target(frame, horizon_days=1, buy_threshold=0.02, sell_threshold=-0.02)

    assert result.loc[0, "target_signal"] == "BUY"
    assert result.loc[1, "target_signal"] == "SELL"
    assert result.loc[2, "target_signal"] == "BUY"


def test_target_rejects_invalid_thresholds() -> None:
    with pytest.raises(ValueError, match="sell_threshold"):
        create_future_return_target(pd.DataFrame({"Close": [100, 101]}), 1, 0.02, 0.0)
