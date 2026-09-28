"""Future-return target construction for BUY/HOLD/SELL classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml


def create_future_return_target(frame: pd.DataFrame, horizon_days: int,
                                buy_threshold: float, sell_threshold: float) -> pd.DataFrame:
    """Add future return and BUY/HOLD/SELL labels without leaking them into features.

    For date t, `future_return` equals Close[t + horizon] / Close[t] - 1.
    The final `horizon_days` rows have no known outcome and retain missing labels.
    """
    if "Close" not in frame.columns:
        raise ValueError("Target construction requires a Close column.")
    if horizon_days < 1:
        raise ValueError("horizon_days must be at least one.")
    if not sell_threshold < 0 < buy_threshold:
        raise ValueError("Require sell_threshold < 0 < buy_threshold.")

    output = frame.copy()
    future_return = output["Close"].shift(-horizon_days) / output["Close"] - 1
    output["future_return"] = future_return
    labels = np.select(
        [future_return >= buy_threshold, future_return <= sell_threshold],
        ["BUY", "SELL"],
        default="HOLD",
    )
    output["target_signal"] = pd.Series(labels, index=output.index).where(future_return.notna())
    return output


def label_feature_file(feature_path: Path, labelled_path: Path, target_config: dict[str, Any]) -> tuple[Path, Path]:
    """Create a labelled feature file and metadata sidecar from a feature file."""
    if labelled_path.exists():
        raise FileExistsError(f"Labelled output already exists: {labelled_path}")
    labelled = create_future_return_target(
        pd.read_csv(feature_path),
        horizon_days=target_config["horizon_days"],
        buy_threshold=target_config["buy_threshold"],
        sell_threshold=target_config["sell_threshold"],
    )
    labelled_path.parent.mkdir(parents=True, exist_ok=True)
    labelled.to_csv(labelled_path, index=False)
    metadata_path = labelled_path.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps({
        "feature_input": str(feature_path),
        "labelled_output": str(labelled_path),
        "formula": "Close[t + horizon_days] / Close[t] - 1",
        "horizon_days": target_config["horizon_days"],
        "buy_threshold": target_config["buy_threshold"],
        "sell_threshold": target_config["sell_threshold"],
        "classes": {"BUY": ">= buy_threshold", "HOLD": "between thresholds", "SELL": "<= sell_threshold"},
    }, indent=2) + "\n", encoding="utf-8")
    return labelled_path, metadata_path


def label_latest_configured_files(config_path: Path, project_root: Path | None = None) -> list[tuple[Path, Path]]:
    """Label the latest feature file for every configured symbol."""
    with config_path.open(encoding="utf-8") as file:
        config: dict[str, Any] = yaml.safe_load(file) or {}
    root = project_root or config_path.parent.parent
    directory = root / config["data"]["processed_layer"]
    outputs: list[tuple[Path, Path]] = []
    for symbol in config["data"]["tickers"]:
        inputs = sorted(directory.glob(f"{symbol}_*_cleaned_features.csv"))
        if not inputs:
            raise FileNotFoundError(f"No feature file found for {symbol} in {directory}.")
        input_path = inputs[-1]
        outputs.append(label_feature_file(input_path, directory / f"{input_path.stem}_labelled.csv", config["target"]))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Create configurable future-return targets.")
    parser.add_argument("--config", type=Path, default=Path("configs/config.yaml"))
    args = parser.parse_args()
    for labelled_path, metadata_path in label_latest_configured_files(args.config):
        print(f"Wrote {labelled_path}")
        print(f"Wrote {metadata_path}")


if __name__ == "__main__":
    main()
