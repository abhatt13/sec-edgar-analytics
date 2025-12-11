-- Gold Layer - Looker-Optimized Materialized Views
-- Pre-aggregated and optimized views for dashboard performance

-- Materialized View: looker_company_metrics
-- Pre-aggregated key financial metrics by company and period
CREATE MATERIALIZED VIEW IF NOT EXISTS `${PROJECT_ID}.gold_sec.looker_company_metrics`
PARTITION BY fiscal_year
CLUSTER BY cik
OPTIONS(
  description="Pre-aggregated financial metrics for Looker dashboards - optimized for company analysis",
  enable_refresh=true,
  refresh_interval_minutes=1440
)
AS
WITH latest_facts AS (
  SELECT
    f.cik,
    c.company_name,
    c.ticker,
    c.sector,
    c.industry,
    f.fiscal_year,
    f.fiscal_period,
    f.concept,
    f.value,
    f.unit,
    f.statement_type,
    ROW_NUMBER() OVER (
      PARTITION BY f.cik, f.concept, f.fiscal_year, f.fiscal_period
      ORDER BY f.filing_date DESC
    ) as rn
  FROM `${PROJECT_ID}.silver_sec.fact_financials` f
  JOIN `${PROJECT_ID}.silver_sec.dim_companies` c ON f.cik = c.cik
  WHERE f.unit = 'USD'
)
SELECT
  cik,
  company_name,
  ticker,
  sector,
  industry,
  fiscal_year,
  fiscal_period,

  -- Income Statement Metrics
  MAX(CASE WHEN concept IN ('Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax') THEN value END) as revenue,
  MAX(CASE WHEN concept = 'CostOfRevenue' THEN value END) as cost_of_revenue,
  MAX(CASE WHEN concept = 'GrossProfit' THEN value END) as gross_profit,
  MAX(CASE WHEN concept = 'OperatingIncomeLoss' THEN value END) as operating_income,
  MAX(CASE WHEN concept = 'NetIncomeLoss' THEN value END) as net_income,
  MAX(CASE WHEN concept = 'OperatingExpenses' THEN value END) as operating_expenses,
  MAX(CASE WHEN concept = 'ResearchAndDevelopmentExpense' THEN value END) as research_and_development,
  MAX(CASE WHEN concept = 'SellingGeneralAndAdministrativeExpense' THEN value END) as sg_and_a,
  MAX(CASE WHEN concept = 'InterestExpense' THEN value END) as interest_expense,
  MAX(CASE WHEN concept = 'IncomeTaxExpenseBenefit' THEN value END) as income_tax_expense,

  -- Balance Sheet Metrics
  MAX(CASE WHEN concept = 'Assets' THEN value END) as total_assets,
  MAX(CASE WHEN concept = 'AssetsCurrent' THEN value END) as current_assets,
  MAX(CASE WHEN concept = 'CashAndCashEquivalentsAtCarryingValue' THEN value END) as cash_and_equivalents,
  MAX(CASE WHEN concept = 'AccountsReceivableNetCurrent' THEN value END) as accounts_receivable,
  MAX(CASE WHEN concept = 'InventoryNet' THEN value END) as inventory,
  MAX(CASE WHEN concept = 'Liabilities' THEN value END) as total_liabilities,
  MAX(CASE WHEN concept = 'LiabilitiesCurrent' THEN value END) as current_liabilities,
  MAX(CASE WHEN concept = 'LongTermDebtNoncurrent' THEN value END) as long_term_debt,
  MAX(CASE WHEN concept = 'StockholdersEquity' THEN value END) as stockholders_equity,

  -- Cash Flow Metrics
  MAX(CASE WHEN concept = 'NetCashProvidedByUsedInOperatingActivities' THEN value END) as operating_cash_flow,
  MAX(CASE WHEN concept = 'NetCashProvidedByUsedInInvestingActivities' THEN value END) as investing_cash_flow,
  MAX(CASE WHEN concept = 'NetCashProvidedByUsedInFinancingActivities' THEN value END) as financing_cash_flow,
  MAX(CASE WHEN concept = 'PaymentsToAcquirePropertyPlantAndEquipment' THEN value END) as capital_expenditures,

  CURRENT_TIMESTAMP() as last_updated

