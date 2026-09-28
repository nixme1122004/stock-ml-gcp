# Cloud Run Deployment

Deployment target: project `nifty-stocks-pipeline`, region `asia-south1` (Mumbai), service `stock-ml-dashboard`.

The Streamlit dashboard and selected Logistic Regression artifact are packaged in one Cloud Run container. Training is not performed at startup.

```powershell
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
gcloud builds submit --tag asia-south1-docker.pkg.dev/nifty-stocks-pipeline/stock-ml/stock-ml-dashboard:v1
gcloud run deploy stock-ml-dashboard --image asia-south1-docker.pkg.dev/nifty-stocks-pipeline/stock-ml/stock-ml-dashboard:v1 --region asia-south1 --project nifty-stocks-pipeline --no-allow-unauthenticated --memory 1Gi --max-instances 2
```

The deployer must have Cloud Run Developer, Service Account User, and Artifact Registry Reader permissions. Make the service public only for an intentional portfolio demo by replacing `--no-allow-unauthenticated` with `--allow-unauthenticated`.
