-- Silver Layer Tables
-- Cleaned, normalized dimension and fact tables

-- Dimension Table: dim_companies
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.silver_sec.dim_companies` (
  cik STRING NOT NULL OPTIONS(description="Central Index Key - unique company identifier"),
  company_name STRING OPTIONS(description="Official registered company name"),
  ticker STRING OPTIONS(description="Primary stock ticker symbol"),
  exchange STRING OPTIONS(description="Primary stock exchange"),
  sic_code STRING OPTIONS(description="Standard Industrial Classification code"),
  industry STRING OPTIONS(description="Industry classification"),
  sector STRING OPTIONS(description="Business sector"),
  first_filing_year INT64 OPTIONS(description="Year of first SEC filing in dataset"),
  last_filing_year INT64 OPTIONS(description="Year of most recent SEC filing in dataset"),
  total_filings INT64 OPTIONS(description="Total number of filings in dataset"),
  created_at TIMESTAMP OPTIONS(description="Record creation timestamp"),
  updated_at TIMESTAMP OPTIONS(description="Record last update timestamp")
)
CLUSTER BY cik
OPTIONS(
  description="Company dimension table with master company information and filing statistics",
  labels=[("layer", "silver"), ("type", "dimension")]
);

-- Dimension Table: dim_taxonomy
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.silver_sec.dim_taxonomy` (
  concept STRING NOT NULL OPTIONS(description="US-GAAP concept name (e.g., Revenues, Assets)"),
  statement_type STRING OPTIONS(description="Financial statement category (income_statement, balance_sheet, cash_flow)"),
  concept_label STRING OPTIONS(description="Human-readable concept label"),
  data_type STRING OPTIONS(description="Data type (monetary, shares, percentage, pure)"),
  period_type STRING OPTIONS(description="Period type (instant or duration)"),
  balance_type STRING OPTIONS(description="Balance type (debit or credit)"),
  companies_using INT64 OPTIONS(description="Number of companies reporting this concept"),
  total_usage_count INT64 OPTIONS(description="Total number of times concept appears in dataset"),
  first_used_year INT64 OPTIONS(description="First fiscal year this concept was used"),
  last_used_year INT64 OPTIONS(description="Most recent fiscal year this concept was used"),
  created_at TIMESTAMP OPTIONS(description="Record creation timestamp"),
  updated_at TIMESTAMP OPTIONS(description="Record last update timestamp")
)
CLUSTER BY concept
OPTIONS(
  description="US-GAAP taxonomy concept dimension with usage statistics",
  labels=[("layer", "silver"), ("type", "dimension")]
);

-- Dimension Table: dim_dates
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.silver_sec.dim_dates` (
  date DATE NOT NULL OPTIONS(description="Calendar date"),
  year INT64 OPTIONS(description="Calendar year"),
  quarter INT64 OPTIONS(description="Calendar quarter (1-4)"),
  month INT64 OPTIONS(description="Month number (1-12)"),
  day INT64 OPTIONS(description="Day of month (1-31)"),
  day_of_week INT64 OPTIONS(description="Day of week (1=Sunday, 7=Saturday)"),
  week_of_year INT64 OPTIONS(description="Week number in year (1-53)"),
  year_quarter STRING OPTIONS(description="Year and quarter combined (e.g., 2023-Q1)"),
  year_month STRING OPTIONS(description="Year and month combined (e.g., 2023-01)")
)
CLUSTER BY date
OPTIONS(
  description="Date dimension for time-based analysis",
  labels=[("layer", "silver"), ("type", "dimension")]
);

-- Fact Table: fact_financials
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.silver_sec.fact_financials` (
  fact_id STRING NOT NULL OPTIONS(description="Surrogate key (MD5 hash of cik+concept+end_date+accession)"),
  cik STRING NOT NULL OPTIONS(description="Company CIK (foreign key to dim_companies)"),
  concept STRING NOT NULL OPTIONS(description="US-GAAP concept (foreign key to dim_taxonomy)"),
  end_date DATE OPTIONS(description="Period end date (foreign key to dim_dates)"),
  filing_date DATE OPTIONS(description="SEC filing date"),
  fiscal_year INT64 NOT NULL OPTIONS(description="Fiscal year of the fact"),
  fiscal_period STRING OPTIONS(description="Fiscal period (FY, Q1, Q2, Q3, Q4)"),
  year_quarter STRING OPTIONS(description="Fiscal year-quarter (e.g., 2023-Q1)"),
  form STRING OPTIONS(description="SEC form type (10-K, 10-Q, etc.)"),
  accession_number STRING OPTIONS(description="SEC filing accession number"),
  value FLOAT64 OPTIONS(description="Numeric value of the financial fact"),
  unit STRING OPTIONS(description="Unit of measure (USD, shares, pure)"),
  statement_type STRING OPTIONS(description="Statement category (income_statement, balance_sheet, cash_flow)"),
  frame STRING OPTIONS(description="Standardized time frame"),
  created_at TIMESTAMP OPTIONS(description="Record creation timestamp")
)
PARTITION BY RANGE_BUCKET(fiscal_year, GENERATE_ARRAY(2000, 2030, 1))
CLUSTER BY cik, concept, end_date
OPTIONS(
  description="Financial facts with partitioning by fiscal_year and clustering for query performance",
  labels=[("layer", "silver"), ("type", "fact")]
);

-- Fact Table: fact_submissions
CREATE TABLE IF NOT EXISTS `${PROJECT_ID}.silver_sec.fact_submissions` (
  cik STRING NOT NULL OPTIONS(description="Company CIK"),
  accession_number STRING NOT NULL OPTIONS(description="SEC filing accession number"),
  form STRING OPTIONS(description="SEC form type"),
  filing_date DATE OPTIONS(description="Filing submission date"),
  fiscal_year INT64 OPTIONS(description="Fiscal year of the filing"),
  fiscal_period STRING OPTIONS(description="Fiscal period"),
  concepts_reported INT64 OPTIONS(description="Number of unique concepts in this filing"),
  total_facts INT64 OPTIONS(description="Total number of facts in this filing"),
  income_statement_facts INT64 OPTIONS(description="Number of income statement facts"),
  balance_sheet_facts INT64 OPTIONS(description="Number of balance sheet facts"),
  cash_flow_facts INT64 OPTIONS(description="Number of cash flow statement facts"),
  created_at TIMESTAMP OPTIONS(description="Record creation timestamp")
)
PARTITION BY RANGE_BUCKET(fiscal_year, GENERATE_ARRAY(2000, 2030, 1))
CLUSTER BY cik, filing_date
OPTIONS(
  description="Filing-level summary statistics",
  labels=[("layer", "silver"), ("type", "fact")]
);
