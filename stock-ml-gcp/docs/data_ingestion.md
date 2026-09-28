# Data Ingestion

## Purpose

The Core Tier manually downloads historical daily OHLCV data for AAPL and MSFT from yfinance. Scheduled cloud ingestion is Stretch Backlog work.

## Raw-data contract

Run the downloader from the repository root:

```powershell
python -m src.data.ingestion
```

Each run writes one timestamped CSV snapshot per configured symbol to `data/raw/`, plus JSON metadata containing the source, retrieval time, request parameters, output columns, and row count. Timestamped names prevent silent overwrites.

Ingestion does not sort, deduplicate, fill missing values, remove invalid values, or calculate features. The later cleaning stage performs those transformations so the raw provider response remains auditable.

## Configuration

`configs/config.yaml` controls symbols, provider, date range, adjustment choice, and raw path. `auto_adjust: false` retains provider OHLCV values; any adjustment policy belongs to the documented cleaning stage.
