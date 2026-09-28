"""Rule-based conversion from model output to portfolio signals."""
from __future__ import annotations
import numpy as np

def decide(predicted_class: str, probability: float, confidence_threshold: float = 0.45) -> str:
    """Return HOLD unless a directional class exceeds configured confidence."""
    if predicted_class in {"BUY", "SELL"} and probability >= confidence_threshold: return predicted_class
    return "HOLD"

def backtest(close, signals, starting_capital: float = 10_000, transaction_cost: float = .001):
    """Long-only next-bar strategy; SELL/HOLD stay in cash, with transaction costs."""
    capital, position = starting_capital, 0.0; values = []
    for price, signal in zip(close, signals):
        if signal == "BUY" and position == 0: position = capital * (1 - transaction_cost) / price; capital = 0
        elif signal == "SELL" and position > 0: capital = position * price * (1 - transaction_cost); position = 0
        values.append(capital + position * price)
    if position > 0: capital = position * close.iloc[-1] * (1 - transaction_cost)
    return {"final_value": capital, "return": capital / starting_capital - 1, "equity_curve": values}
