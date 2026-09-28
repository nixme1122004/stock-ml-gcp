import json

import pandas as pd
import pytest

from src.data.cleaning import clean_ohlcv, clean_raw_file


def test_clean_ohlcv_sorts_deduplicates_and_drops_invalid_rows() -> None:
    raw = pd.DataFrame(
        {
            "Date": ["2024-01-03", "2024-01-02", "2024-01-02", "2024-01-04", "2024-01-05"],
            "Open": [102, 100, 101, 105, 106],
            "High": [103, 102, 103, 104, 107],
            "Low": [101, 99, 100, 103, 105],
            "Close": [102, 101, 102, 104, None],
            "Volume": [20, 10, 11, 30, 40],
        }
    )

    cleaned, summary = clean_ohlcv(raw)

    assert list(cleaned["Date"].dt.strftime("%Y-%m-%d")) == ["2024-01-02", "2024-01-03"]
    assert list(cleaned["Close"]) == [102.0, 102.0]
    assert summary == {
        "input_rows": 5,
        "dropped_missing_or_unparseable": 1,
        "dropped_duplicate_timestamps": 1,
        "dropped_invalid_values": 1,
        "output_rows": 2,
    }


def test_clean_ohlcv_does_not_fill_non_trading_days() -> None:
    raw = pd.DataFrame(
        {
            "Date": ["2024-01-05", "2024-01-08"],
            "Open": [100, 101], "High": [102, 103], "Low": [99, 100],
            "Close": [101, 102], "Volume": [10, 20],
        }
    )

    cleaned, _ = clean_ohlcv(raw)

    assert len(cleaned) == 2
    assert "2024-01-06" not in set(cleaned["Date"].dt.strftime("%Y-%m-%d"))


def test_clean_ohlcv_rejects_missing_required_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        clean_ohlcv(pd.DataFrame({"Date": ["2024-01-02"], "Close": [100]}))


def test_clean_raw_file_preserves_raw_and_writes_lineage(tmp_path) -> None:
    raw_path = tmp_path / "AAPL_20240103T000000Z.csv"
    pd.DataFrame(
        {"Date": ["2024-01-02"], "Open": [100], "High": [102], "Low": [99], "Close": [101], "Volume": [10]}
    ).to_csv(raw_path, index=False)
    processed_path = tmp_path / "processed" / "AAPL_cleaned.csv"

    output_path, metadata_path = clean_raw_file(raw_path, processed_path)

    assert raw_path.exists()
    assert output_path.exists()
    assert json.loads(metadata_path.read_text(encoding="utf-8"))["summary"]["output_rows"] == 1
