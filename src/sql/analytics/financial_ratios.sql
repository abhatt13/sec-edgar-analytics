-- Financial Ratio Analytical Queries
-- Common queries for financial analysis and reporting

-- Query 1: Top Companies by Profit Margin (Latest Year)
WITH latest_year AS (
  SELECT MAX(fiscal_year) as max_year
  FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
)
SELECT
  company_name,
  ticker,
  fiscal_year,
  net_profit_margin_pct,
  revenue,
  net_income,
  return_on_equity_pct
FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
WHERE fiscal_year = (SELECT max_year FROM latest_year)
  AND revenue > 1000000000 -- Minimum $1B revenue
  AND net_profit_margin_pct IS NOT NULL
ORDER BY net_profit_margin_pct DESC
LIMIT 25;

-- Query 2: Companies with Highest ROE by Sector
SELECT
  sector,
  company_name,
  ticker,
  fiscal_year,
  return_on_equity_pct,
  net_profit_margin_pct,
  debt_to_equity_ratio
FROM (
  SELECT
    sector,
    company_name,
    ticker,
    fiscal_year,
    return_on_equity_pct,
    net_profit_margin_pct,
    debt_to_equity_ratio,
    ROW_NUMBER() OVER (PARTITION BY sector ORDER BY return_on_equity_pct DESC) as rank
  FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
  WHERE fiscal_year = 2023
    AND sector IS NOT NULL
    AND return_on_equity_pct > 0
)
WHERE rank <= 5
ORDER BY sector, rank;

-- Query 3: Liquidity Analysis - Companies with Weak Current Ratios
SELECT
  company_name,
  ticker,
  sector,
  fiscal_year,
  current_ratio,
  quick_ratio,
  cash_ratio,
  current_liabilities as current_liabilities_usd
FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
WHERE fiscal_year >= 2020
  AND current_ratio < 1.0 -- Below healthy threshold
  AND current_ratio IS NOT NULL
ORDER BY current_ratio ASC, fiscal_year DESC
LIMIT 100;

-- Query 4: High Growth Companies (Revenue CAGR)
WITH revenue_growth AS (
  SELECT
    cik,
    company_name,
    ticker,
    MIN(CASE WHEN fiscal_year = 2020 THEN revenue END) as revenue_2020,
    MAX(CASE WHEN fiscal_year = 2023 THEN revenue END) as revenue_2023,
    COUNT(DISTINCT fiscal_year) as years_of_data
  FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
  WHERE fiscal_year BETWEEN 2020 AND 2023
  GROUP BY cik, company_name, ticker
  HAVING years_of_data >= 3
)
SELECT
  company_name,
  ticker,
  revenue_2020,
  revenue_2023,
  revenue_2023 - revenue_2020 as revenue_growth_absolute,
  ROUND(
    POWER(SAFE_DIVIDE(revenue_2023, revenue_2020), 1.0/3) - 1,
    4
  ) * 100 as revenue_cagr_3yr_pct
FROM revenue_growth
WHERE revenue_2020 > 0
  AND revenue_2023 > revenue_2020
ORDER BY revenue_cagr_3yr_pct DESC
LIMIT 50;

-- Query 5: Leverage Analysis - Highly Leveraged Companies
SELECT
  company_name,
  ticker,
  sector,
  fiscal_year,
  debt_to_equity_ratio,
  debt_to_assets_pct,
  long_term_debt_to_equity,
  total_assets,
  stockholders_equity
FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
WHERE fiscal_year = 2023
  AND debt_to_equity_ratio > 2.0 -- High leverage
  AND total_assets > 1000000000 -- Minimum $1B assets
ORDER BY debt_to_equity_ratio DESC
LIMIT 50;

-- Query 6: Profitability Trend Analysis
SELECT
  company_name,
  ticker,
  fiscal_year,
  gross_margin_pct,
  operating_margin_pct,
  net_profit_margin_pct,
  return_on_assets_pct,
  return_on_equity_pct
FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
WHERE cik IN (
  -- Top 10 companies by revenue in latest year
  SELECT cik
  FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
  WHERE fiscal_year = 2023
  ORDER BY revenue DESC
  LIMIT 10
)
  AND fiscal_year >= 2020
ORDER BY company_name, fiscal_year;

-- Query 7: Sector Performance Comparison
SELECT
  sector,
  fiscal_year,
  COUNT(DISTINCT cik) as company_count,
  ROUND(AVG(gross_margin_pct), 2) as avg_gross_margin_pct,
  ROUND(AVG(operating_margin_pct), 2) as avg_operating_margin_pct,
  ROUND(AVG(net_profit_margin_pct), 2) as avg_net_margin_pct,
  ROUND(AVG(return_on_equity_pct), 2) as avg_roe_pct,
  ROUND(AVG(current_ratio), 2) as avg_current_ratio
FROM `${PROJECT_ID}.gold_sec.looker_financial_ratios`
WHERE fiscal_year >= 2020
  AND sector IS NOT NULL
GROUP BY sector, fiscal_year
ORDER BY sector, fiscal_year;
