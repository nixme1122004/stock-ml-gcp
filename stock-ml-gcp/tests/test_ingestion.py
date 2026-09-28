from datetime import datetime, timezone
import json

import pandas as pd
import pytest

from src.data.ingestion import fetch_ohlcv, ingest_from_config, write_raw_snapshot


class FakeTicker:
    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def history(self, **kwargs: object) -> pd.DataFrame:
        return pd.DataFrame(
            {"Open": [100.0, 101.0], "Close": [101.0, 102.0], "Volume": [10, 20]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03"], utc=True),
        )


def test_fetch_ohlcv_preserves_provider_rows_and_timestamp_index() -> None:
    result = fetch_ohlcv("AAPL", "2024-01-01", None, False, ticker_factory=FakeTicker)
    assert list(result["Close"]) == [101.0, 102.0]
    assert isinstance(result.index, pd.DatetimeIndex)
    assert result.index.tz is not None


def test_write_raw_snapshot_records_source_and_request(tmp_path) -> None:
    frame = pd.DataFrame({"Close": [101.0]}, index=pd.to_datetime(["2024-01-02"], utc=True))
    retrieved_at = datetime(2024, 1, 3, tzinfo=timezone.utc)
    csv_path, metadata_path = write_raw_snapshot(
        frame, "AAPL", tmp_path,
        {"start_date": "2018-01-01", "end_date": None, "auto_adjust": False}, retrieved_at,
    )
    assert csv_path.name == "AAPL_20240103T000000Z.csv"
    saved = pd.read_csv(csv_path)
    assert "Date" in saved.columns
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["source"] == "yfinance"
    assert metadata["request"]["auto_adjust"] is False


def test_raw_snapshot_never_silently_overwrites(tmp_path) -> None:
    frame = pd.DataFrame({"Close": [101.0]}, index=pd.to_datetime(["2024-01-02"]))
    retrieved_at = datetime(2024, 1, 3, tzinfo=timezone.utc)
    write_raw_snapshot(frame, "AAPL", tmp_path, {}, retrieved_at)
    with pytest.raises(FileExistsError):
        write_raw_snapshot(frame, "AAPL", tmp_path, {}, retrieved_at)


def test_ingest_from_config_uses_configured_symbols(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "data:\n  tickers: [AAPL, MSFT]\n  source: yfinance\n  start_date: '2024-01-01'\n"
        "  end_date: null\n  auto_adjust: false\n  raw_layer: data/raw\n", encoding="utf-8"
    )
    outputs = ingest_from_config(
        config_path, project_root=tmp_path, ticker_factory=FakeTicker,
        retrieved_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
    )
    assert [pair[0].name for pair in outputs] == ["AAPL_20240103T000000Z.csv", "MSFT_20240103T000000Z.csv"]
