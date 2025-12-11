# Airflow DAGs for SEC EDGAR Analytics

This directory contains Apache Airflow DAGs and custom operators for orchestrating the SEC EDGAR data pipeline.

## DAG Overview

### sec_edgar_pipeline.py

Main orchestration DAG that runs the complete end-to-end pipeline:

**Schedule**: Daily at 2 AM EST (7 AM UTC)
**Max Active Runs**: 1 (prevents overlapping executions)
**Retries**: 3 attempts with 5-minute delay
**Timeout**: 4 hours

**Pipeline Stages**:

1. **Check SEC Updates** (Python)
   - Determines if new data is available
   - Returns execution metadata

2. **Data Ingestion** (Cloud Functions + GCS Sensors)
   - Download companyfacts.zip
   - Download submissions.zip
   - Verify uploads to GCS

3. **Data Processing** (Dataproc Serverless)
   - Parse XBRL data → bronze tables
   - Create dimension tables → silver layer
   - Create fact tables → silver layer

4. **Data Quality Validation** (BigQuery)
   - Row count checks
   - Null value validation
   - Fiscal year range check
   - Data quality flag verification (>95% pass rate)

5. **Refresh Looker Views** (BigQuery)
   - Refresh looker_company_metrics
   - Refresh looker_financial_ratios
   - Refresh looker_peer_comparison
   - Refresh looker_timeseries

6. **Send Notification** (Email)
   - Success email with pipeline summary

## Custom Operators

### BigQueryDataQualityOperator

Executes multiple data quality checks against BigQuery tables.

**Usage**:
```python
quality_checks = BigQueryDataQualityOperator(
    task_id="run_quality_checks",
    project_id=PROJECT_ID,
    dataset_id="silver_sec",
    table_id="fact_financials",
    quality_checks=[
        {
            "name": "null_check",
            "sql": "SELECT COUNT(*) = 0 FROM table WHERE critical_field IS NULL"
        },
    ],
)
```

### LookerMaterializedViewRefreshOperator

Refreshes BigQuery materialized views and returns metadata.

**Usage**:
```python
refresh_view = LookerMaterializedViewRefreshOperator(
    task_id="refresh_metrics",
    project_id=PROJECT_ID,
    dataset_id="gold_sec",
    view_id="looker_company_metrics",
)
```

## Setup

### 1. Deploy to Cloud Composer

**Create Composer Environment**:
```bash
gcloud composer environments create sec-edgar-airflow \
  --location us-central1 \
  --python-version 3 \
  --machine-type n1-standard-4 \
  --node-count 3 \
  --service-account sec-composer-sa@PROJECT_ID.iam.gserviceaccount.com
```

**Upload DAGs**:
```bash
# Get the DAGs folder location
DAGS_FOLDER=$(gcloud composer environments describe sec-edgar-airflow \
  --location us-central1 \
  --format="value(config.dagGcsPrefix)")

# Upload DAGs and operators
gsutil -m rsync -r airflow/dags/ ${DAGS_FOLDER}/
```

### 2. Set Airflow Variables

```bash
gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  variables set -- \
  gcp_project_id YOUR_PROJECT_ID

gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  variables set -- \
  gcp_region us-central1

gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  variables set -- \
  gcs_raw_bucket sec-edgar-dev-raw-data-PROJECT_ID

gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  variables set -- \
  gcs_processed_bucket sec-edgar-dev-processed-data-PROJECT_ID

gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  variables set -- \
  notification_email your-email@example.com
```

### 3. Install Python Dependencies

Create `requirements.txt` for Composer:
```bash
cat > composer-requirements.txt << EOF
apache-airflow-providers-google==10.11.1
pyyaml==6.0.1
EOF

gcloud composer environments update sec-edgar-airflow \
  --location us-central1 \
  --update-pypi-packages-from-file composer-requirements.txt
```

### 4. Configure Email Notifications

