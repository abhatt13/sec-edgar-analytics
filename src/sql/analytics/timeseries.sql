-- Time-Series Analysis Queries
-- Growth trends, TTM calculations, and historical analysis

-- Query 1: Revenue Growth Trends (Quarterly)
SELECT
  company_name,
  ticker,
  fiscal_year,
  fiscal_period,
  ROUND(revenue / 1000000, 2) as revenue_millions,
  ROUND(ttm_revenue / 1000000, 2) as ttm_revenue_millions,
  ROUND(revenue_yoy_growth_pct, 2) as yoy_growth_pct,
  ROUND(revenue_4q_avg / 1000000, 2) as avg_4q_revenue_millions
FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
WHERE ticker IN ('AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META') -- FAANG comparison
  AND fiscal_year >= 2020
  AND fiscal_period != 'FY' -- Quarterly data only
ORDER BY ticker, fiscal_year, fiscal_period;

-- Query 2: Companies with Accelerating Growth
WITH growth_acceleration AS (
  SELECT
    cik,
    company_name,
    ticker,
    fiscal_year,
    fiscal_period,
    revenue_yoy_growth_pct as current_growth,
    LAG(revenue_yoy_growth_pct, 1) OVER (
      PARTITION BY cik ORDER BY fiscal_year, fiscal_period
    ) as prior_quarter_growth,
    LAG(revenue_yoy_growth_pct, 4) OVER (
      PARTITION BY cik ORDER BY fiscal_year, fiscal_period
    ) as prior_year_growth
  FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
  WHERE fiscal_period IN ('Q1', 'Q2', 'Q3', 'Q4')
    AND revenue > 100000000 -- $100M+ revenue
)
SELECT
  company_name,
  ticker,
  fiscal_year,
  fiscal_period,
  ROUND(current_growth, 2) as current_yoy_growth_pct,
  ROUND(prior_quarter_growth, 2) as prior_qtr_growth_pct,
  ROUND(current_growth - prior_quarter_growth, 2) as qoq_acceleration_pct
FROM growth_acceleration
WHERE current_growth > prior_quarter_growth
  AND current_growth > 20 -- High growth threshold
  AND fiscal_year = 2023
ORDER BY qoq_acceleration_pct DESC
LIMIT 50;

-- Query 3: TTM Analysis - Trailing Twelve Months Metrics
SELECT
  company_name,
  ticker,
  fiscal_year,
  fiscal_period,
  ROUND(ttm_revenue / 1000000000, 2) as ttm_revenue_billions,
  ROUND(ttm_net_income / 1000000000, 2) as ttm_net_income_billions,
  ROUND(SAFE_DIVIDE(ttm_net_income, ttm_revenue) * 100, 2) as ttm_profit_margin_pct,

  -- Compare to same quarter last year
  LAG(ttm_revenue, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period) as ttm_revenue_yoy_prior,
  ROUND(
    SAFE_DIVIDE(
      ttm_revenue - LAG(ttm_revenue, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period),
      LAG(ttm_revenue, 4) OVER (PARTITION BY cik ORDER BY fiscal_year, fiscal_period)
    ) * 100,
    2
  ) as ttm_revenue_yoy_growth_pct

FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
WHERE fiscal_year >= 2022
  AND ttm_revenue > 1000000000 -- $1B+ TTM revenue
  AND fiscal_period = 'Q4' -- Year-end comparison
ORDER BY ttm_revenue_yoy_growth_pct DESC
LIMIT 100;

-- Query 4: Consistency Analysis - Low Volatility Companies
WITH volatility_calc AS (
  SELECT
    cik,
    company_name,
    ticker,
    STDDEV(revenue_yoy_growth_pct) as revenue_growth_stddev,
    AVG(revenue_yoy_growth_pct) as avg_revenue_growth,
    COUNT(*) as quarters_of_data
  FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
  WHERE fiscal_year >= 2020
    AND fiscal_period IN ('Q1', 'Q2', 'Q3', 'Q4')
    AND revenue_yoy_growth_pct IS NOT NULL
  GROUP BY cik, company_name, ticker
  HAVING quarters_of_data >= 12 -- At least 3 years of data
)
SELECT
  company_name,
  ticker,
  ROUND(avg_revenue_growth, 2) as avg_yoy_growth_pct,
  ROUND(revenue_growth_stddev, 2) as growth_volatility_stddev,
  ROUND(SAFE_DIVIDE(avg_revenue_growth, revenue_growth_stddev), 2) as consistency_score,
  quarters_of_data
FROM volatility_calc
WHERE avg_revenue_growth > 5 -- Positive growth
  AND revenue_growth_stddev < 15 -- Low volatility
ORDER BY consistency_score DESC
LIMIT 50;

