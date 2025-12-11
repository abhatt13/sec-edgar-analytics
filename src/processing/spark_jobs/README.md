# PySpark Jobs for SEC EDGAR Processing

This directory contains PySpark jobs that process SEC EDGAR XBRL data and create normalized tables in BigQuery.

## Jobs Overview

### 1. parse_xbrl.py
Parses XBRL JSON from companyfacts.zip and creates raw bronze tables.

**Input**: `gs://bucket/bulk/companyfacts.zip`
**Output**:
- `bronze_sec.raw_companies`
- `bronze_sec.raw_financials`

**Features**:
- Extracts company information (CIK, name, ticker)
- Flattens nested US-GAAP taxonomy facts
- Categorizes concepts by financial statement type
- Applies data quality validations
- Handles multiple units (USD, shares, pure)
- Filters to valid forms (10-K, 10-Q, etc.)

### 2. create_dimensions.py
Creates dimension tables in the silver layer.

**Input**: Bronze tables
**Output**:
- `silver_sec.dim_companies`
- `silver_sec.dim_taxonomy`
- `silver_sec.dim_dates`

**Features**:
- Company dimension with filing statistics
- Taxonomy dimension with usage metrics
- Date dimension with calendar attributes

### 3. create_facts.py
Creates fact tables in the silver layer with partitioning and clustering.

**Input**: Bronze tables
**Output**:
- `silver_sec.fact_financials` (partitioned by fiscal_year, clustered by cik/concept/end_date)
- `silver_sec.fact_submissions`

**Features**:
- Deduplication logic (keeps most recent filing)
- Surrogate key generation
- Partitioning for query performance
- Clustering for common access patterns

## Configuration

Set these environment variables:

```bash
export GCP_PROJECT_ID="your-project-id"
export GCS_RAW_BUCKET="sec-edgar-raw-data"
export GCS_PROCESSED_BUCKET="sec-edgar-processed-data"
export BQ_BRONZE_DATASET="bronze_sec"
export BQ_SILVER_DATASET="silver_sec"
export BQ_GOLD_DATASET="gold_sec"
```

## Running Locally (for testing)

### Prerequisites
```bash
pip install pyspark
pip install google-cloud-bigquery-storage
```

### Run parse_xbrl.py
```bash
spark-submit \
  --packages com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2 \
  parse_xbrl.py \
  gs://your-bucket/bulk/companyfacts.zip \
  bronze_sec
```

### Run create_dimensions.py
```bash
spark-submit \
  --packages com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2 \
  create_dimensions.py \
  bronze_sec \
  silver_sec
```

### Run create_facts.py
```bash
spark-submit \
  --packages com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2 \
  create_facts.py \
  bronze_sec \
  silver_sec
```

## Running on Dataproc Serverless

### Upload jobs to GCS
```bash
gsutil cp *.py gs://your-bucket/spark-jobs/
```

### Submit parse_xbrl job
```bash
gcloud dataproc batches submit pyspark \
  gs://your-bucket/spark-jobs/parse_xbrl.py \
  --region=us-central1 \
  --batch=sec-parse-xbrl-$(date +%s) \
  --service-account=sec-dataproc-sa@PROJECT.iam.gserviceaccount.com \
  --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.32.2.jar \
  -- gs://your-bucket/bulk/companyfacts.zip bronze_sec
```

### Submit create_dimensions job
```bash
gcloud dataproc batches submit pyspark \
  gs://your-bucket/spark-jobs/create_dimensions.py \
  --region=us-central1 \
  --batch=sec-create-dimensions-$(date +%s) \
  --service-account=sec-dataproc-sa@PROJECT.iam.gserviceaccount.com \
  --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.32.2.jar \
  -- bronze_sec silver_sec
```

### Submit create_facts job
```bash
gcloud dataproc batches submit pyspark \
  gs://your-bucket/spark-jobs/create_facts.py \
  --region=us-central1 \
  --batch=sec-create-facts-$(date +%s) \
  --service-account=sec-dataproc-sa@PROJECT.iam.gserviceaccount.com \
  --jars=gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.32.2.jar \
  -- bronze_sec silver_sec
```

## Data Quality Checks

All jobs implement quality checks:

- **Null validation**: Critical fields must not be null
- **Fiscal year validation**: Must be between 1900-2100
- **Deduplication**: Handles duplicate facts from amendments
- **Unit filtering**: Only processes USD, shares, and pure units
- **Form filtering**: Only processes 10-K, 10-Q, 8-K, 20-F, 40-F

Quality metrics are logged for each run.

## Performance Optimization

- **Partitioning**: Tables partitioned by fiscal_year for efficient time-based queries
- **Clustering**: Tables clustered by cik/concept/date for common access patterns
- **Caching**: Intermediate DataFrames cached when reused
- **Direct write**: Uses BigQuery Storage Write API for faster loads

## US-GAAP Concepts Processed

### Income Statement
- Revenues, CostOfRevenue, GrossProfit
- OperatingIncomeLoss, NetIncomeLoss
- EarningsPerShareBasic, EarningsPerShareDiluted
- OperatingExpenses, R&D, SG&A

### Balance Sheet
- Assets, AssetsCurrent, AssetsNoncurrent
- CashAndCashEquivalents, AccountsReceivable, Inventory
- Liabilities, StockholdersEquity, RetainedEarnings

### Cash Flow
- NetCashProvidedByUsedInOperatingActivities
- NetCashProvidedByUsedInInvestingActivities
- NetCashProvidedByUsedInFinancingActivities
- CapEx, Dividends, Debt Issuance/Repayment

## Troubleshooting

### Out of memory errors
Increase executor memory:
```bash
--conf spark.executor.memory=8g
--conf spark.driver.memory=4g
```

### BigQuery write errors
Check service account permissions:
- `roles/bigquery.dataEditor`
- `roles/bigquery.jobUser`

### Missing data
Check data quality flags in output tables:
- `data_quality_passed` column
- `has_null_critical` column
- `invalid_fiscal_year` column

## Next Steps

After running these jobs:
1. Verify table counts in BigQuery
2. Run BigQuery schema creation (sql/schema/)
3. Create gold layer analytics views
4. Set up Airflow DAG for orchestration
