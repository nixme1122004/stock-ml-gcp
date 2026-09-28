# Feature Engineering

## Prediction timing and leakage prevention

The system makes a post-market-close prediction on date `t`. Every feature for `t` uses the close and volume observed no later than `t`; the future-return target will use prices after `t`. Rolling windows are trailing windows, never centred, and no feature uses `shift(-1)`.

The separate feature guide recommends lagging all features by one day. That is appropriate for a prediction made before the close of `t`. This project instead documents an end-of-day prediction, so an additional lag is unnecessary and would discard valid information available at prediction time.

## Locked indicators and model representations

| Locked indicator | Calculation retained in output | Model representation |
| --- | --- | --- |
| Close | `Close` | `close_to_sma_20`, `close_to_sma_50` |
| Volume | `Volume` | `volume_relative_20` = volume / trailing 20-day mean - 1 |
| Daily Return | `daily_return` | `daily_return` |
| SMA 20 / SMA 50 | `sma_20`, `sma_50` | `sma_20_to_sma_50` |
| EMA 12 / EMA 26 | `ema_12`, `ema_26` | `ema_12_to_ema_26` |
| Volatility 20d | `volatility_20d` | `volatility_20d` |
| RSI | `rsi` | `rsi` |

The raw indicators remain in the feature file for inspection, but they are not model inputs where their absolute scale would mix AAPL and MSFT price levels. Initial rows naturally contain NaN values until their trailing window is complete. They are retained here and will be removed only when creating the model-ready, labelled dataset.

Run from the project root after cleaning:

```powershell
python -m src.features.engineering
```
