"""PySpark job to parse XBRL JSON from SEC companyfacts.zip."""

import json
import logging
from typing import Dict, List, Any, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType,
    DoubleType,
    IntegerType,
    ArrayType,
    MapType,
)

from config import SparkConfig, XBRLConfig


logger = logging.getLogger(__name__)


class XBRLParser:
    """Parse XBRL JSON data from SEC companyfacts files."""

    def __init__(self, spark: SparkSession, config: SparkConfig, xbrl_config: XBRLConfig):
        """Initialize XBRL parser.

        Args:
            spark: SparkSession instance
            config: Spark configuration
            xbrl_config: XBRL parsing configuration
        """
        self.spark = spark
        self.config = config
        self.xbrl_config = xbrl_config

    def read_companyfacts_zip(self, gcs_path: str) -> DataFrame:
        """Read companyfacts.zip from GCS.

        Args:
            gcs_path: GCS path to companyfacts.zip

        Returns:
            DataFrame with raw JSON data
        """
        logger.info(f"Reading companyfacts from {gcs_path}")

        # Read JSON files from the zip archive
        df = self.spark.read.json(gcs_path)

        logger.info(f"Loaded {df.count()} company records")
        return df

    def extract_company_info(self, df: DataFrame) -> DataFrame:
        """Extract company dimension data.

        Args:
            df: Raw companyfacts DataFrame

        Returns:
            DataFrame with company information
        """
        logger.info("Extracting company information")

        company_df = df.select(
            F.col("cik").cast(StringType()).alias("cik"),
            F.col("entityName").alias("company_name"),
            F.col("tickers").getItem(0).alias("ticker"),
            F.col("exchanges").getItem(0).alias("exchange"),
        )

        # Add derived fields
        company_df = company_df.withColumn(
            "cik_padded", F.lpad(F.col("cik"), 10, "0")
        )

        logger.info(f"Extracted {company_df.count()} companies")
        return company_df

    def extract_us_gaap_facts(self, df: DataFrame) -> DataFrame:
        """Extract US-GAAP taxonomy facts from nested structure.

        Args:
            df: Raw companyfacts DataFrame

        Returns:
            DataFrame with flattened financial facts
        """
        logger.info("Extracting US-GAAP facts")

        # Explode the facts nested structure
        # Structure: facts.us-gaap.{concept}.units.{unit}[{fact_array}]

        # First, explode the us-gaap concepts
        facts_df = df.select(
            F.col("cik").cast(StringType()).alias("cik"),
            F.col("entityName").alias("company_name"),
            F.explode(F.map_keys(F.col("facts.us-gaap"))).alias("concept"),
        )

        # Get the concept data
        facts_df = facts_df.withColumn(
            "concept_data",
            F.col(f"facts.us-gaap.{F.col('concept')}")
        )

        # Explode units
        facts_df = facts_df.select(
            "cik",
            "company_name",
            "concept",
            F.explode(F.map_keys(F.col("concept_data.units"))).alias("unit"),
        )

        # Get the facts array for each unit
        facts_df = facts_df.withColumn(
            "facts_array",
            F.col(f"concept_data.units.{F.col('unit')}")
        )

        # Explode the facts array
        facts_df = facts_df.select(
            "cik",
            "company_name",
            "concept",
            "unit",
            F.explode("facts_array").alias("fact")
        )

        # Extract fact details
        result_df = facts_df.select(
            F.col("cik"),
            F.col("company_name"),
            F.col("concept"),
            F.col("unit"),
            F.col("fact.end").alias("end_date"),
            F.col("fact.val").cast(DoubleType()).alias("value"),
            F.col("fact.accn").alias("accession_number"),
            F.col("fact.fy").cast(IntegerType()).alias("fiscal_year"),
            F.col("fact.fp").alias("fiscal_period"),
            F.col("fact.form").alias("form"),
            F.col("fact.filed").alias("filed_date"),
            F.col("fact.frame").alias("frame"),
        )

        # Filter to valid units and forms
        result_df = result_df.filter(
            F.col("unit").isin(self.xbrl_config.VALID_UNITS)
        ).filter(
            F.col("form").isin(self.xbrl_config.VALID_FORMS)
        )

        # Add derived columns
        result_df = result_df.withColumn(
            "cik_padded", F.lpad(F.col("cik"), 10, "0")
        ).withColumn(
            "year_quarter", F.concat(F.col("fiscal_year"), F.lit("-"), F.col("fiscal_period"))
        )

        logger.info(f"Extracted {result_df.count()} financial facts")
        return result_df

    def categorize_concepts(self, df: DataFrame) -> DataFrame:
        """Add statement category to each concept.

        Args:
            df: DataFrame with financial facts

        Returns:
            DataFrame with statement_type column added
        """
        logger.info("Categorizing concepts by financial statement")

        # Create categorization logic
        df = df.withColumn(
            "statement_type",
            F.when(
                F.col("concept").isin(self.xbrl_config.INCOME_STATEMENT_CONCEPTS),
                "income_statement"
            ).when(
                F.col("concept").isin(self.xbrl_config.BALANCE_SHEET_CONCEPTS),
                "balance_sheet"
            ).when(
                F.col("concept").isin(self.xbrl_config.CASH_FLOW_CONCEPTS),
                "cash_flow"
            ).otherwise("other")
        )

        return df

    def apply_data_quality_checks(self, df: DataFrame) -> DataFrame:
        """Apply data quality validations.

        Args:
            df: DataFrame to validate

        Returns:
            DataFrame with quality flags added
        """
        logger.info("Applying data quality checks")

        # Check for nulls in critical columns
        df = df.withColumn(
            "has_null_critical",
            F.when(
                F.col("cik").isNull()
                | F.col("concept").isNull()
                | F.col("value").isNull()
                | F.col("fiscal_year").isNull(),
                True
            ).otherwise(False)
        )

        # Check for invalid fiscal years
        df = df.withColumn(
            "invalid_fiscal_year",
            F.when(
                (F.col("fiscal_year") < 1900) | (F.col("fiscal_year") > 2100),
                True
            ).otherwise(False)
        )

        # Overall quality flag
        df = df.withColumn(
            "data_quality_passed",
            ~F.col("has_null_critical") & ~F.col("invalid_fiscal_year")
        )

        # Log quality metrics
        total_count = df.count()
        passed_count = df.filter(F.col("data_quality_passed")).count()
        logger.info(f"Data quality: {passed_count}/{total_count} records passed")

        return df

    def write_to_bigquery(
        self,
        df: DataFrame,
        table_name: str,
        dataset: str,
        mode: str = "overwrite"
    ) -> None:
        """Write DataFrame to BigQuery.

        Args:
            df: DataFrame to write
            table_name: Target table name
            dataset: BigQuery dataset
            mode: Write mode (overwrite, append)
        """
        table_id = f"{self.config.GCP_PROJECT_ID}.{dataset}.{table_name}"

        logger.info(f"Writing to BigQuery table: {table_id}")

        df.write.format("bigquery") \
            .option("table", table_id) \
            .option("writeMethod", "direct") \
            .mode(mode) \
            .save()

        logger.info(f"Successfully wrote {df.count()} records to {table_id}")


