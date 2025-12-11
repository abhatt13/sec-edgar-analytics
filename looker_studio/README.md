# Looker Studio Dashboards

Interactive business intelligence dashboards for SEC EDGAR financial analytics, built with Looker Studio (formerly Google Data Studio) and connected to BigQuery.

## Overview

This directory contains specifications and setup guides for 4 production Looker Studio dashboards:

1. **Executive Summary** - High-level KPIs and trends
2. **Company Deep Dive** - Detailed single-company analysis
3. **Peer Comparison** - Benchmarking and sector analysis
4. **Industry Analysis** - Market-wide trends and patterns

## Files

- **`dashboard_specs.md`**: Complete specifications for all dashboards including:
  - Layout and component details
  - Chart types and configurations
  - Filter specifications
  - Color schemes and styling
  - Performance targets

- **`looker_studio_setup.md`**: Step-by-step setup guide including:
  - Service account configuration
  - BigQuery connector setup
  - Dashboard creation walkthrough
  - Sharing and permissions
  - Troubleshooting tips

## Quick Start

### Prerequisites

1. BigQuery datasets populated with data
2. Materialized views created (`gold_sec` dataset)
3. Service account: `sec-looker-sa@PROJECT_ID.iam.gserviceaccount.com`
4. Google account for Looker Studio access

### Setup Steps

1. **Create Service Account Key**
   ```bash
   gcloud iam service-accounts keys create ~/looker-sa-key.json \
     --iam-account=sec-looker-sa@PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Access Looker Studio**
   - Go to https://lookerstudio.google.com/
   - Create → Data Source → BigQuery
   - Upload service account key
   - Connect to `gold_sec` dataset

3. **Create Dashboards**
   - Follow `looker_studio_setup.md` for detailed steps
   - Use `dashboard_specs.md` as reference for components

4. **Share with Team**
   - Share dashboards with stakeholders
   - Set appropriate permissions (Viewer/Editor)

## Dashboard URLs

After creation, document your dashboard URLs here:

- **Executive Summary**: [URL after creation]
- **Company Deep Dive**: [URL after creation]
- **Peer Comparison**: [URL after creation]
- **Industry Analysis**: [URL after creation]

## Data Sources

All dashboards connect to these BigQuery materialized views in `gold_sec`:

| View Name | Purpose | Refresh Frequency |
|-----------|---------|-------------------|
| `looker_company_metrics` | Pre-aggregated financials | Daily |
| `looker_financial_ratios` | Calculated ratios | Daily |
| `looker_peer_comparison` | Industry benchmarks | Daily |
| `looker_timeseries` | TTM and growth metrics | Daily |

## Features

### Dashboard 1: Executive Summary
- 📊 Total companies, revenue, profit margin scorecards
- 📈 Quarterly revenue trend line
- 🏆 Top 25 companies by revenue
- 🥧 Sector distribution pie chart
- 🔥 Profitability heatmap by sector
- 📅 Recent filings table

### Dashboard 2: Company Deep Dive
- 🏢 Company profile header
- 📑 Financial statement tables (3 statements)
- 📊 Quarterly metrics trend charts
- 🔢 12 key financial ratios scorecards
- 📊 TTM vs Annual comparison
- 👥 Peer comparison table

### Dashboard 3: Peer Comparison
- 🗺️ Metrics heatmap (companies × ratios)
- 📊 Scatter plot analysis with customizable axes
- 🎯 Percentile rankings bullet charts
- 🏆 Sector leaders leaderboard
- 📊 Distribution histograms
- 🎚️ Interactive sector and company filters

### Dashboard 4: Industry Analysis
- 🌍 Market overview scorecards
- 📊 Sector performance comparison
- 🗺️ Market share treemap
- 📦 Growth rate distribution box plots
- 📈 Time-series sector trends
- 🔗 Correlation matrix (advanced)

## Performance

**Targets**:
- Initial load: < 3 seconds
- Filter application: < 1 second
- Drill-through navigation: < 2 seconds

**Optimization**:
- All dashboards use materialized views (pre-aggregated data)
- BigQuery tables partitioned by `fiscal_year`
- Clustering on `cik` and `sector` for fast filtering
- Automatic caching with 1-hour refresh

## Costs

**BigQuery Query Costs**:
- Average cost per dashboard load: ~$0.001-0.01
- Estimated monthly cost (100 users, 10 views/day): ~$30-300

**Tips to Reduce Costs**:
- Use materialized views (included)
- Enable Looker Studio caching (1 hour)
- Apply date range filters
- Limit rows returned in tables

## Customization

### Add Custom Metrics

Create calculated fields in Looker Studio:

**Example: EBITDA**
```
revenue - cost_of_revenue - operating_expenses + depreciation_amortization
```

**Example: Free Cash Flow**
```
operating_cash_flow - capital_expenditures
```

### Add Company Logos

Use a blended data source:
1. Create Google Sheet with CIK → Logo URL mapping
2. Blend with BigQuery data on CIK
3. Use Image chart type with Logo URL field

### Add External Data

Blend with:
- Stock prices (via Google Finance connector)
- Economic indicators (from FRED API)
- News sentiment (custom data source)

## Maintenance

### Weekly Tasks
- ✅ Review dashboard performance
- ✅ Check for errors in logs
- ✅ Verify data freshness

### Monthly Tasks
- ✅ Review BigQuery costs
- ✅ Optimize slow-loading charts
- ✅ Gather user feedback
- ✅ Update color schemes/styling as needed

### Quarterly Tasks
- ✅ Add new companies/sectors if available
- ✅ Update calculated fields if taxonomy changes
- ✅ Review and refresh dashboard designs

## Support

### Common Issues

**"No data to display"**
- Check BigQuery tables have data
- Verify materialized views are refreshed
- Check filter settings

**"Access denied"**
- Verify service account permissions
- Re-upload service account key if needed

**Slow performance**
- Check query complexity
- Add more filters to reduce data scanned
- Use smaller date ranges

### Getting Help

1. Review `looker_studio_setup.md` troubleshooting section
2. Check BigQuery query logs for errors
3. Review Looker Studio community forums
4. Contact data engineering team

## Resources

- [Looker Studio Documentation](https://support.google.com/looker-studio)
- [BigQuery Best Practices](https://cloud.google.com/bigquery/docs/best-practices)
- [Dashboard Design Principles](https://datastudio.google.com/reporting/)

## Future Enhancements

Potential improvements for future iterations:

- [ ] Real-time stock price integration
- [ ] News sentiment analysis overlay
- [ ] Analyst estimates comparison
- [ ] Automated anomaly detection
- [ ] Custom alerts and notifications
- [ ] Mobile app optimization
- [ ] Voice-activated dashboard navigation (experimental)

---

**Note**: Looker Studio is free to use with a Google account. No additional licensing required.
