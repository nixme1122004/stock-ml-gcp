"""Raw OHLCV ingestion for the stock-ml-gcp project.

This module deliberately stores provider responses as timestamped snapshots.
Cleaning, adjustment decisions, and feature creation belong to later pipeline stages.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml
import yfinance as yf


REQUIRED_CONFIG_KEYS = {"tickers", "source", "start_date", "raw_layer"}


def load_data_config(config_path: Path) -> dict[str, Any]:
    """Load and minimally validate the data section of the project configuration."""
    with config_path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}

    data_config = config.get("data")
    if not isinstance(data_config, dict):
        raise ValueError("config.yaml must contain a 'data' mapping.")

    missing_keys = REQUIRED_CONFIG_KEYS.difference(data_config)
    if missing_keys:
        missing = ", ".join(sorted(missing_keys))
        raise ValueError(f"data configuration is missing: {missing}.")
    if data_config["source"] != "yfinance":
        raise ValueError("Core Tier ingestion currently supports only source: yfinance.")
    if not data_config["tickers"]:
        raise ValueError("data.tickers must contain at least one symbol.")
    return data_config


def fetch_ohlcv(symbol: str, start_date: str, end_date: str | None, auto_adjust: bool,
                actions: bool = False,
                ticker_factory: Callable[[str], Any] = yf.Ticker) -> pd.DataFrame:
    """Download one symbol's uncleaned OHLCV history from yfinance."""
    history = ticker_factory(symbol).history(
        start=start_date, end=end_date, auto_adjust=auto_adjust, actions=actions
    )
    if history.empty:
        raise ValueError(f"No OHLCV rows returned for {symbol}.")
    if not isinstance(history.index, pd.DatetimeIndex):
        raise ValueError(f"Expected a DatetimeIndex from yfinance for {symbol}.")
    return history.copy()


def write_raw_snapshot(frame: pd.DataFrame, symbol: str, raw_directory: Path,
                       request_metadata: Mapping[str, Any],
                       retrieved_at: datetime | None = None) -> tuple[Path, Path]:
    """Write an immutable CSV snapshot and adjacent metadata JSON file."""
    if frame.empty:
        raise ValueError("Cannot write an empty raw snapshot.")
    timestamp = retrieved_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware.")
    timestamp = timestamp.astimezone(timezone.utc)
    snapshot_id = timestamp.strftime("%Y%m%dT%H%M%SZ")
    raw_directory.mkdir(parents=True, exist_ok=True)
    csv_path = raw_directory / f"{symbol}_{snapshot_id}.csv"
    metadata_path = raw_directory / f"{symbol}_{snapshot_id}.metadata.json"
    if csv_path.exists() or metadata_path.exists():
        raise FileExistsError(f"Raw snapshot already exists for {symbol}: {snapshot_id}")
    output = frame.copy()
    output.index.name = output.index.name or "Date"
    output.to_csv(csv_path, index=True)
    metadata = {
        "symbol": symbol, "source": "yfinance", "retrieved_at_utc": timestamp.isoformat(),
        "row_count": len(output), "columns": output.columns.tolist(), "request": dict(request_metadata),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return csv_path, metadata_path


def ingest_from_config(config_path: Path, project_root: Path | None = None,
                       ticker_factory: Callable[[str], Any] = yf.Ticker,
                       retrieved_at: datetime | None = None) -> list[tuple[Path, Path]]:
    """Download configured symbols and save timestamped raw snapshots."""
    data_config = load_data_config(config_path)
    root = project_root or config_path.parent.parent
    raw_directory = root / data_config["raw_layer"]
    request = {"start_date": data_config["start_date"], "end_date": data_config.get("end_date"),
               "auto_adjust": data_config.get("auto_adjust", False), "actions": False}
    outputs: list[tuple[Path, Path]] = []
    for symbol in data_config["tickers"]:
        frame = fetch_ohlcv(symbol=symbol, ticker_factory=ticker_factory, **request)
        outputs.append(write_raw_snapshot(frame, symbol, raw_directory, request, retrieved_at))
    return outputs


def main() -> None:
    """Run manual/script-based Core Tier ingestion."""
    parser = argparse.ArgumentParser(description="Download raw AAPL/MSFT OHLCV snapshots.")
    parser.add_argument("--config", type=Path, default=Path("configs/config.yaml"))
    args = parser.parse_args()
    for csv_path, metadata_path in ingest_from_config(args.config):
        print(f"Wrote {csv_path}")
        print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
