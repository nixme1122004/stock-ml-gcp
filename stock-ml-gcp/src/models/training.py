"""Chronological model training and evaluation."""
from __future__ import annotations
import json
from pathlib import Path
import joblib
import pandas as pd
import yaml
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

LABELS = ["BUY", "HOLD", "SELL"]

def chronological_split(df: pd.DataFrame, train_fraction: float, validation_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split by unique dates so no later observation enters training."""
    ordered = df.sort_values("Date").reset_index(drop=True)
    dates = ordered["Date"].drop_duplicates().tolist()
    train_end = dates[int(len(dates) * train_fraction) - 1]
    val_end = dates[int(len(dates) * (train_fraction + validation_fraction)) - 1]
    return (ordered[ordered.Date <= train_end], ordered[(ordered.Date > train_end) & (ordered.Date <= val_end)], ordered[ordered.Date > val_end])

def metrics(y_true: pd.Series, predicted: pd.Series) -> dict:
    precision, recall, f1, support = precision_recall_fscore_support(y_true, predicted, labels=LABELS, zero_division=0)
    return {"accuracy": accuracy_score(y_true, predicted), "confusion_matrix": confusion_matrix(y_true, predicted, labels=LABELS).tolist(), "classes": {label: {"precision": float(p), "recall": float(r), "f1": float(f), "support": int(s)} for label, p, r, f, s in zip(LABELS, precision, recall, f1, support)}}

def train_all(config_path: Path = Path("configs/config.yaml")) -> dict:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")); root = config_path.parent.parent
    paths = sorted((root / config["data"]["processed_layer"]).glob("*_labelled.csv"))
    frames = [pd.read_csv(path).assign(symbol=path.name.split("_")[0]) for path in paths]
    if not frames: raise FileNotFoundError("Run feature and target stages first.")
    columns = config["features"]["model_columns"]
    df = pd.concat(frames, ignore_index=True); df["Date"] = pd.to_datetime(df.Date, utc=True)
    df = df.dropna(subset=[*columns, "target_signal"]).sort_values("Date")
    train, validation, test = chronological_split(df, config["split"]["train_fraction"], config["split"]["validation_fraction"])
    x_train, y_train = train[columns], train.target_signal
    models = {"logistic_regression": Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1000, random_state=config["models"]["random_seed"]))]), "random_forest": RandomForestClassifier(n_estimators=config["models"]["random_forest"]["n_estimators"], min_samples_leaf=config["models"]["random_forest"]["min_samples_leaf"], random_state=config["models"]["random_seed"], n_jobs=-1)}
    report = {"periods": {"train": [str(train.Date.min()), str(train.Date.max())], "validation": [str(validation.Date.min()), str(validation.Date.max())], "test": [str(test.Date.min()), str(test.Date.max())]}, "models": {}}
    artifacts = root / "artifacts"; artifacts.mkdir(exist_ok=True)
    for name, model in models.items():
        model.fit(x_train, y_train)
        val_pred = model.predict(validation[columns]); test_pred = model.predict(test[columns])
        report["models"][name] = {"validation": metrics(validation.target_signal, val_pred), "test": metrics(test.target_signal, test_pred)}
        joblib.dump({"model": model, "features": columns}, artifacts / f"{name}.joblib")
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / "model_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

if __name__ == "__main__":
    print(json.dumps(train_all(), indent=2))
