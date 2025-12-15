# SEC Data Ingestion Cloud Function

This Cloud Function downloads SEC EDGAR bulk data files and uploads them to Google Cloud Storage.

## Deployment

The function is already deployed to:
**URL:** `https://us-central1-sec-edgar-analytics.cloudfunctions.net/sec-data-ingestion`

### Redeploy

```bash
gcloud functions deploy sec-data-ingestion \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=ingest_sec_data \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=sec-ingestion-cf-sa@sec-edgar-analytics.iam.gserviceaccount.com \
  --memory=4GB \
  --timeout=540s \
  --env-vars-file=.env.yaml
```

## Usage

### Trigger via HTTP

```bash
# Download companyfacts for 2024
curl -X POST \
  https://us-central1-sec-edgar-analytics.cloudfunctions.net/sec-data-ingestion \
  -H "Content-Type: application/json" \
  -d '{"year": 2024, "file_types": ["companyfacts"]}'

# Download both companyfacts and submissions
curl -X POST \
  https://us-central1-sec-edgar-analytics.cloudfunctions.net/sec-data-ingestion \
  -H "Content-Type: application/json" \
  -d '{"year": 2024, "file_types": ["companyfacts", "submissions"]}'
```

## Files

- `main.py` - Entry point for the Cloud Function
- `config.py` - Configuration dataclasses
- `sec_downloader.py` - SEC API downloader with rate limiting
- `rate_limiter.py` - Token bucket rate limiter (10 req/sec)
- `requirements.txt` - Python dependencies
- `.env.yaml` - Environment variables (NOT committed to git)

## Environment Variables

Create a `.env.yaml` file with:

```yaml
SEC_USER_AGENT: "YourCompany your-email@example.com"
GCP_PROJECT_ID: "your-project-id"
GCS_RAW_BUCKET: "your-raw-bucket-name"
DATA_START_YEAR: "2023"
DATA_END_YEAR: "2024"
LOG_LEVEL: "INFO"
```

## Cost Optimization

**WARNING:** The companyfacts.zip file is ~2GB, requiring 4GB of memory.

To stay under $20/month:
- Run **weekly** (not daily) using Cloud Scheduler
- Consider streaming to GCS instead of loading into memory
- Monitor costs in GCP Console

## Logs

View logs:
```bash
gcloud functions logs read sec-data-ingestion \
  --region=us-central1 \
  --limit=50
```
