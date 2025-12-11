# Looker Studio Dashboard Specifications

Complete specifications for 4 production Looker Studio dashboards connected to BigQuery.

## Data Source Connection

**Primary Dataset**: `gold_sec` (BigQuery)
**Tables Used**:
- `looker_company_metrics`
- `looker_financial_ratios`
- `looker_peer_comparison`
- `looker_timeseries`

**Service Account**: `sec-looker-sa@PROJECT_ID.iam.gserviceaccount.com`
**Required Permissions**: `roles/bigquery.dataViewer`, `roles/bigquery.jobUser`

---

## Dashboard 1: Executive Summary

**Purpose**: High-level overview of key financial metrics and trends across all companies

### Layout
- **Grid**: 12 columns × responsive rows
- **Theme**: Corporate (Blue/White color scheme)
- **Refresh**: Auto-refresh every 1 hour

### Components

#### 1.1 Scorecard Row (Top)
**Data Source**: `looker_company_metrics` + `looker_timeseries`

| Metric | Calculation | Period |
|--------|-------------|---------|
| Total Companies | `COUNT(DISTINCT cik)` | Current |
| Total Revenue (TTM) | `SUM(ttm_revenue) / 1B` | Latest Quarter |
| Avg Profit Margin | `AVG(net_profit_margin_pct)` | Latest Year |
| Companies with Positive Growth | `COUNT(IF revenue_yoy_growth_pct > 0)` | YoY |

**Formatting**:
- Currency values: $X.XX B
- Percentages: X.X%
- Trend indicators: ↑ Green if positive, ↓ Red if negative

#### 1.2 Revenue Trend Chart (Center-Left)
**Chart Type**: Line chart with dual axis
**Data Source**: `looker_timeseries`

- **Dimensions**: `fiscal_year`, `fiscal_period`
- **Metrics**:
  - Primary axis: `SUM(ttm_revenue)` (Billions)
  - Secondary axis: `AVG(revenue_yoy_growth_pct)` (%)
- **Filters**: Last 12 quarters
- **Breakdown**: None (aggregate all companies)

#### 1.3 Top 25 Companies by Revenue (Center-Right)
**Chart Type**: Bar chart (horizontal)
**Data Source**: `looker_company_metrics`

- **Dimension**: `company_name` OR `ticker`
- **Metric**: `revenue`
- **Sort**: Descending by revenue
- **Limit**: 25
- **Filter**: `fiscal_year = MAX(fiscal_year)` AND `fiscal_period = 'FY'`
- **Color**: Gradient (blue scale)

#### 1.4 Sector Distribution (Bottom-Left)
**Chart Type**: Pie chart
**Data Source**: `looker_financial_ratios`

- **Dimension**: `sector`
- **Metric**: `COUNT(DISTINCT cik)`
- **Filter**: Latest fiscal year
- **Labels**: Show percentage and count

#### 1.5 Profitability Heatmap (Bottom-Right)
**Chart Type**: Table with conditional formatting
**Data Source**: `looker_financial_ratios`

- **Dimensions**: `sector`
- **Metrics**:
  - `AVG(gross_margin_pct)`
  - `AVG(operating_margin_pct)`
  - `AVG(net_profit_margin_pct)`
  - `AVG(return_on_equity_pct)`
- **Conditional Formatting**:
  - Green: >75th percentile
  - Yellow: 25-75th percentile
  - Red: <25th percentile

#### 1.6 Recent Filings Table (Bottom)
**Chart Type**: Table with links
**Data Source**: `looker_company_metrics`

- **Columns**: Company, Ticker, Fiscal Year, Quarter, Revenue, Net Income, Filing Date
- **Sort**: Most recent filing_date
- **Limit**: 50
- **Drill-down**: Link to Dashboard 2 (Company Deep Dive)

### Filters (Global)
- **Fiscal Year**: Multi-select dropdown (default: Latest 2 years)
- **Sector**: Multi-select dropdown (default: All)
- **Min Revenue**: Slider (default: $0)

---

## Dashboard 2: Company Deep Dive

**Purpose**: Detailed financial analysis for individual companies

### Layout
- **Single company focus** with drill-through from Dashboard 1
- **Parameter**: `Company CIK` or `Ticker`

### Components

#### 2.1 Company Header Card
**Data Source**: `looker_company_metrics`

Display:
- Company Name (Large font)
- Ticker Symbol
- Sector | Industry
- Latest Revenue | Market Cap Proxy
- Company Logo (if available via external API)

