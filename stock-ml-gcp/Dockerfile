FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY artifacts ./artifacts
COPY data/processed ./data/processed
COPY reports ./reports
CMD ["sh", "-c", "streamlit run app/dashboard.py --server.address=0.0.0.0 --server.port=${PORT:-8080}"]
