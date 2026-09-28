"""Cleaning and validation for raw daily OHLCV snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


PRICE_COLUMNS = ("Open", "High", "Low", "Close")
CORE_COLUMNS = (*PRICE_COLUMNS, "Volume")


def clean_ohlcv(raw_frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Return valid, chronologically sorted OHLCV rows and an audit summary.

    Missing and invalid rows are removed rather than imputed: forward-filling a
    non-trading or malformed observation would invent market information.
    """
    missing_columns = set(CORE_COLUMNS).difference(raw_frame.columns)
    if missing_columns:
        raise ValueError(f"Raw OHLCV is missing required columns: {sorted(missing_columns)}")
    if "Date" not in raw_frame.columns:
        raise ValueError("Raw OHLCV CSV must contain a Date column.")

    frame = raw_frame.copy()
    initial_rows = len(frame)
    frame["Date"] = pd.to_datetime(frame["Date"], utc=True, errors="coerce")
    for column in CORE_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(subset=["Date", *CORE_COLUMNS])
    after_missing_rows = len(frame)
    frame = frame.sort_values("Date", kind="stable")
    frame = frame.drop_duplicates(subset="Date", keep="last")
    after_duplicate_rows = len(frame)

    finite_values = np.isfinite(frame.loc[:, CORE_COLUMNS]).all(axis=1)
    valid_prices = (frame.loc[:, PRICE_COLUMNS] > 0).all(axis=1)
    valid_volume = frame["Volume"] >= 0
    valid_ohlc_range = (
        (frame["High"] >= frame["Low"])
        & frame["Open"].between(frame["Low"], frame["High"])
        & frame["Close"].between(frame["Low"], frame["High"])
    )
    frame = frame.loc[finite_values & valid_prices & valid_volume & valid_ohlc_range].copy()
    if frame.empty:
        raise ValueError("No valid OHLCV rows remain after cleaning.")

    summary = {
        "input_rows": initial_rows,
        "dropped_missing_or_unparseable": initial_rows - after_missing_rows,
        "dropped_duplicate_timestamps": after_missing_rows - after_duplicate_rows,
        "dropped_invalid_values": after_duplicate_rows - len(frame),
        "output_rows": len(frame),
    }
    return frame.reset_index(drop=True), summary


def clean_raw_file(raw_path: Path, processed_path: Path) -> tuple[Path, Path]:
    """Clean one raw CSV without changing it and write processed data plus lineage."""
    raw_frame = pd.read_csv(raw_path)
    cleaned_frame, summary = clean_ohlcv(raw_frame)
    processed_path.parent.mkdir(parents=True, exist_ok=True)
    if processed_path.exists():
        raise FileExistsError(f"Processed output already exists: {processed_path}")
    cleaned_frame.to_csv(processed_path, index=False)
    metadata_path = processed_path.with_suffix(".metadata.json")
    metadata = {
        "raw_input": str(raw_path),
        "processed_output": str(processed_path),
        "cleaning_rules": {
            "sort": "Date ascending",
            "duplicate_policy": "keep last observation for a timestamp",
            "missing_policy": "drop rows with missing/unparseable timestamp or core OHLCV",
            "invalid_policy": "drop non-finite values, non-positive prices, negative volume, invalid OHLC ranges",
            "market_holidays": "not reindexed or forward-filled",
        },
        "summary": summary,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return processed_path, metadata_path


def clean_latest_configured_snapshots(config_path: Path, project_root: Path | None = None) -> list[tuple[Path, Path]]:
    """Clean the latest timestamped raw snapshot for each configured symbol."""
    with config_path.open(encoding="utf-8") as file:
        config: dict[str, Any] = yaml.safe_load(file) or {}
    data_config = config["data"]
    root = project_root or config_path.parent.parent
    raw_directory = root / data_config["raw_layer"]
    processed_directory = root / data_config["processed_layer"]
    outputs: list[tuple[Path, Path]] = []
    for symbol in data_config["tickers"]:
        snapshots = sorted(raw_directory.glob(f"{symbol}_*.csv"))
        if not snapshots:
            raise FileNotFoundError(f"No raw snapshot found for {symbol} in {raw_directory}.")
        raw_path = snapshots[-1]
        outputs.append(clean_raw_file(raw_path, processed_directory / f"{raw_path.stem}_cleaned.csv"))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean latest configured raw OHLCV snapshots.")
    parser.add_argument("--config", type=Path, default=Path("configs/config.yaml"))
    args = parser.parse_args()
    for processed_path, metadata_path in clean_latest_configured_snapshots(args.config):
        print(f"Wrote {processed_path}")
        print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