FROM latest_facts
WHERE rn = 1
GROUP BY cik, company_name, ticker, sector, industry, fiscal_year, fiscal_period;

-- Materialized View: looker_financial_ratios
-- Calculated financial ratios for company analysis
CREATE MATERIALIZED VIEW IF NOT EXISTS `${PROJECT_ID}.gold_sec.looker_financial_ratios`
PARTITION BY fiscal_year
CLUSTER BY cik
OPTIONS(
  description="Calculated financial ratios for Looker dashboards - profitability, liquidity, leverage metrics",
  enable_refresh=true,
  refresh_interval_minutes=1440
)
AS
SELECT
  cik,
  company_name,
  ticker,
  fiscal_year,
  fiscal_period,

  -- Profitability Ratios
  SAFE_DIVIDE(gross_profit, revenue) * 100 as gross_margin_pct,
  SAFE_DIVIDE(operating_income, revenue) * 100 as operating_margin_pct,
  SAFE_DIVIDE(net_income, revenue) * 100 as net_profit_margin_pct,
  SAFE_DIVIDE(net_income, total_assets) * 100 as return_on_assets_pct,
  SAFE_DIVIDE(net_income, stockholders_equity) * 100 as return_on_equity_pct,

  -- Liquidity Ratios
  SAFE_DIVIDE(current_assets, current_liabilities) as current_ratio,
  SAFE_DIVIDE(current_assets - inventory, current_liabilities) as quick_ratio,
  SAFE_DIVIDE(cash_and_equivalents, current_liabilities) as cash_ratio,

  -- Leverage Ratios
  SAFE_DIVIDE(total_liabilities, total_assets) * 100 as debt_to_assets_pct,
  SAFE_DIVIDE(total_liabilities, stockholders_equity) as debt_to_equity_ratio,
  SAFE_DIVIDE(long_term_debt, stockholders_equity) as long_term_debt_to_equity,

  -- Efficiency Ratios
  SAFE_DIVIDE(revenue, total_assets) as asset_turnover,
  SAFE_DIVIDE(revenue, accounts_receivable) as receivables_turnover,

  -- Operating Ratios
  SAFE_DIVIDE(operating_expenses, revenue) * 100 as operating_expense_ratio_pct,
  SAFE_DIVIDE(research_and_development, revenue) * 100 as rd_intensity_pct,

  -- Cash Flow Ratios
  SAFE_DIVIDE(operating_cash_flow, net_income) as operating_cash_flow_ratio,
  SAFE_DIVIDE(operating_cash_flow - capital_expenditures, net_income) as free_cash_flow_ratio,

  -- Raw values for reference
  revenue,
  net_income,
  total_assets,
  stockholders_equity,
  operating_cash_flow,

  CURRENT_TIMESTAMP() as last_updated

FROM `${PROJECT_ID}.gold_sec.looker_company_metrics`
WHERE fiscal_period = 'FY'; -- Annual metrics only for ratios

