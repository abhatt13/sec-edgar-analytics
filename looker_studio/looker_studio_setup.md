# Looker Studio Setup Guide

Step-by-step guide to set up Looker Studio dashboards for SEC EDGAR Analytics.

## Prerequisites

- ✅ BigQuery datasets populated (bronze, silver, gold)
- ✅ Materialized views created and refreshed
- ✅ GCP service account with BigQuery permissions
- ✅ Google account for Looker Studio access

---

## Step 1: Service Account Setup

### 1.1 Verify Service Account Exists

```bash
gcloud iam service-accounts list --filter="email:sec-looker-sa@*"
```

If not created, the Terraform infrastructure should have created it. Otherwise:

```bash
gcloud iam service-accounts create sec-looker-sa \
  --display-name="SEC Looker Studio Service Account"
```

### 1.2 Grant BigQuery Permissions

```bash
PROJECT_ID="your-project-id"

# BigQuery Data Viewer
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sec-looker-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

# BigQuery Job User (required for query execution)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:sec-looker-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### 1.3 Create Service Account Key

```bash
gcloud iam service-accounts keys create ~/looker-sa-key.json \
  --iam-account=sec-looker-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

**⚠️ Important**: Store this key securely. You'll upload it to Looker Studio.

---

## Step 2: Connect BigQuery to Looker Studio

### 2.1 Access Looker Studio

1. Go to https://lookerstudio.google.com/
2. Sign in with your Google account
3. Click **"Create"** → **"Data Source"**

### 2.2 Select BigQuery Connector

1. Search for **"BigQuery"** in the connector list
2. Click **"BigQuery"** connector

### 2.3 Authorize with Service Account

1. Click **"AUTHORIZE"** button
2. Select **"Service Account"** tab
3. Upload the `looker-sa-key.json` file
4. Click **"Connect"**

### 2.4 Select Dataset

1. **Project**: Select your GCP project
2. **Dataset**: Select `gold_sec`
3. **Table**: Select `looker_company_metrics`
4. Click **"CONNECT"** (top-right)

### 2.5 Configure Fields

The schema will auto-detect. Verify:
- **Dimension fields** (green): cik, company_name, ticker, sector, fiscal_year, fiscal_period
- **Metric fields** (blue): revenue, net_income, total_assets, etc.

**Field Type Corrections** (if needed):
- Ensure `fiscal_year` is set as **Dimension** (not Metric)
- Ensure currency fields have **Type**: Number, **Default Aggregation**: Sum

Click **"CREATE REPORT"** to save the data source.

### 2.6 Create Additional Data Sources

Repeat steps 2.3-2.5 for:
- `gold_sec.looker_financial_ratios`
- `gold_sec.looker_peer_comparison`
- `gold_sec.looker_timeseries`

**Tip**: Name each data source clearly:
- "SEC Company Metrics"
- "SEC Financial Ratios"
- "SEC Peer Comparison"
- "SEC Time Series"

---

## Step 3: Create Dashboard 1 - Executive Summary

### 3.1 Create New Report

1. Go to https://lookerstudio.google.com/
2. Click **"Create"** → **"Report"**
3. Select **"SEC Company Metrics"** data source
4. Click **"ADD TO REPORT"**

### 3.2 Add Scorecards (Top Row)

**Scorecard 1: Total Companies**
1. Click **"Add a chart"** → **"Scorecard"**
2. Drag to top-left of canvas
3. **Data**:
   - Metric: `cik` (change aggregation to COUNT DISTINCT)
4. **Style**:
   - Metric name: "Total Companies"
   - Font size: Large
   - Compact numbers: Off

**Scorecard 2: Total Revenue**
1. Add another Scorecard next to the first
2. **Data**:
   - Metric: `revenue` (SUM)
3. **Style**:
   - Metric name: "Total Revenue (Latest Year)"
   - Prefix: "$"
   - Suffix: "B" (if displaying in billions)

**Scorecard 3: Avg Profit Margin**
1. Add Scorecard
2. **Data**:
   - Metric: Create calculated field:
     ```
     (SUM(net_income) / SUM(revenue)) * 100
     ```
   - Name: "Avg Profit Margin %"
3. **Style**:
   - Suffix: "%"

Repeat for the 4th scorecard (Companies with Positive Growth).

### 3.3 Add Revenue Trend Line Chart

