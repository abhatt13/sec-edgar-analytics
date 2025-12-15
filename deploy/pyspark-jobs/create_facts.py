"""PySpark job to create fact tables in BigQuery."""

import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from config import SparkConfig


logger = logging.getLogger(__name__)


class FactBuilder:
    """Build fact tables from raw SEC data."""

    def __init__(self, spark: SparkSession, config: SparkConfig):
        """Initialize fact builder.

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
        partition_column: str = None,
        cluster_columns: list = None,
        mode: str = "overwrite"
    ) -> None:
        """Write DataFrame to BigQuery with partitioning and clustering.

        Args:
            df: DataFrame to write
            table_name: Target table name
            dataset: BigQuery dataset
            partition_column: Column to partition by
            cluster_columns: Columns to cluster by
            mode: Write mode
        """
        table_id = f"{self.config.GCP_PROJECT_ID}.{dataset}.{table_name}"

        logger.info(f"Writing to BigQuery table: {table_id}")

        writer = df.write.format("bigquery") \
            .option("table", table_id) \
            .option("writeMethod", "direct")

        if partition_column:
            writer = writer.option("partitionField", partition_column) \
                           .option("partitionType", "YEAR")

        if cluster_columns:
            writer = writer.option("clusteredFields", ",".join(cluster_columns))

        writer.mode(mode).save()

        logger.info(f"Successfully wrote {df.count()} records to {table_id}")

    def create_fact_financials(self, raw_financials_df: DataFrame) -> DataFrame:
        """Create financial facts table.

        Args:
            raw_financials_df: Raw financials data

        Returns:
            Financial facts DataFrame
        """
        logger.info("Creating fact_financials")

        # Filter to quality-passed records
        fact_financials = raw_financials_df.filter(
            F.col("data_quality_passed") == True
        )

        # Select and transform columns
        fact_financials = fact_financials.select(
            F.col("cik_padded").alias("cik"),
            F.col("concept"),
            F.to_date(F.col("end_date")).alias("end_date"),
            F.to_date(F.col("filed_date")).alias("filing_date"),
            F.col("fiscal_year"),
            F.col("fiscal_period"),
            F.col("year_quarter"),
            F.col("form"),
            F.col("accession_number"),
            F.col("value"),
            F.col("unit"),
            F.col("statement_type"),
            F.col("frame"),
        )

        # Add surrogate key
        fact_financials = fact_financials.withColumn(
            "fact_id",
            F.md5(
                F.concat(
                    F.col("cik"),
                    F.col("concept"),
                    F.col("end_date"),
                    F.col("accession_number")
                )
            )
        )

        # Handle duplicates - keep most recent filing
        window_spec = Window.partitionBy(
            "cik", "concept", "end_date", "fiscal_year", "fiscal_period"
        ).orderBy(F.col("filing_date").desc())

        fact_financials = fact_financials.withColumn(
            "row_num", F.row_number().over(window_spec)
        ).filter(F.col("row_num") == 1).drop("row_num")

        # Add metadata
        fact_financials = fact_financials.withColumn(
            "created_at", F.current_timestamp()
        )

        logger.info(f"Created fact_financials with {fact_financials.count()} records")
        return fact_financials

    def create_fact_submissions(self, raw_financials_df: DataFrame) -> DataFrame:
        """Create submissions fact table (aggregated by filing).

        Args:
            raw_financials_df: Raw financials data

        Returns:
            Submissions fact DataFrame
        """
        logger.info("Creating fact_submissions")

        # Aggregate metrics by accession number
        fact_submissions = raw_financials_df.groupBy(
            F.col("cik_padded").alias("cik"),
            F.col("accession_number"),
            F.col("form"),
            F.to_date(F.col("filed_date")).alias("filing_date"),
            F.col("fiscal_year"),
            F.col("fiscal_period"),
        ).agg(
            F.countDistinct("concept").alias("concepts_reported"),
            F.count("*").alias("total_facts"),
            F.sum(
                F.when(F.col("statement_type") == "income_statement", 1).otherwise(0)
            ).alias("income_statement_facts"),
            F.sum(
                F.when(F.col("statement_type") == "balance_sheet", 1).otherwise(0)
            ).alias("balance_sheet_facts"),
            F.sum(
                F.when(F.col("statement_type") == "cash_flow", 1).otherwise(0)
            ).alias("cash_flow_facts"),
        )

        # Add metadata
        fact_submissions = fact_submissions.withColumn(
            "created_at", F.current_timestamp()
        )

        logger.info(f"Created fact_submissions with {fact_submissions.count()} records")
        return fact_submissions


def main(
    bronze_dataset: str = "bronze_sec",
    silver_dataset: str = "silver_sec"
) -> None:
    """Main entry point for fact table creation job.

    Args:
        bronze_dataset: Source BigQuery dataset
        silver_dataset: Target BigQuery dataset
    """
    # Initialize Spark
    spark = SparkSession.builder \
        .appName("SEC-Create-Facts") \
        .config("spark.jars.packages", "com.google.cloud.spark:spark-bigquery-with-dependencies_2.12:0.32.2") \
        .getOrCreate()

    try:
        # Initialize configuration
        config = SparkConfig()

        # Initialize builder
        builder = FactBuilder(spark, config)

        # Read raw financials
        raw_financials_df = builder.read_from_bigquery("raw_financials", bronze_dataset)

        # Create fact tables
        fact_financials = builder.create_fact_financials(raw_financials_df)
        builder.write_to_bigquery(
            fact_financials,
            "fact_financials",
            silver_dataset,
            partition_column="fiscal_year",
            cluster_columns=["cik", "concept", "end_date"]
        )

        fact_submissions = builder.create_fact_submissions(raw_financials_df)
        builder.write_to_bigquery(
            fact_submissions,
            "fact_submissions",
            silver_dataset,
            partition_column="fiscal_year",
            cluster_columns=["cik", "filing_date"]
        )

        logger.info("Fact table creation job completed successfully")

    except Exception as e:
        logger.error(f"Error in fact table creation job: {e}")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    import sys

    bronze_dataset = sys.argv[1] if len(sys.argv) > 1 else "bronze_sec"
    silver_dataset = sys.argv[2] if len(sys.argv) > 2 else "silver_sec"

    main(bronze_dataset, silver_dataset)
