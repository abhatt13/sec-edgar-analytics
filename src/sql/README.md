# BigQuery SQL Schema and Analytics

This directory contains BigQuery table definitions and analytical queries for the SEC EDGAR Analytics Platform.

## Directory Structure

```
sql/
├── schema/
│   ├── bronze_tables.sql      # Raw data tables (Bronze layer)
│   ├── silver_tables.sql      # Dimension & fact tables (Silver layer)
│   └── gold_views.sql         # Materialized views for Looker (Gold layer)
└── analytics/
    ├── financial_ratios.sql   # Profitability, liquidity, leverage queries
    ├── peer_comparison.sql    # Benchmarking and sector analysis
    └── timeseries.sql         # Growth trends, TTM, historical analysis
```

## Data Architecture

### Bronze Layer (Raw Data)
- `raw_companies`: Company master data from SEC
- `raw_financials`: All financial facts from XBRL filings with data quality flags

### Silver Layer (Normalized)
**Dimensions:**
- `dim_companies`: Company dimension with filing statistics
- `dim_taxonomy`: US-GAAP concept dimension with usage metrics
- `dim_dates`: Date dimension for temporal analysis

**Facts:**
- `fact_financials`: Partitioned by fiscal_year, clustered by cik/concept/end_date
- `fact_submissions`: Filing-level aggregated metrics

### Gold Layer (Analytics - Looker Optimized)
**Materialized Views (Refreshed Daily):**

1. **looker_company_metrics**
   - Pre-aggregated financials by company/period
   - Income statement, balance sheet, cash flow metrics
   - Optimized for company analysis dashboards

2. **looker_financial_ratios**
   - Calculated ratios (profitability, liquidity, leverage)
   - Gross margin, operating margin, net margin
   - ROA, ROE, current ratio, debt-to-equity
   - Only annual (FY) periods for consistency

3. **looker_peer_comparison**
   - Industry benchmarks and sector averages
   - Percentile rankings by sector
   - Peer group analysis for competitive insights

4. **looker_timeseries**
   - Trailing twelve months (TTM) calculations
   - Year-over-year growth percentages
   - 4-quarter moving averages
   - Quarterly and annual trends

## Deployment

### 1. Set Project ID

```bash
export PROJECT_ID="your-gcp-project-id"
```

### 2. Create Bronze Tables

```bash
# Replace ${PROJECT_ID} in the SQL files
sed "s/\${PROJECT_ID}/$PROJECT_ID/g" schema/bronze_tables.sql > /tmp/bronze_tables.sql

# Execute in BigQuery
bq query --use_legacy_sql=false < /tmp/bronze_tables.sql
```

### 3. Create Silver Tables

```bash
sed "s/\${PROJECT_ID}/$PROJECT_ID/g" schema/silver_tables.sql > /tmp/silver_tables.sql
bq query --use_legacy_sql=false < /tmp/silver_tables.sql
```

### 4. Create Gold Materialized Views

**Important**: Gold views depend on silver tables being populated first.

```bash
sed "s/\${PROJECT_ID}/$PROJECT_ID/g" schema/gold_views.sql > /tmp/gold_views.sql
bq query --use_legacy_sql=false < /tmp/gold_views.sql
```

## Materialized View Refresh

Materialized views refresh automatically every 24 hours (1440 minutes). To manually refresh:

```bash
# Refresh specific view
bq query --use_legacy_sql=false \
  "CALL BQ.REFRESH_MATERIALIZED_VIEW('${PROJECT_ID}.gold_sec.looker_company_metrics')"

# Refresh all gold views
for view in looker_company_metrics looker_financial_ratios looker_peer_comparison looker_timeseries; do
  bq query --use_legacy_sql=false \
    "CALL BQ.REFRESH_MATERIALIZED_VIEW('${PROJECT_ID}.gold_sec.${view}')"
done
```

## Running Analytical Queries

### Financial Ratios Analysis

```bash
sed "s/\${PROJECT_ID}/$PROJECT_ID/g" analytics/financial_ratios.sql > /tmp/financial_ratios.sql
bq query --use_legacy_sql=false < /tmp/financial_ratios.sql
```

### Peer Comparison