#### 2.2 Financial Statement Tabs

**Tab 1: Income Statement**
**Chart Type**: Table + Trend chart
**Data Source**: `looker_company_metrics`

| Line Item | 2020 | 2021 | 2022 | 2023 | Trend |
|-----------|------|------|------|------|-------|
| Revenue | | | | | Line chart |
| Cost of Revenue | | | | | Line chart |
| Gross Profit | | | | | Line chart |
| Operating Expenses | | | | | Line chart |
| Operating Income | | | | | Line chart |
| Net Income | | | | | Line chart |

**Tab 2: Balance Sheet**
Similar table for Assets, Liabilities, Equity

**Tab 3: Cash Flow**
Similar table for Operating, Investing, Financing cash flows

#### 2.3 Financial Ratios Scorecard
**Data Source**: `looker_financial_ratios`

Display 12 key ratios in card format:
- Profitability: Gross Margin, Operating Margin, Net Margin, ROE, ROA
- Liquidity: Current Ratio, Quick Ratio
- Leverage: Debt-to-Equity, Debt-to-Assets
- Efficiency: Asset Turnover, Receivables Turnover

Each card shows:
- Current value
- YoY change (↑/↓)
- Sector average comparison bar

#### 2.4 Quarterly Trends (Time Series)
**Chart Type**: Multi-line chart
**Data Source**: `looker_timeseries`

- **X-axis**: Quarter (last 12 quarters)
- **Y-axis**: Dollars
- **Lines**:
  - Revenue (primary axis)
  - Net Income (primary axis)
  - Operating Cash Flow (primary axis)
  - Free Cash Flow (calculated)

#### 2.5 TTM vs Annual Comparison
**Chart Type**: Grouped column chart
**Data Source**: `looker_timeseries`

- Compare TTM metrics vs last full year
- Metrics: Revenue, Net Income, Operating Income

#### 2.6 Peer Comparison Table
**Data Source**: `looker_peer_comparison`

Show this company vs sector peers:
- **Columns**: Metric | This Company | Sector Avg | Percentile Rank
- **Metrics**: All major ratios
- **Highlight**: Where company outperforms (green) or underperforms (red)

### Filters
- **Fiscal Year Range**: Date range picker
- **Comparison Period**: Dropdown (QoQ, YoY, 3-Year)

---

## Dashboard 3: Peer Comparison & Benchmarking

**Purpose**: Compare companies within sectors and identify leaders/laggards

### Components

#### 3.1 Sector Selector (Top)
**Control Type**: Dropdown with multi-select
**Default**: Technology sector

#### 3.2 Metrics Heatmap (Center)
**Chart Type**: Heatmap table
**Data Source**: `looker_peer_comparison`

- **Rows**: Companies (top 50 by revenue in sector)
- **Columns**: Key metrics (8-10 financial ratios)
- **Cell Color**: Percentile-based (Red-Yellow-Green)
- **Cell Value**: Actual metric value
- **Sort**: By any column

Metrics to include:
- Gross Margin %
- Operating Margin %
- Net Margin %
- ROE %
- ROA %
- Current Ratio
- Debt/Equity
- Revenue Growth YoY %

#### 3.3 Scatter Plot Analysis
**Chart Type**: Scatter plot with trendline
**Data Source**: `looker_financial_ratios`

- **X-axis**: Choose metric (dropdown parameter)
- **Y-axis**: Choose metric (dropdown parameter)
- **Bubble Size**: Revenue
- **Bubble Color**: Sector
- **Labels**: Company ticker
- **Trendline**: Linear regression

Default: X=ROE%, Y=Profit Margin%

#### 3.4 Percentile Rankings
**Chart Type**: Bullet chart
**Data Source**: `looker_peer_comparison`

For selected company, show percentile rankings:
- Each metric = horizontal bullet chart
- Target line at 50th percentile
- Shaded regions: <25 (red), 25-75 (yellow), >75 (green)

#### 3.5 Sector Leaders Board
**Chart Type**: Table with medals/badges
**Data Source**: `looker_peer_comparison`

Top 10 companies by:
- Highest Profit Margin
- Highest ROE
- Highest Revenue Growth
- Best Liquidity (Current Ratio)

Show:
- Rank (1-10)
- Company
- Ticker
- Metric Value
- Sector Avg

#### 3.6 Distribution Charts
**Chart Type**: Histogram or box plot
**Data Source**: `looker_financial_ratios`

Show distribution of key metrics across sector:
- Net Profit Margin distribution
- ROE distribution
- Highlight selected company's position

