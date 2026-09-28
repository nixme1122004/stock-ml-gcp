# Experiment Log

Each chat/session working this project logs an entry here: what was built, files changed, what's next.
Keep entries short — this is a build trail, not a report.

---

## Chat 1 — Scope & repo skeleton
**Date:** 2026-09-26
**Built:** Repo structure (`notebooks/`, `src/{data,features,models,utils}`, `tests/`, `configs/`, `docs/`, `reports/`), root `README.md`, `configs/config.yaml` with locked decisions, `requirements.txt`, `.gitignore`.
**Files changed:** All of the above (new repo).

---

## Chat 2 - Raw market-data ingestion
**Date:** 2026-09-28
**Stage:** Ingestion.
**Built:** Config-driven yfinance OHLCV downloader that creates timestamped raw CSV snapshots and source/request metadata for every configured symbol.
**Files changed:** `configs/config.yaml`, `src/data/ingestion.py`, `tests/test_ingestion.py`, `docs/data_ingestion.md`, raw/processed data placeholders.
**Important decisions:** Raw downloads are not cleaned or overwritten; `auto_adjust` is explicitly configured as `false`; processing is deferred to retain an auditable raw layer.
**Known limitations:** A working local Python environment is required to execute the downloader and tests. No scheduled ingestion or cloud storage was added.
**Next:** Cleaning and validation of raw OHLCV data.

---

## Chat 3 - Raw OHLCV cleaning
**Date:** 2026-09-28
**Stage:** Cleaning.
**Built:** Separate processed-data cleaner with UTC timestamp parsing, chronological sorting, duplicate handling, invalid-data checks, and per-output lineage metadata.
**Files changed:** `configs/config.yaml`, `src/data/cleaning.py`, `tests/test_cleaning.py`, `docs/data_cleaning.md`, `docs/experiment_log.md`.
**Important decisions:** Missing or invalid rows are dropped rather than forward-filled; duplicate timestamps retain the last provider observation; market holidays remain absent.
**Known limitations:** Tests cannot run until the local Python launcher is repaired. No features or targets were created.
**Next:** Causal feature engineering using the locked indicator set.
**Next:** Chat 2 — ingestion script for AAPL/MSFT OHLCV to a raw data layer.