-- Materialized View: looker_peer_comparison
-- Industry benchmarks and percentile rankings
CREATE MATERIALIZED VIEW IF NOT EXISTS `${PROJECT_ID}.gold_sec.looker_peer_comparison`
PARTITION BY fiscal_year
CLUSTER BY sector
OPTIONS(
  description="Peer comparison and industry benchmarks with percentile rankings",
  enable_refresh=true,
  refresh_interval_minutes=1440
)
AS
WITH company_ratios AS (
  SELECT
    cik,
    company_name,
    ticker,
    sector,
    industry,
    fiscal_year,
    gross_margin_pct,
    operating_margin_pct,
    net_profit_margin_pct,
    return_on_assets_pct,
    return_on_equity_pct,
    current_ratio,
    debt_to_equity_ratio,
    revenue,
    net_income,
    total_assets
  FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
  WHERE sector IS NOT NULL
)
SELECT
  cik,
  company_name,
  ticker,
  sector,
  industry,
  fiscal_year,

  -- Company Metrics
  gross_margin_pct,
  operating_margin_pct,
  net_profit_margin_pct,
  return_on_assets_pct,
  return_on_equity_pct,
  current_ratio,
  debt_to_equity_ratio,
  revenue,

  -- Industry Averages
  AVG(gross_margin_pct) OVER (PARTITION BY sector, fiscal_year) as sector_avg_gross_margin,
  AVG(operating_margin_pct) OVER (PARTITION BY sector, fiscal_year) as sector_avg_operating_margin,
  AVG(net_profit_margin_pct) OVER (PARTITION BY sector, fiscal_year) as sector_avg_net_margin,
  AVG(return_on_equity_pct) OVER (PARTITION BY sector, fiscal_year) as sector_avg_roe,

  -- Percentile Rankings
  PERCENT_RANK() OVER (PARTITION BY sector, fiscal_year ORDER BY gross_margin_pct) * 100 as gross_margin_percentile,
  PERCENT_RANK() OVER (PARTITION BY sector, fiscal_year ORDER BY operating_margin_pct) * 100 as operating_margin_percentile,
  PERCENT_RANK() OVER (PARTITION BY sector, fiscal_year ORDER BY net_profit_margin_pct) * 100 as net_margin_percentile,
  PERCENT_RANK() OVER (PARTITION BY sector, fiscal_year ORDER BY return_on_equity_pct) * 100 as roe_percentile,
  PERCENT_RANK() OVER (PARTITION BY sector, fiscal_year ORDER BY revenue) * 100 as revenue_percentile,

  -- Peer Count
  COUNT(*) OVER (PARTITION BY sector, fiscal_year) as peer_count,

  CURRENT_TIMESTAMP() as last_updated

FROM company_ratios;

-- Materialized View: looker_timeseries
-- Time-series metrics with TTM and growth calculations
CREATE MATERIALIZED VIEW IF NOT EXISTS `${PROJECT_ID}.gold_sec.looker_timeseries`
PARTITION BY fiscal_year
CLUSTER BY cik
OPTIONS(
  description="Time-series metrics with trailing twelve months (TTM) and year-over-year growth",
  enable_refresh=true,
  refresh_interval_minutes=1440
)
AS
WITH quarterly_metrics AS (
  SELECT
    cik,
    company_name,
    ticker,
    fiscal_year,
    fiscal_period,
    revenue,
    net_income,
    operating_cash_flow,
    total_assets
  FROM `${PROJECT_ID}.gold_sec.looker_company_metrics`
  WHERE fiscal_period IN ('Q1', 'Q2', 'Q3', 'Q4', 'FY')
)
SELECT
  cik,
  company_name,
  ticker,
  fiscal_year,
  fiscal_period,

  -- Current Period Metrics
  revenue,
  net_income,
  operating_cash_flow,
  total_assets,

  -- Trailing 4 Quarters (TTM for quarterly data)
  SUM(revenue) OVER (
    PARTITION BY cik
    ORDER BY fiscal_year, fiscal_period
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ) as ttm_revenue,

  SUM(net_income) OVER (
    PARTITION BY cik
    ORDER BY fiscal_year, fiscal_period
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ) as ttm_net_income,

  -- Year-over-Year Growth
  LAG(revenue, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period) as revenue_yoy_prior,
  SAFE_DIVIDE(
    revenue - LAG(revenue, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period),
    LAG(revenue, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period)
  ) * 100 as revenue_yoy_growth_pct,

  SAFE_DIVIDE(
    net_income - LAG(net_income, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period),
    LAG(net_income, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period)
  ) * 100 as net_income_yoy_growth_pct,

  -- Moving Averages (4 quarter)
  AVG(revenue) OVER (
    PARTITION BY cik
    ORDER BY fiscal_year, fiscal_period
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ) as revenue_4q_avg,

  AVG(net_income) OVER (
    PARTITION BY cik
    ORDER BY fiscal_year, fiscal_period
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ) as net_income_4q_avg,

  CURRENT_TIMESTAMP() as last_updated

FROM quarterly_metrics;