def main(companyfacts_path: str, output_dataset: str = "bronze_sec") -> None:
    """Main entry point for XBRL parsing job.

    Args:
        companyfacts_path: GCS path to companyfacts.zip
        output_dataset: Target BigQuery dataset
    """
    # Initialize Spark
    spark = SparkSession.builder \
        .appName("SEC-XBRL-Parser") \
        .config("spark.jars.packages", "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2") \
        .getOrCreate()

    try:
        # Initialize configurations
        config = SparkConfig()
        xbrl_config = XBRLConfig()

        # Initialize parser
        parser = XBRLParser(spark, config, xbrl_config)

        # Read companyfacts data
        raw_df = parser.read_companyfacts_zip(companyfacts_path)

        # Extract company information
        companies_df = parser.extract_company_info(raw_df)
        parser.write_to_bigquery(companies_df, "raw_companies", output_dataset)

        # Extract and process financial facts
        facts_df = parser.extract_us_gaap_facts(raw_df)
        facts_df = parser.categorize_concepts(facts_df)
        facts_df = parser.apply_data_quality_checks(facts_df)

        # Write to BigQuery
        parser.write_to_bigquery(facts_df, "raw_financials", output_dataset)

        logger.info("XBRL parsing job completed successfully")

    except Exception as e:
        logger.error(f"Error in XBRL parsing job: {e}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: parse_xbrl.py <companyfacts_gcs_path> [output_dataset]")
        sys.exit(1)

    companyfacts_path = sys.argv[1]
    output_dataset = sys.argv[2] if len(sys.argv) > 2 else "bronze_sec"

    main(companyfacts_path, output_dataset)