### Filters
- **Sector**: Dropdown (required)
- **Fiscal Year**: Single select (default: latest)
- **Min Revenue**: Slider (filter out small companies)
- **Selected Company**: Dropdown (for highlighting in charts)

---

## Dashboard 4: Industry Analysis & Trends

**Purpose**: Macro-level trends across sectors and the entire dataset

### Components

#### 4.1 Market Overview Cards
**Data Source**: `looker_company_metrics` + `looker_timeseries`

| Metric | Calculation |
|--------|-------------|
| Total Companies | COUNT(DISTINCT cik) |
| Total Sectors | COUNT(DISTINCT sector) |
| Aggregate Revenue | SUM(revenue) latest year |
| Aggregate Market Cap | Approximation |
| Avg Revenue Growth | AVG(revenue_yoy_growth_pct) |

#### 4.2 Sector Performance Comparison
**Chart Type**: Grouped bar chart
**Data Source**: `looker_financial_ratios`

- **X-axis**: Sector
- **Y-axis**: Average metric value
- **Metrics** (grouped bars):
  - Avg Gross Margin
  - Avg Operating Margin
  - Avg Net Margin
  - Avg ROE
- **Sort**: By sector or by metric value

#### 4.3 Sector Revenue Pie/Treemap
**Chart Type**: Treemap
**Data Source**: `looker_company_metrics`

- **Hierarchy**: Sector > Company
- **Size**: Revenue
- **Color**: Profit Margin
- **Labels**: Show sector and $XXB

#### 4.4 Growth Rate Distribution
**Chart Type**: Box plot by sector
**Data Source**: `looker_timeseries`

- **X-axis**: Sector
- **Y-axis**: Revenue YoY Growth %
- **Box plot**: Shows median, quartiles, outliers

#### 4.5 Time-Series Sector Trends
**Chart Type**: Multi-line chart
**Data Source**: `looker_timeseries`

- **X-axis**: Fiscal Quarter
- **Y-axis**: Aggregate Revenue by Sector
- **Lines**: One per sector (8-10 major sectors)
- **Period**: Last 3 years

#### 4.6 Correlation Matrix (Advanced)
**Chart Type**: Heatmap
**Data Source**: `looker_financial_ratios`

Show correlation between financial metrics:
- Revenue vs Net Income
- Revenue Growth vs Profit Margin
- Debt/Equity vs ROE
- etc.

Color scale: -1 (red) to +1 (green)

#### 4.7 Market Share Analysis
**Chart Type**: Stacked bar chart
**Data Source**: `looker_peer_comparison`

- **X-axis**: Sector
- **Y-axis**: Total Revenue
- **Stacked Segments**: Top 10 companies + "Others"
- **Shows**: Market concentration in each sector

### Filters
- **Fiscal Year Range**: Multi-select or slider
- **Sectors**: Multi-select (default: all)
- **Company Size**: Small/Medium/Large based on revenue brackets

---

## Common Design Elements

### Color Palette
- **Primary**: #1A73E8 (Google Blue)
- **Secondary**: #34A853 (Green)
- **Warning**: #FBBC04 (Yellow)
- **Error**: #EA4335 (Red)
- **Neutral**: #5F6368 (Gray)

### Typography
- **Headers**: Roboto, 18-24px, Bold
- **Body**: Roboto, 12-14px, Regular
- **Numbers**: Roboto Mono, 14-16px

### Interactivity
- **Drill-through**: Click company → Navigate to Deep Dive dashboard
- **Tooltips**: Show detailed metrics on hover
- **Cross-filtering**: Selecting in one chart filters others
- **Date Range**: Global filter affects all dashboards

### Performance Targets
- **Initial Load**: < 3 seconds
- **Filter Application**: < 1 second
- **Drill-through**: < 2 seconds

### Mobile Optimization
- Stack charts vertically on mobile
- Simplify tables (fewer columns)
- Larger touch targets for filters

---

## Implementation Checklist

- [ ] Set up BigQuery connection in Looker Studio
- [ ] Configure service account access
- [ ] Create 4 separate dashboard reports
- [ ] Build all charts and tables
- [ ] Configure filters and parameters
- [ ] Set up drill-through links
- [ ] Apply theme and styling
- [ ] Test on desktop and mobile
- [ ] Share with stakeholders
- [ ] Schedule email delivery (optional)

## Next Steps

See `looker_studio_setup.md` for detailed step-by-step setup instructions.
