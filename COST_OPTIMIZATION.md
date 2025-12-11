# Cost Optimization Guide - $20/Month Budget

This guide shows how to run the SEC EDGAR Analytics Platform for **under $20/month**.

## Cost Breakdown (Estimated Monthly)

### ✅ FREE Services (No Cost)
- **BigQuery**: 1 TB queries/month free + 10 GB storage free
- **Cloud Storage**: 5 GB free (Standard class)
- **Cloud Functions**: 2M invocations free, 400K GB-seconds free
- **Cloud Build**: 120 build-minutes/day free

### 💰 Paid Services (Minimal Usage)

| Service | Usage | Cost |
|---------|-------|------|
| Cloud Storage (excess) | ~10 GB | $0.20 |
| BigQuery (excess storage) | ~5 GB | $0.10 |
| Cloud Functions (if exceed free tier) | Occasional | $0-2.00 |
| Dataproc Serverless | 2-3 jobs/week | $3-8.00 |
| Cloud Composer | **DISABLED** | $0.00 |
| **TOTAL** | | **$5-15/month** |

---

## Cost-Saving Configuration

### 1. Disable Cloud Composer (Airflow)
Cloud Composer costs ~$300/month minimum. Instead, use **Cloud Scheduler + Cloud Functions**:

```bash
# Run ingestion weekly instead of daily
gcloud scheduler jobs create http sec-weekly-ingestion \
  --schedule="0 2 * * 0" \
  --uri="https://us-central1-sec-edgar-analytics.cloudfunctions.net/sec-data-ingestion" \
  --http-method=POST
```

### 2. Limit Data Scope
Instead of 2020-2024 (5 years), start with **2023-2024 (2 years)**:
- Reduces storage by 60%
- Reduces processing time by 60%

### 3. Use Dataproc Serverless Sparingly
- Run PySpark jobs **weekly** instead of daily
- Use smallest instance size: `n1-standard-4` (2 workers)
- Set max execution time to 30 minutes

### 4. Optimize BigQuery
- Store only 2 years of data (~5 GB total)
- Partition all tables by year
- Use clustered tables for faster queries
- Disable materialized views auto-refresh (manual refresh weekly)

### 5. Cloud Storage Lifecycle
- Move data to Nearline after 30 days (50% cost reduction)
- Delete raw files after 90 days (keep only processed data)

---

## Implementation Steps

### Step 1: Update terraform.tfvars
```hcl
budget_amount = 20
data_start_year = 2023  # Only 2 years of data
data_end_year = 2024
```

### Step 2: Skip Cloud Composer
Comment out Composer resources in Terraform (already done in modules).

### Step 3: Manual Job Scheduling
Use Cloud Scheduler (free tier: 3 jobs) instead of Airflow:

```bash
# Ingestion job (weekly on Sunday 2 AM)
gcloud scheduler jobs create http sec-ingestion \
  --schedule="0 2 * * 0" \
  --uri="https://us-central1-sec-edgar-analytics.cloudfunctions.net/sec-data-ingestion" \
  --http-method=POST \
  --message-body='{"file_types": ["companyfacts"], "year": 2024}'

# Processing job (weekly on Sunday 3 AM)
gcloud scheduler jobs create http sec-processing \
  --schedule="0 3 * * 0" \
  --uri="https://us-central1-sec-edgar-analytics.cloudfunctions.net/trigger-dataproc" \
  --http-method=POST

# View refresh (weekly on Sunday 4 AM)
gcloud scheduler jobs create http sec-refresh-views \
  --schedule="0 4 * * 0" \
  --uri="https://us-central1-sec-edgar-analytics.cloudfunctions.net/refresh-looker-views" \
  --http-method=POST
```

### Step 4: Monitor Costs Daily
```bash
# Check current month spending
gcloud billing accounts list
gcloud beta billing projects describe sec-edgar-analytics --format="value(billingAccountName)"

# View budget alerts
gcloud billing budgets list --billing-account=YOUR_BILLING_ACCOUNT_ID
```

---

## Free Tier Limits (Stay Within These)

### BigQuery
- ✅ **1 TB queries/month** - We'll use ~50 GB/month (well under limit)
- ✅ **10 GB storage** - We'll use ~5 GB with 2 years of data
- ❌ Streaming inserts NOT free (we use batch loads - free)

### Cloud Storage
- ✅ **5 GB Standard storage** - We'll use ~10 GB (extra $0.20/month)
- ✅ **1 GB Nearline** - Archive old data here
- ✅ **5 GB egress to Americas**

### Cloud Functions
- ✅ **2M invocations/month** - We'll use ~400/month (weekly runs)
- ✅ **400K GB-seconds compute** - Plenty for our use
- ✅ **200K CPU-seconds**

### Dataproc Serverless
- ❌ NO free tier - This is our main cost ($3-8/month)
- Use n1-standard-4 (smallest: $0.16/hour)
- Run for ~30 min/week = 2 hours/month = $0.32/month
- Add Spark overhead: ~$3-5/month total

---

## What You Can Do with $20/Month

✅ **Full Pipeline**:
- Weekly data ingestion from SEC (2023-2024 data)
- PySpark processing on Dataproc Serverless
- BigQuery analytics with 20+ queries
- Looker Studio dashboards (4 dashboards)
- GitHub Actions CI/CD (free for public repos)

✅ **Scalable**:
- Can add more years later if needed
- Can increase processing frequency (daily = ~$20-40/month)
- Can enable Cloud Composer if budget increases

❌ **Limitations**:
- No daily orchestration (weekly only)
- Limited to 2 years of data initially
- Manual job triggers for ad-hoc analysis

---

## Emergency Cost Controls

If spending approaches $20:

1. **Stop Dataproc jobs immediately**:
```bash
gcloud dataproc jobs list --region=us-central1 --filter="status.state=RUNNING" --format="value(reference.jobId)"
gcloud dataproc jobs kill JOB_ID --region=us-central1
```

2. **Disable Cloud Scheduler jobs**:
```bash
gcloud scheduler jobs pause sec-ingestion
gcloud scheduler jobs pause sec-processing
gcloud scheduler jobs pause sec-refresh-views
```

3. **Set hard budget cap** (requires billing admin):
```bash
# This will DISABLE billing if budget exceeded (stops all resources)
gcloud beta billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Hard Cap at $20" \
  --budget-amount=20 \
  --threshold-rule=percent=1.0,basis=current-spend \
  --disable-default-iam-recipients
```

⚠️ **WARNING**: Hard budget cap will shut down the entire project if exceeded. Only use if necessary.

---

## Recommended Starting Configuration

**Budget**: $20/month
**Data Scope**: 2023-2024 (2 years)
**Processing**: Weekly (Sunday 2-4 AM)
**Storage**: 10 GB total
**Expected Cost**: **$5-10/month**
**Buffer**: $10-15 for unexpected usage

This gives you a fully functional SEC analytics platform with room to grow!
