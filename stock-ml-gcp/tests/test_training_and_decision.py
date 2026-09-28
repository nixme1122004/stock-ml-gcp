import pandas as pd
from src.models.decision import backtest, decide
from src.models.training import chronological_split

def test_chronological_split_has_no_date_overlap():
    df = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=10), "x": range(10)})
    train, validation, test = chronological_split(df, .6, .2)
    assert train.Date.max() < validation.Date.min() < test.Date.min()

def test_decision_boundaries_and_backtest():
    assert decide("BUY", .45) == "BUY" and decide("SELL", .44) == "HOLD"
    result = backtest(pd.Series([100., 110., 120.]), ["BUY", "HOLD", "SELL"], transaction_cost=0)
    assert result["final_value"] == 12000
