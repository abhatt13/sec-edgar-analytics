-- Peer Comparison and Benchmarking Queries

-- Query 1: Company vs Sector Benchmarks
SELECT
  company_name,
  ticker,
  sector,
  fiscal_year,

  -- Company Metrics
  gross_margin_pct as company_gross_margin,
  operating_margin_pct as company_operating_margin,
  net_profit_margin_pct as company_net_margin,
  return_on_equity_pct as company_roe,

  -- Sector Benchmarks
  sector_avg_gross_margin,
  sector_avg_operating_margin,
  sector_avg_net_margin,
  sector_avg_roe,

  -- Performance vs Peers
  ROUND(gross_margin_pct - sector_avg_gross_margin, 2) as gross_margin_vs_sector,
  ROUND(operating_margin_pct - sector_avg_operating_margin, 2) as operating_margin_vs_sector,
  ROUND(net_profit_margin_pct - sector_avg_net_margin, 2) as net_margin_vs_sector,

  -- Percentile Rankings
  ROUND(gross_margin_percentile, 0) as gross_margin_percentile,
  ROUND(operating_margin_percentile, 0) as operating_margin_percentile,
  ROUND(net_margin_percentile, 0) as net_margin_percentile,

  peer_count

FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
WHERE ticker IS NOT NULL
  AND fiscal_year = 2023
ORDER BY sector, net_margin_percentile DESC;

-- Query 2: Top Performers by Sector (Top Quartile)
SELECT
  sector,
  company_name,
  ticker,
  fiscal_year,
  net_profit_margin_pct,
  return_on_equity_pct,
  revenue,
  net_margin_percentile,
  roe_percentile
FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
WHERE net_margin_percentile >= 75 -- Top quartile
  AND fiscal_year = 2023
  AND sector IS NOT NULL
ORDER BY sector, net_margin_percentile DESC;

-- Query 3: Underperformers Needing Attention (Bottom Quartile)
SELECT
  sector,
  company_name,
  ticker,
  fiscal_year,
  net_profit_margin_pct,
  sector_avg_net_margin,
  net_profit_margin_pct - sector_avg_net_margin as margin_gap,
  net_margin_percentile,
  current_ratio,
  debt_to_equity_ratio
FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
WHERE net_margin_percentile <= 25 -- Bottom quartile
  AND fiscal_year = 2023
  AND revenue > 100000000 -- Minimum $100M revenue
ORDER BY net_margin_percentile ASC;

-- Query 4: Sector Leaders (Top 3 by Multiple Metrics)
WITH ranked_companies AS (
  SELECT
    sector,
    company_name,
    ticker,
    fiscal_year,
    gross_margin_pct,
    operating_margin_pct,
    net_profit_margin_pct,
    return_on_equity_pct,
    revenue,

    -- Composite score (average of percentiles)
    (gross_margin_percentile + operating_margin_percentile +
     net_margin_percentile + roe_percentile) / 4 as composite_score,

    ROW_NUMBER() OVER (PARTITION BY sector ORDER BY
      (gross_margin_percentile + operating_margin_percentile +
       net_margin_percentile + roe_percentile) / 4 DESC
    ) as sector_rank
  FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
  WHERE fiscal_year = 2023
    AND sector IS NOT NULL
    AND revenue > 500000000 -- Minimum $500M revenue
)
SELECT
  sector,
  sector_rank,
  company_name,
  ticker,
  ROUND(composite_score, 1) as overall_score,
  ROUND(gross_margin_pct, 2) as gross_margin_pct,
  ROUND(operating_margin_pct, 2) as operating_margin_pct,
  ROUND(net_profit_margin_pct, 2) as net_profit_margin_pct,
  ROUND(return_on_equity_pct, 2) as return_on_equity_pct
FROM ranked_companies
WHERE sector_rank <= 3
ORDER BY sector, sector_rank;

-- Query 5: Peer Group Analysis for Specific Company
-- Replace 'AAPL' with any ticker
WITH target_company AS (
  SELECT sector, fiscal_year
  FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
  WHERE ticker = 'AAPL'
    AND fiscal_year = 2023
  LIMIT 1
)
SELECT
  CASE WHEN pc.ticker = 'AAPL' THEN '>>> TARGET <<<' ELSE '' END as target_flag,
  pc.company_name,
  pc.ticker,
  ROUND(pc.revenue / 1000000000, 2) as revenue_billions,
  ROUND(pc.gross_margin_pct, 2) as gross_margin_pct,
  ROUND(pc.operating_margin_pct, 2) as operating_margin_pct,
  ROUND(pc.net_profit_margin_pct, 2) as net_profit_margin_pct,
  ROUND(pc.return_on_equity_pct, 2) as roe_pct,
  ROUND(pc.net_margin_percentile, 0) as net_margin_percentile
FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison` pc
CROSS JOIN target_company tc
WHERE pc.sector = tc.sector
  AND pc.fiscal_year = tc.fiscal_year
  AND pc.revenue > 10000000000 -- $10B+ revenue
ORDER BY pc.net_margin_percentile DESC;

-- Query 6: Market Share Analysis within Sector
WITH sector_totals AS (
  SELECT
    sector,
    fiscal_year,
    SUM(revenue) as total_sector_revenue
  FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison`
  WHERE fiscal_year = 2023
    AND sector IS NOT NULL
  GROUP BY sector, fiscal_year
)
SELECT
  pc.sector,
  pc.company_name,
  pc.ticker,
  ROUND(pc.revenue / 1000000000, 2) as revenue_billions,
  ROUND(st.total_sector_revenue / 1000000000, 2) as sector_revenue_billions,
  ROUND(SAFE_DIVIDE(pc.revenue, st.total_sector_revenue) * 100, 2) as market_share_pct,
  ROUND(pc.revenue_percentile, 0) as revenue_percentile
FROM `${PROJECT_ID}.gold_sec.looker_peer_comparison` pc
JOIN sector_totals st ON pc.sector = st.sector AND pc.fiscal_year = st.fiscal_year
WHERE pc.fiscal_year = 2023
  AND pc.revenue_percentile >= 90 -- Top 10% by revenue
ORDER BY pc.sector, market_share_pct DESC;
