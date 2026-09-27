# stock-ml-gcp

A small, finished, resume-ready ML system that predicts short-term stock price **direction** for AAPL and MSFT and converts that prediction into a **BUY / HOLD / SELL** signal — deployed on GCP with basic evaluation, a backtest against buy-and-hold, and a dashboard.

## Problem statement

Given recent price/volume history for a stock, predict whether its price is more likely to move meaningfully **up**, **down**, or stay **flat** over a short horizon, and turn that prediction into an actionable, human-readable signal (BUY / HOLD / SELL) rather than a raw probability or price forecast.

This is explicitly **not** a price-forecasting or trading-bot project. It's a classification problem — direction, not magnitude — with the model and the trading-decision logic kept as two separate, inspectable pieces.

## Scope (Core Tier)

- **Stocks:** AAPL, MSFT only (training universe — the feature pipeline itself is stock-agnostic, see below).
- **Target:** BUY/HOLD/SELL derived from a documented forward-return threshold, not raw price.
- **Features:** Close, Volume, Daily Return, SMA_20, SMA_50, EMA_12, EMA_26, Volatility_20d, RSI — all normalized/relative (returns, ratios, RSI) rather than raw price levels, so the same pipeline could later take in an unseen stock without rewriting feature logic.
- **Models:** Logistic Regression baseline → Random Forest.
- **Validation:** time-aware / walk-forward split — never a random shuffle, to avoid look-ahead leakage.
- **Deployment:** one path — either a Vertex AI endpoint or a Cloud Run app.
- **Dashboard:** Streamlit app showing the latest prediction, signal, and history vs. outcome.

Anything beyond this (scheduled ingestion, Vertex AI Pipelines, CI/CD, drift monitoring, Looker Studio, sentiment/fundamentals features, deep learning models) is intentionally **out of scope** for now — see the Stretch Backlog in the build plan doc.

## Architecture (high level)

```
Raw OHLCV (AAPL/MSFT)
      │  ingestion script
      ▼
Raw data layer (local / GCS)
      │  pandas cleaning
      ▼
Processed dataset (local parquet / BigQuery)
      │  feature engineering (stock-agnostic, normalized)
      ▼
Model-ready dataset
      │  walk-forward split
      ▼
Train: Logistic Regression → Random Forest
      │
      ▼
Evaluation + backtest vs. buy-and-hold
      │
      ▼
Decision engine (rule-based: prediction + confidence → BUY/HOLD/SELL)
      │
      ▼
Deployment (Vertex AI endpoint OR Cloud Run)
      │
      ▼
Streamlit dashboard
```

## Repo layout

```
stock-ml-gcp/
├── notebooks/          # exploration, feature dev, baseline, evaluation notebooks
├── src/
│   ├── data/            # ingestion + cleaning
│   ├── features/        # feature engineering (stock-agnostic)
│   ├── models/           # training + inference
│   └── utils/            # shared helpers
├── tests/                # unit tests
├── configs/
│   └── config.yaml       # locked decisions: tickers, features, split method, model choice
├── docs/
│   └── experiment_log.md # what was built, when, what's next — one entry per chat/session
├── reports/               # evaluation reports, backtest results
├── requirements.txt
└── README.md
```

## Status

Working through an 11-step build plan, one step per chat, tracked in `docs/experiment_log.md`. Current step: **Chat 1 — scope & repo skeleton (this file)**.