**Set SMTP settings** in Composer environment variables:
```bash
gcloud composer environments update sec-edgar-airflow \
  --location us-central1 \
  --update-env-variables \
  AIRFLOW__EMAIL__EMAIL_BACKEND=airflow.utils.email.send_email_smtp,\
  AIRFLOW__SMTP__SMTP_HOST=smtp.gmail.com,\
  AIRFLOW__SMTP__SMTP_STARTTLS=True,\
  AIRFLOW__SMTP__SMTP_SSL=False,\
  AIRFLOW__SMTP__SMTP_PORT=587,\
  AIRFLOW__SMTP__SMTP_MAIL_FROM=your-email@gmail.com
```

**Add SMTP credentials to Secret Manager**:
```bash
echo -n "your-email@gmail.com" | gcloud secrets create smtp-user --data-file=-
echo -n "your-app-password" | gcloud secrets create smtp-password --data-file=-
```

## Running the DAG

### Manual Trigger

```bash
# Trigger via CLI
gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  dags trigger -- sec_edgar_pipeline

# Trigger with execution date
gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  dags trigger -- sec_edgar_pipeline --exec-date 2024-01-15
```

### View DAG in Airflow UI

```bash
# Get Airflow web UI URL
gcloud composer environments describe sec-edgar-airflow \
  --location us-central1 \
  --format="value(config.airflowUri)"
```

Navigate to the URL and:
1. Find `sec_edgar_pipeline` DAG
2. Toggle ON to enable scheduling
3. Click "Trigger DAG" for manual run

## Monitoring

### Check DAG Status

```bash
gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  dags list-runs -- -d sec_edgar_pipeline --state running
```

### View Task Logs

```bash
gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  tasks logs -- sec_edgar_pipeline parse_xbrl_data 2024-01-15
```

### Check Task Instance Status

```bash
gcloud composer environments run sec-edgar-airflow \
  --location us-central1 \
  tasks state -- sec_edgar_pipeline parse_xbrl_data 2024-01-15
```

## Troubleshooting

### DAG Not Appearing in UI
- Check that files are uploaded to the correct GCS bucket
- Verify Python syntax: `python airflow/dags/sec_edgar_pipeline.py`
- Check Airflow scheduler logs in Composer

### Import Errors
- Ensure custom operators are in the `operators/` subdirectory
- Verify `__init__.py` files exist in all directories
- Check that dependencies are installed in Composer environment

### Task Failures
- Review task logs in Airflow UI
- Check service account permissions
- Verify GCS paths and BigQuery table names
- Ensure Dataproc jobs have correct JAR dependencies

### Email Notifications Not Working
- Verify SMTP settings in environment variables
- Check that email address is valid
- Test with a simple EmailOperator task

## Performance Optimization

### Parallelize Independent Tasks
Tasks within task groups run in parallel when possible:
- `download_companyfacts` and `download_submissions` (parallel)
- `create_dimensions` and `create_facts` (parallel after parse_xbrl)
- All 4 materialized view refreshes (parallel)

### Resource Allocation
Adjust Composer environment based on workload:
```bash
gcloud composer environments update sec-edgar-airflow \
  --location us-central1 \
  --node-count 5 \
  --machine-type n1-standard-8
```

### Task Execution Timeout
Configure per-task timeouts in DAG:
```python
task = SomeOperator(
    task_id="long_running_task",
    execution_timeout=timedelta(hours=2),
)
```

## Best Practices

1. **Test in Dev First**: Always test DAG changes in development Composer environment
2. **Use Variables**: Store configuration in Airflow Variables, not hardcoded
3. **Monitor Costs**: Composer can be expensive; use appropriate sizing
4. **Version Control**: All DAG changes should go through Git
5. **Document Changes**: Update this README when modifying DAGs
6. **Idempotency**: Ensure tasks can be safely retried
7. **Data Validation**: Always include quality checks before downstream tasks

## Cost Optimization

- Use `schedule_interval=None` during development
- Scale down Composer environment when not in use
- Use Dataproc Serverless (no persistent clusters)
- Set appropriate task timeouts to prevent runaway costs

## Next Steps

1. Upload DAGs to Composer environment
2. Set all required Airflow variables
3. Configure email notifications
4. Test DAG with manual trigger
5. Monitor first few scheduled runs
6. Set up alerts for DAG failures