```bash
sed "s/\${PROJECT_ID}/$PROJECT_ID/g" analytics/peer_comparison.sql > /tmp/peer_comparison.sql
bq query --use_legacy_sql=false < /tmp/peer_comparison.sql
```

### Time-Series Analysis

```bash
sed "s/\${PROJECT_ID}/$PROJECT_ID/g" analytics/timeseries.sql > /tmp/timeseries.sql
bq query --use_legacy_sql=false < /tmp/timeseries.sql
```

## Query Performance Optimization

### Partitioning
- **Bronze**: `raw_financials` partitioned by `fiscal_year`
- **Silver**: `fact_financials` partitioned by `fiscal_year` (range bucket 2000-2030)
- **Gold**: All materialized views partitioned by `fiscal_year`

### Clustering
- **Bronze**: `raw_financials` clustered by `cik_padded, concept`
- **Silver**:
  - `fact_financials` clustered by `cik, concept, end_date`
  - `fact_submissions` clustered by `cik, filing_date`
- **Gold**: All views clustered by `cik` or `sector`

### Query Best Practices

1. **Always filter by fiscal_year** to leverage partitioning:
   ```sql
   WHERE fiscal_year >= 2020
   ```

2. **Filter by cik early** to benefit from clustering:
   ```sql
   WHERE cik = '0000320193' -- Apple Inc.
   ```

3. **Use materialized views** for Looker queries to reduce cost and latency

4. **Limit row scans** with appropriate WHERE clauses and LIMIT statements

## Common Use Cases

### 1. Company Financial Profile
```sql
SELECT *
FROM `${PROJECT_ID}.gold_sec.looker_company_metrics`
WHERE ticker = 'AAPL' AND fiscal_year = 2023;
```

### 2. Sector Benchmarking
```sql
SELECT *
FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
WHERE sector = 'Technology' AND fiscal_year = 2023
ORDER BY net_margin_percentile DESC;
```

### 3. Growth Trend Analysis
```sql
SELECT *
FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
WHERE ticker = 'MSFT' AND fiscal_year >= 2020
ORDER BY fiscal_year, fiscal_period;
```

### 4. High-Level Metrics
```sql
SELECT *
FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL')
  AND fiscal_year = 2023;
```

## Monitoring

### Check View Refresh Status
```sql
SELECT
  table_name,
  DATE(last_refresh_time) as last_refresh_date,
  refresh_interval_minutes
FROM `${PROJECT_ID}.gold_sec.INFORMATION_SCHEMA.MATERIALIZED_VIEWS`;
```

### Table Sizes
```sql
SELECT
  table_name,
  ROUND(size_bytes / POW(10,9), 2) as size_gb,
  row_count
FROM `${PROJECT_ID}.silver_sec.__TABLES__`
ORDER BY size_bytes DESC;
```

### Query Costs (Last 7 Days)
```sql
SELECT
  DATE(creation_time) as query_date,
  user_email,
  SUM(total_bytes_billed) / POW(10,12) as tb_billed,
  ROUND(SUM(total_bytes_billed) / POW(10,12) * 5, 2) as estimated_cost_usd
FROM `${PROJECT_ID}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND statement_type = 'SELECT'
GROUP BY query_date, user_email
ORDER BY query_date DESC;
```

## Troubleshooting

### View refresh fails
- Check that source tables have data
- Verify IAM permissions for the service account
- Review BigQuery logs for specific errors

### Queries are slow
- Ensure partitioning and clustering are being used
- Check if you're selecting `SELECT *` on large tables
- Use EXPLAIN to analyze query execution plan

### High costs
- Review most expensive queries in INFORMATION_SCHEMA.JOBS
- Ensure Looker is using materialized views, not raw tables
- Set up cost controls and budget alerts

## Next Steps

1. Populate bronze tables with PySpark jobs
2. Create silver dimension and fact tables
3. Wait for initial data load to complete
4. Create and refresh gold materialized views
5. Connect Looker Studio to gold views
6. Set up scheduled refresh via Airflow

## Documentation

- Column descriptions are embedded in table schemas
- Use `INFORMATION_SCHEMA` to explore metadata
- Check BigQuery console for table/view documentation
