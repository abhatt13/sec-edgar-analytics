"""PySpark job to create dimension tables in BigQuery."""

import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, IntegerType

from .config import SparkConfig


logger = logging.getLogger(__name__)


class DimensionBuilder:
    """Build dimension tables from raw SEC data."""

    def __init__(self, spark: SparkSession, config: SparkConfig):
        """Initialize dimension builder.

        Args:
            spark: SparkSession instance
            config: Spark configuration
        """
        self.spark = spark
        self.config = config

    def read_from_bigquery(self, table_name: str, dataset: str) -> DataFrame:
        """Read DataFrame from BigQuery.

        Args:
            table_name: Source table name
            dataset: BigQuery dataset

        Returns:
            DataFrame
        """
        table_id = f"{self.config.GCP_PROJECT_ID}.{dataset}.{table_name}"
        logger.info(f"Reading from BigQuery table: {table_id}")

        df = self.spark.read.format("bigquery").option("table", table_id).load()

        logger.info(f"Read {df.count()} records from {table_id}")
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
            mode: Write mode
        """
        table_id = f"{self.config.GCP_PROJECT_ID}.{dataset}.{table_name}"

        logger.info(f"Writing to BigQuery table: {table_id}")

        df.write.format("bigquery") \
            .option("table", table_id) \
            .option("writeMethod", "direct") \
            .mode(mode) \
            .save()

        logger.info(f"Successfully wrote {df.count()} records to {table_id}")

    def create_dim_companies(self, raw_companies_df: DataFrame, raw_financials_df: DataFrame) -> DataFrame:
        """Create companies dimension table.

        Args:
            raw_companies_df: Raw companies data
            raw_financials_df: Raw financials data for enrichment

        Returns:
            Companies dimension DataFrame
        """
        logger.info("Creating dim_companies")

        # Start with company base info
        dim_companies = raw_companies_df.select(
            F.col("cik_padded").alias("cik"),
            F.col("company_name"),
            F.col("ticker"),
            F.col("exchange"),
        ).distinct()

        # Get SIC code from financials if available (from entity data)
        # Note: In real implementation, this would come from submissions data
        # For now, we'll add placeholder columns

        dim_companies = dim_companies.withColumn(
            "sic_code", F.lit(None).cast(StringType())
        ).withColumn(
            "industry", F.lit(None).cast(StringType())
        ).withColumn(
            "sector", F.lit(None).cast(StringType())
        )

        # Add metadata columns
        dim_companies = dim_companies.withColumn(
            "created_at", F.current_timestamp()
        ).withColumn(
            "updated_at", F.current_timestamp()
        )

        # Get filing statistics from financials
        filing_stats = raw_financials_df.groupBy("cik_padded").agg(
            F.min("fiscal_year").alias("first_filing_year"),
            F.max("fiscal_year").alias("last_filing_year"),
            F.countDistinct("accession_number").alias("total_filings"),
        )

        # Join with stats
        dim_companies = dim_companies.join(
            filing_stats,
            dim_companies.cik == filing_stats.cik_padded,
            "left"
        ).drop(filing_stats.cik_padded)

        logger.info(f"Created dim_companies with {dim_companies.count()} records")
        return dim_companies

    def create_dim_taxonomy(self, raw_financials_df: DataFrame) -> DataFrame:
        """Create taxonomy dimension table.

        Args:
            raw_financials_df: Raw financials data

        Returns:
            Taxonomy dimension DataFrame
        """
        logger.info("Creating dim_taxonomy")

        # Extract unique concepts with their metadata
        dim_taxonomy = raw_financials_df.select(
            F.col("concept"),
            F.col("statement_type"),
        ).distinct()

        # Add concept metadata
        # In production, this would be enriched from XBRL taxonomy files
        dim_taxonomy = dim_taxonomy.withColumn(
            "concept_label",
            F.regexp_replace(F.col("concept"), "([A-Z])", " $1")
        ).withColumn(
            "data_type", F.lit("monetary").cast(StringType())
        ).withColumn(
            "period_type", F.lit("duration").cast(StringType())
        ).withColumn(
            "balance_type", F.lit(None).cast(StringType())
        )

        # Add usage statistics
        usage_stats = raw_financials_df.groupBy("concept").agg(
            F.countDistinct("cik").alias("companies_using"),
            F.count("*").alias("total_usage_count"),
            F.min("fiscal_year").alias("first_used_year"),
            F.max("fiscal_year").alias("last_used_year"),
        )

        dim_taxonomy = dim_taxonomy.join(usage_stats, "concept", "left")

        # Add metadata
        dim_taxonomy = dim_taxonomy.withColumn(
            "created_at", F.current_timestamp()
        ).withColumn(
            "updated_at", F.current_timestamp()
        )

        logger.info(f"Created dim_taxonomy with {dim_taxonomy.count()} records")
        return dim_taxonomy

    def create_dim_dates(self, raw_financials_df: DataFrame) -> DataFrame:
        """Create date dimension table.

        Args:
            raw_financials_df: Raw financials data

        Returns:
            Date dimension DataFrame
        """
        logger.info("Creating dim_dates")

        # Extract unique dates
        dates_df = raw_financials_df.select(
            F.to_date(F.col("end_date")).alias("date")
        ).distinct().filter(F.col("date").isNotNull())

        # Add date attributes
        dim_dates = dates_df.withColumn(
            "year", F.year(F.col("date"))
        ).withColumn(
            "quarter", F.quarter(F.col("date"))
        ).withColumn(
            "month", F.month(F.col("date"))
        ).withColumn(
            "day", F.dayofmonth(F.col("date"))
        ).withColumn(
            "day_of_week", F.dayofweek(F.col("date"))
        ).withColumn(
            "week_of_year", F.weekofyear(F.col("date"))
        ).withColumn(
            "year_quarter",
            F.concat(F.col("year"), F.lit("-Q"), F.col("quarter"))
        ).withColumn(
            "year_month",
            F.date_format(F.col("date"), "yyyy-MM")
        )

        logger.info(f"Created dim_dates with {dim_dates.count()} records")
        return dim_dates


def main(
    bronze_dataset: str = "bronze_sec",
    silver_dataset: str = "silver_sec"
) -> None:
    """Main entry point for dimension creation job.

    Args:
        bronze_dataset: Source BigQuery dataset
        silver_dataset: Target BigQuery dataset
    """
    # Initialize Spark
    spark = SparkSession.builder \
        .appName("SEC-Create-Dimensions") \
        .config("spark.jars.packages", "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2") \
        .getOrCreate()

    try:
        # Initialize configuration
        config = SparkConfig()

        # Initialize builder
        builder = DimensionBuilder(spark, config)

        # Read raw data
        raw_companies_df = builder.read_from_bigquery("raw_companies", bronze_dataset)
        raw_financials_df = builder.read_from_bigquery("raw_financials", bronze_dataset)

        # Filter to quality-passed records
        raw_financials_df = raw_financials_df.filter(F.col("data_quality_passed") == True)

        # Create dimension tables
        dim_companies = builder.create_dim_companies(raw_companies_df, raw_financials_df)
        builder.write_to_bigquery(dim_companies, "dim_companies", silver_dataset)

        dim_taxonomy = builder.create_dim_taxonomy(raw_financials_df)
        builder.write_to_bigquery(dim_taxonomy, "dim_taxonomy", silver_dataset)

        dim_dates = builder.create_dim_dates(raw_financials_df)
        builder.write_to_bigquery(dim_dates, "dim_dates", silver_dataset)

        logger.info("Dimension creation job completed successfully")

    except Exception as e:
        logger.error(f"Error in dimension creation job: {e}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    import sys

    bronze_dataset = sys.argv[1] if len(sys.argv) > 1 else "bronze_sec"
    silver_dataset = sys.argv[2] if len(sys.argv) > 2 else "silver_sec"

    main(bronze_dataset, silver_dataset)