1. **Add a chart** → **"Time series chart"**
2. Drag to center-left area
3. **Data**:
   - Date Dimension: Create calculated field combining `fiscal_year` and `fiscal_period`
   - Metric: `revenue` (SUM)
4. **Style**:
   - Title: "Revenue Trend (Quarterly)"
   - Show data labels: On
   - Line color: #1A73E8 (blue)

### 3.4 Add Top 25 Companies Bar Chart

1. **Add a chart** → **"Bar chart"**
2. **Data**:
   - Dimension: `company_name` (or `ticker`)
   - Metric: `revenue` (SUM)
   - Sort: revenue DESC
   - Rows: 25
3. **Filter**: Add filter `fiscal_period = "FY"` and `fiscal_year = MAX(fiscal_year)`
4. **Style**:
   - Orientation: Horizontal
   - Color: Gradient (blue)

### 3.5 Add Sector Distribution Pie Chart

1. **Add a chart** → **"Pie chart"**
2. **Data**:
   - Dimension: Change data source to "SEC Financial Ratios" → `sector`
   - Metric: `cik` (COUNT DISTINCT)
3. **Style**:
   - Show labels: Percentage + Value
   - Donut chart: Optional

### 3.6 Add Profitability Table

1. **Add a chart** → **"Table"**
2. **Data**:
   - Dimension: `sector`
   - Metrics: `gross_margin_pct`, `operating_margin_pct`, `net_profit_margin_pct`, `return_on_equity_pct` (all AVG)
3. **Style**:
   - Conditional formatting on all metric columns:
     - Green if > sector 75th percentile
     - Yellow if between 25-75th percentile
     - Red if < 25th percentile

### 3.7 Add Global Filters

1. **Add a control** → **"Drop-down list"**
2. **Control field**: `fiscal_year`
3. Position at top of dashboard
4. **Style**: Multi-select allowed

Repeat for `sector` filter.

### 3.8 Style and Layout

