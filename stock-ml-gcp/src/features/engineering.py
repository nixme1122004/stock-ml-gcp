"""Causal, stock-agnostic technical feature engineering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


REQUIRED_COLUMNS = {"Date", "Close", "Volume"}


def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Calculate causal RSI from trailing mean gains and losses."""
    if period < 1:
        raise ValueError("RSI period must be at least one.")
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.rolling(period, min_periods=period).mean()
    average_loss = losses.rolling(period, min_periods=period).mean()
    relative_strength = average_gain / average_loss
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.mask((average_gain == 0) & (average_loss == 0), 50.0)
    rsi = rsi.mask((average_gain > 0) & (average_loss == 0), 100.0)
    rsi = rsi.mask((average_gain == 0) & (average_loss > 0), 0.0)
    return rsi


def engineer_features(frame: pd.DataFrame, rsi_period: int = 14,
                      volume_lookback: int = 20) -> pd.DataFrame:
    """Add locked indicators and scale-independent model features.

    A feature on date t only uses values through the close on date t. This is
    valid for a post-close prediction whose target begins after t; no future
    row or centred rolling window is used.
    """
    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing columns for feature engineering: {sorted(missing_columns)}")
    if volume_lookback < 1:
        raise ValueError("volume_lookback must be at least one.")

    output = frame.copy()
    output["Date"] = pd.to_datetime(output["Date"], utc=True, errors="raise")
    output = output.sort_values("Date", kind="stable").reset_index(drop=True)
    if output["Date"].duplicated().any():
        raise ValueError("Feature input must not contain duplicate timestamps.")

    close = output["Close"].astype(float)
    volume = output["Volume"].astype(float)
    output["daily_return"] = close.pct_change()
    output["sma_20"] = close.rolling(20, min_periods=20).mean()
    output["sma_50"] = close.rolling(50, min_periods=50).mean()
    output["ema_12"] = close.ewm(span=12, adjust=False, min_periods=12).mean()
    output["ema_26"] = close.ewm(span=26, adjust=False, min_periods=26).mean()
    output["volatility_20d"] = output["daily_return"].rolling(20, min_periods=20).std()
    output["rsi"] = calculate_rsi(close, rsi_period)
    output["volume_sma_20"] = volume.rolling(volume_lookback, min_periods=volume_lookback).mean()

    # Raw Close and Volume remain as auditable source columns; the model receives
    # only these relative representations, preventing cross-stock price scaling.
    output["close_to_sma_20"] = close / output["sma_20"] - 1
    output["close_to_sma_50"] = close / output["sma_50"] - 1
    output["volume_relative_20"] = volume / output["volume_sma_20"] - 1
    output["sma_20_to_sma_50"] = output["sma_20"] / output["sma_50"] - 1
    output["ema_12_to_ema_26"] = output["ema_12"] / output["ema_26"] - 1
    return output.replace([np.inf, -np.inf], np.nan)


def engineer_processed_file(processed_path: Path, feature_path: Path,
                            rsi_period: int = 14, volume_lookback: int = 20) -> tuple[Path, Path]:
    """Create a feature file and metadata sidecar from one cleaned input file."""
    if feature_path.exists():
        raise FileExistsError(f"Feature output already exists: {feature_path}")
    features = engineer_features(pd.read_csv(processed_path), rsi_period, volume_lookback)
    feature_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(feature_path, index=False)
    metadata_path = feature_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps({
        "processed_input": str(processed_path),
        "feature_output": str(feature_path),
        "prediction_timing": "post-close on date t",
        "causality": "features use observations at or before date t only",
        "rsi_period": rsi_period,
        "volume_lookback": volume_lookback,
        "model_columns": [
            "close_to_sma_20", "close_to_sma_50", "volume_relative_20", "daily_return",
            "sma_20_to_sma_50", "ema_12_to_ema_26", "volatility_20d", "rsi",
        ],
    }, indent=2) + "\n", encoding="utf-8")
    return feature_path, metadata_path


def engineer_latest_configured_files(config_path: Path, project_root: Path | None = None) -> list[tuple[Path, Path]]:
    """Engineer features for the latest cleaned file per configured symbol."""
    with config_path.open(encoding="utf-8") as file:
        config: dict[str, Any] = yaml.safe_load(file) or {}
    root = project_root or config_path.parent.parent
    processed_directory = root / config["data"]["processed_layer"]
    feature_config = config["features"]
    outputs: list[tuple[Path, Path]] = []
    for symbol in config["data"]["tickers"]:
        inputs = sorted(processed_directory.glob(f"{symbol}_*_cleaned.csv"))
        if not inputs:
            raise FileNotFoundError(f"No cleaned file found for {symbol} in {processed_directory}.")
        input_path = inputs[-1]
        output_path = processed_directory / f"{input_path.stem}_features.csv"
        outputs.append(engineer_processed_file(
            input_path, output_path, feature_config["rsi_period"], feature_config["volume_lookback"]
        ))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Create causal technical features from cleaned OHLCV.")
    parser.add_argument("--config", type=Path, default=Path("configs/config.yaml"))
    args = parser.parse_args()
    for feature_path, metadata_path in engineer_latest_configured_files(args.config):
        print(f"Wrote {feature_path}")
        print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
