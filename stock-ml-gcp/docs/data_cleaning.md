# Data Cleaning

## Purpose

Cleaning converts a raw provider snapshot into a separate processed CSV without modifying the raw source file. Run it after ingestion:

```powershell
python -m src.data.cleaning
```

The script selects the latest timestamped snapshot for each configured symbol and writes a matching `_cleaned.csv` file plus lineage metadata to `data/processed/`.

## Rules

- Parse timestamps as UTC and sort ascending before later feature engineering.
- Drop duplicate timestamps, retaining the last provider observation.
- Drop rows with missing or unparseable core OHLCV values; do not forward-fill.
- Drop non-finite data, non-positive prices, negative volume, and OHLC values that violate the daily low/high range.
- Keep market holidays and non-trading days absent. No calendar reindexing or fabricated prices occur.

The metadata sidecar records row counts removed by each rule. This provides an auditable boundary between raw provider data and all downstream transformations.