1. **Theme**: Click **"Theme and layout"** → Select "Simple Dark" or "Corporate"
2. **Page size**: Fixed (1600 x 900) or Auto-fit
3. **Background**: White (#FFFFFF)
4. **Title**: Add text box "SEC EDGAR Executive Dashboard" at the top

---

## Step 4: Create Dashboard 2 - Company Deep Dive

### 4.1 Create New Report

Follow step 3.1 to create a new report.

### 4.2 Add Company Parameter

1. **Resource** menu → **"Manage filters"**
2. **Create a filter**:
   - Name: "Selected Company"
   - Field: `cik` or `ticker`
   - Type: "Include"
   - Filter type: "Control field parameter"
3. This allows users to select a company

### 4.3 Add Company Header Card

1. Add a **Scorecard** showing `company_name`
2. Add several small scorecards below showing:
   - Ticker
   - Sector
   - Latest Revenue
   - Latest Net Income

All scorecards should use the company filter.

### 4.4 Add Financial Statement Table

1. **Add a chart** → **"Pivot table"**
2. **Data**:
   - Row dimension: Create calculated field for line items (e.g., "Revenue", "Cost of Revenue", etc.)
   - Column dimension: `fiscal_year`
   - Metric: Respective metric value
3. **Filter**: Apply "Selected Company" filter

**Pro Tip**: You may need to create separate tables for Income Statement, Balance Sheet, and Cash Flow, or use **tabs** with different table pages.

### 4.5 Add Quarterly Trends Chart

1. **Add a chart** → **Time series with multiple metrics**
2. Change data source to "SEC Time Series"
3. **Data**:
   - Date: Combine `fiscal_year` + `fiscal_period`
   - Metrics: `revenue`, `net_income`, `operating_cash_flow`
4. **Filter**: Selected company

### 4.6 Add Peer Comparison Table

1. Change data source to "SEC Peer Comparison"
2. Add **Table** chart
3. **Dimensions**: `company_name`
4. **Metrics**: All ratio fields
5. **Filter**: Same sector as selected company
6. **Conditional formatting**: Highlight selected company row

---

## Step 5: Create Dashboard 3 - Peer Comparison

### 5.1 Create Heatmap Table

1. New report with "SEC Peer Comparison" data source
2. **Add a chart** → **"Heatmap table"** (if available) or **"Table with conditional formatting"**
3. **Rows**: `company_name`
4. **Columns**: Multiple metric fields
5. **Style**: Apply color scale (Red-Yellow-Green) based on percentile values

### 5.2 Add Scatter Plot

1. **Add a chart** → **"Scatter chart"**
2. Change data source to "SEC Financial Ratios"
3. **X-axis**: `return_on_equity_pct`
4. **Y-axis**: `net_profit_margin_pct`
5. **Bubble size**: `revenue`
6. **Bubble color**: `sector`

### 5.3 Add Sector Filter

Add drop-down filter for `sector` at the top.

---

## Step 6: Create Dashboard 4 - Industry Analysis

### 6.1 Sector Performance Chart

1. **Add a chart** → **"Column chart"**
2. **Data source**: "SEC Financial Ratios"
3. **Dimension**: `sector`
4. **Metrics**: `gross_margin_pct`, `operating_margin_pct`, `net_profit_margin_pct` (all AVG)
5. **Style**: Grouped columns

### 6.2 Treemap for Market Share

1. **Add a chart** → **"Treemap"**
2. **Data source**: "SEC Company Metrics"
3. **Dimension**: `sector` (level 1), `company_name` (level 2)
4. **Size**: `revenue` (SUM)
5. **Color**: `net_profit_margin_pct` (AVG)

### 6.3 Trend Lines by Sector

1. **Add a chart** → **"Time series"**
2. **Data source**: "SEC Time Series"
3. **Date**: Fiscal quarter
4. **Metric**: `revenue` (SUM)
5. **Breakdown**: `sector`
6. **Style**: One line per sector

---

## Step 7: Sharing and Permissions

### 7.1 Share Dashboard

1. Click **"Share"** button (top-right)
2. **Get shareable link**: Copy link
3. **Invite people**: Add email addresses
4. **Permission level**:
   - **Viewer**: Can view only
   - **Editor**: Can modify dashboard

### 7.2 Embed in Website (Optional)

1. Click **"File"** → **"Embed report"**
2. Copy the embed code
3. Adjust width/height as needed

### 7.3 Schedule Email Delivery

1. Click **"Schedule delivery"** icon
2. **Frequency**: Daily, Weekly, Monthly
3. **Recipients**: Email addresses
4. **Format**: PDF or Link
5. **Time**: Select delivery time

---

## Step 8: Maintenance and Optimization

### 8.1 Performance Tips

- Use **materialized views** instead of raw tables
- Apply **pre-filters** to reduce data scanned
- Avoid `SELECT *` - choose specific fields
- Use **date range filters** to limit data
- **Cache** data for faster loading

### 8.2 Refresh Data

Looker Studio caches data. To force refresh:
1. **Resource** menu → **"Manage added data sources"**
2. Select data source → **"REFRESH FIELDS"**

Or:
- Set **"Data freshness"** to 1 hour (auto-refresh)

### 8.3 Monitor Usage

Check BigQuery query logs to see dashboard query patterns:
```sql
SELECT
  user_email,
  query,
  total_bytes_billed / POW(10,9) as gb_billed,
  ROUND(total_bytes_billed / POW(10,12) * 5, 2) as cost_usd
FROM `PROJECT_ID.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
WHERE job_type = 'QUERY'
  AND statement_type = 'SELECT'
  AND creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND user_email LIKE '%looker%'
ORDER BY total_bytes_billed DESC
LIMIT 100;
```

---

## Troubleshooting

### "Access Denied" Errors
- Verify service account has `bigquery.dataViewer` and `bigquery.jobUser` roles
- Check that data source is authorized properly

### Slow Dashboard Performance
- Use materialized views (gold layer) instead of fact tables
- Add filters to reduce data scanned
- Partition and cluster BigQuery tables
- Use aggregated data sources

### Charts Not Showing Data
- Check filters - they might be excluding all data
- Verify field types (Dimension vs Metric)
- Ensure data exists in BigQuery tables

### Incorrect Metrics
- Check aggregation type (SUM vs AVG vs COUNT)
- Verify calculated fields
- Check for NULL values affecting calculations

---

## Next Steps

1. ✅ Set up all 4 dashboards
2. ✅ Share with stakeholders
3. ✅ Set up scheduled email delivery
4. ✅ Monitor query costs
5. ✅ Gather user feedback
6. ✅ Iterate and improve visualizations

For detailed dashboard specifications, see `dashboard_specs.md`.
