-- Bronze Layer Tables
-- Raw data from SEC EDGAR with minimal transformations

-- Table: raw_companies
-- Description: Raw company information from SEC companyfacts
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.bronze_sec.raw_companies` (
  cik STRING OPTIONS(description="Central Index Key (CIK) - SEC company identifier"),
  cik_padded STRING OPTIONS(description="CIK padded to 10 digits with leading zeros"),
  company_name STRING OPTIONS(description="Official company name registered with SEC"),
  ticker STRING OPTIONS(description="Stock ticker symbol (primary exchange)"),
  exchange STRING OPTIONS(description="Primary stock exchange (NYSE, NASDAQ, etc.)"),
  created_at TIMESTAMP OPTIONS(description="Record creation timestamp")
)
PARTITION BY DATE(created_at)
OPTIONS(
  description="Raw company master data from SEC EDGAR",
  labels=[("layer", "bronze"), ("source", "sec-edgar")]
);

-- Table: raw_financials
-- Description: Raw financial facts from XBRL filings
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.bronze_sec.raw_financials` (
  cik STRING OPTIONS(description="Central Index Key"),
  cik_padded STRING OPTIONS(description="CIK padded to 10 digits"),
  company_name STRING OPTIONS(description="Company name"),
  concept STRING OPTIONS(description="US-GAAP concept name (e.g., Revenues, Assets)"),
  unit STRING OPTIONS(description="Unit of measure (USD, shares, pure)"),
  end_date STRING OPTIONS(description="Period end date for the financial fact"),
  value FLOAT64 OPTIONS(description="Numeric value of the financial fact"),
  accession_number STRING OPTIONS(description="SEC filing accession number"),
  fiscal_year INT64 OPTIONS(description="Fiscal year of the filing"),
  fiscal_period STRING OPTIONS(description="Fiscal period (FY, Q1, Q2, Q3, Q4)"),
  form STRING OPTIONS(description="SEC form type (10-K, 10-Q, 8-K, etc.)"),
  filed_date STRING OPTIONS(description="Date the filing was submitted to SEC"),
  frame STRING OPTIONS(description="Standardized time frame (e.g., CY2023Q1)"),
  statement_type STRING OPTIONS(description="Financial statement category (income_statement, balance_sheet, cash_flow, other)"),
  year_quarter STRING OPTIONS(description="Fiscal year and quarter combined (e.g., 2023-Q1)"),
  has_null_critical BOOLEAN OPTIONS(description="Data quality flag: true if critical fields are null"),
  invalid_fiscal_year BOOLEAN OPTIONS(description="Data quality flag: true if fiscal year is out of valid range"),
  data_quality_passed BOOLEAN OPTIONS(description="Overall data quality flag: true if all checks passed"),
  created_at TIMESTAMP OPTIONS(description="Record creation timestamp")
)
PARTITION BY fiscal_year
CLUSTER BY cik_padded, concept
OPTIONS(
  description="Raw financial facts from SEC XBRL filings with data quality flags",
  labels=[("layer", "bronze"), ("source", "sec-edgar")]
);

-- Add column descriptions for better documentation
COMMENT ON COLUMN `${PROJECT_ID}.bronze_sec.raw_financials`.concept IS
  'US-GAAP taxonomy concept. Common values: Revenues, NetIncomeLoss, Assets, Liabilities, CashAndCashEquivalentsAtCarryingValue';

COMMENT ON COLUMN `${PROJECT_ID}.bronze_sec.raw_financials`.fiscal_period IS
  'FY = Full Year, Q1/Q2/Q3/Q4 = Quarters';
