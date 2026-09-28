import numpy as np
import pandas as pd

from src.features.engineering import calculate_rsi, engineer_features


def make_ohlcv(rows: int = 60) -> pd.DataFrame:
    close = pd.Series(np.arange(100, 100 + rows, dtype=float))
    return pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=rows, freq="B"),
        "Close": close,
        "Volume": np.arange(1_000, 1_000 + rows),
    })


def test_features_are_chronological_and_have_expected_warmup_nans() -> None:
    result = engineer_features(make_ohlcv().iloc[::-1])

    assert result["Date"].is_monotonic_increasing
    assert pd.isna(result.loc[0, "daily_return"])
    assert result.loc[:18, "sma_20"].isna().all()
    assert pd.isna(result.loc[48, "sma_50"])
    assert not pd.isna(result.loc[49, "sma_50"])


def test_return_and_relative_features_use_only_current_and_past_data() -> None:
    frame = make_ohlcv()
    result = engineer_features(frame)
    row = 49
    expected_sma_20 = frame.loc[row - 19:row, "Close"].mean()

    assert result.loc[row, "daily_return"] == (frame.loc[row, "Close"] / frame.loc[row - 1, "Close"] - 1)
    assert result.loc[row, "close_to_sma_20"] == (frame.loc[row, "Close"] / expected_sma_20 - 1)
    assert result.loc[row, "sma_20_to_sma_50"] == (result.loc[row, "sma_20"] / result.loc[row, "sma_50"] - 1)


def test_rsi_handles_gains_losses_and_flat_windows() -> None:
    assert calculate_rsi(pd.Series([100.0] * 15), period=14).iloc[-1] == 50.0
    assert calculate_rsi(pd.Series(np.arange(100.0, 115.0)), period=14).iloc[-1] == 100.0
    assert calculate_rsi(pd.Series(np.arange(115.0, 100.0, -1.0)), period=14).iloc[-1] == 0.0


def test_future_change_does_not_change_an_earlier_feature_row() -> None:
    original = make_ohlcv()
    changed = original.copy()
    changed.loc[55, "Close"] = 10_000.0

    original_features = engineer_features(original)
    changed_features = engineer_features(changed)

    pd.testing.assert_series_equal(
        original_features.loc[50, ["daily_return", "sma_20", "ema_26", "rsi"]],
        changed_features.loc[50, ["daily_return", "sma_20", "ema_26", "rsi"]],
    )
