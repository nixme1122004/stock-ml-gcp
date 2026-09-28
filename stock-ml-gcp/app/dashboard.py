"""Streamlit dashboard for the trained stock-direction model."""
from pathlib import Path
import json
import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
@st.cache_resource
def load_artifact(): return joblib.load(ROOT / "artifacts" / "logistic_regression.joblib")

st.set_page_config(page_title="Stock ML Signals", layout="wide")
st.title("AAPL and MSFT Direction Signals")
artifact = load_artifact()
files = sorted((ROOT / "data" / "processed").glob("*_labelled.csv"))
if not files:
    st.error("No labelled feature data is packaged with this deployment."); st.stop()
symbol = st.selectbox("Stock", sorted({path.name.split("_")[0] for path in files}))
data = pd.read_csv(next(path for path in files if path.name.startswith(f"{symbol}_")))
features = artifact["features"]
eligible = data.dropna(subset=features)
latest = eligible.iloc[[-1]]
probabilities = artifact["model"].predict_proba(latest[features])[0]
classes = artifact["model"].classes_
prediction = classes[probabilities.argmax()]
confidence = float(probabilities.max())
signal = prediction if prediction in {"BUY", "SELL"} and confidence >= 0.45 else "HOLD"
col1, col2, col3 = st.columns(3)
col1.metric("Latest model class", prediction)
col2.metric("Decision signal", signal)
col3.metric("Confidence", f"{confidence:.1%}")
st.subheader("Class probabilities")
st.bar_chart(pd.DataFrame({"probability": probabilities}, index=classes))
st.subheader("Recent labelled outcomes")
st.dataframe(data[["Date", "Close", "future_return", "target_signal"]].tail(20), use_container_width=True)
metrics_path = ROOT / "reports" / "model_metrics.json"
if metrics_path.exists():
    st.subheader("Evaluation summary")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    st.json(metrics["models"]["logistic_regression"]["test"])