-- Query 5: Seasonal Pattern Analysis
SELECT
  company_name,
  ticker,
  fiscal_period,
  COUNT(*) as years_analyzed,
  ROUND(AVG(revenue) / 1000000, 2) as avg_revenue_millions,
  ROUND(STDDEV(revenue) / 1000000, 2) as revenue_stddev_millions,
  ROUND(MIN(revenue) / 1000000, 2) as min_revenue_millions,
  ROUND(MAX(revenue) / 1000000, 2) as max_revenue_millions,

  -- Coefficient of variation (volatility measure)
  ROUND(SAFE_DIVIDE(STDDEV(revenue), AVG(revenue)) * 100, 2) as coefficient_of_variation_pct

FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
WHERE ticker IN ('AAPL', 'NKE', 'HD', 'TGT', 'WMT') -- Retailers with potential seasonality
  AND fiscal_year BETWEEN 2020 AND 2023
  AND fiscal_period IN ('Q1', 'Q2', 'Q3', 'Q4')
GROUP BY company_name, ticker, fiscal_period
ORDER BY ticker, fiscal_period;

-- Query 6: Multi-Year Compound Growth
WITH year_endpoints AS (
  SELECT
    cik,
    company_name,
    ticker,
    MIN(CASE WHEN fiscal_year = 2020 AND fiscal_period = 'FY' THEN revenue END) as revenue_2020,
    MAX(CASE WHEN fiscal_year = 2023 AND fiscal_period = 'FY' THEN revenue END) as revenue_2023,
    MIN(CASE WHEN fiscal_year = 2020 AND fiscal_period = 'FY' THEN net_income END) as net_income_2020,
    MAX(CASE WHEN fiscal_year = 2023 AND fiscal_period = 'FY' THEN net_income END) as net_income_2023
  FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
  WHERE fiscal_period = 'FY'
  GROUP BY cik, company_name, ticker
  HAVING revenue_2020 IS NOT NULL AND revenue_2023 IS NOT NULL
)
SELECT
  company_name,
  ticker,
  ROUND(revenue_2020 / 1000000000, 2) as revenue_2020_billions,
  ROUND(revenue_2023 / 1000000000, 2) as revenue_2023_billions,
  ROUND((POWER(SAFE_DIVIDE(revenue_2023, revenue_2020), 1.0/3) - 1) * 100, 2) as revenue_cagr_3yr_pct,

  ROUND(net_income_2020 / 1000000000, 2) as net_income_2020_billions,
  ROUND(net_income_2023 / 1000000000, 2) as net_income_2023_billions,
  ROUND((POWER(SAFE_DIVIDE(net_income_2023, net_income_2020), 1.0/3) - 1) * 100, 2) as net_income_cagr_3yr_pct

FROM year_endpoints
WHERE revenue_2020 > 0
  AND revenue_2023 > revenue_2020
ORDER BY revenue_cagr_3yr_pct DESC
LIMIT 100;

-- Query 7: Recovery Analysis (Post-Pandemic)
WITH pandemic_recovery AS (
  SELECT
    cik,
    company_name,
    ticker,
    MAX(CASE WHEN fiscal_year = 2019 AND fiscal_period = 'FY' THEN revenue END) as pre_pandemic_revenue,
    MIN(revenue) as pandemic_trough_revenue,
    MAX(CASE WHEN fiscal_year = 2023 AND fiscal_period = 'FY' THEN revenue END) as current_revenue
  FROM `${PROJECT_ID}.gold_sec.looker_timeseries`
  WHERE fiscal_year BETWEEN 2019 AND 2023
    AND fiscal_period = 'FY'
  GROUP BY cik, company_name, ticker
)
SELECT
  company_name,
  ticker,
  ROUND(pre_pandemic_revenue / 1000000000, 2) as pre_pandemic_revenue_billions,
  ROUND(pandemic_trough_revenue / 1000000000, 2) as trough_revenue_billions,
  ROUND(current_revenue / 1000000000, 2) as current_revenue_billions,

  ROUND(SAFE_DIVIDE(pandemic_trough_revenue - pre_pandemic_revenue, pre_pandemic_revenue) * 100, 2) as pandemic_decline_pct,
  ROUND(SAFE_DIVIDE(current_revenue - pre_pandemic_revenue, pre_pandemic_revenue) * 100, 2) as recovery_vs_2019_pct,

  CASE
    WHEN current_revenue > pre_pandemic_revenue * 1.1 THEN 'Recovered+'
    WHEN current_revenue > pre_pandemic_revenue THEN 'Recovered'
    WHEN current_revenue > pandemic_trough_revenue THEN 'Recovering'
    ELSE 'Still Below Trough'
  END as recovery_status

FROM pandemic_recovery
WHERE pre_pandemic_revenue > 100000000
ORDER BY recovery_vs_2019_pct DESC
LIMIT 100;
