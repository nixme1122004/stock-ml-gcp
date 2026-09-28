# Target Definition

For each market date `t`, the system predicts the five-trading-day future return:

`future_return[t] = Close[t + 5] / Close[t] - 1`

The target is configured in `configs/config.yaml`:

- BUY: future return is at least +2%.
- SELL: future return is at most -2%.
- HOLD: future return falls strictly between -2% and +2%.

Five trading days is a short horizon while allowing moves large enough to distinguish from ordinary daily noise. The symmetric 2% thresholds define a neutral band and will be kept fixed during Core Tier evaluation. They are an explicit project assumption, not a profitability claim.

The target reads prices strictly after date `t`. The final five rows have no realised future return, so their target is missing and they must not enter model fitting or evaluation. Feature columns do not use `future_return` or `target_signal`.
