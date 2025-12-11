"""
SEC EDGAR Data Pipeline DAG

This DAG orchestrates the complete SEC EDGAR data processing pipeline:
1. Check for new SEC data updates
2. Download bulk files (companyfacts.zip, submissions.zip)
3. Process XBRL data with PySpark on Dataproc Serverless
4. Validate data quality in BigQuery
5. Refresh Looker materialized views
6. Send completion notification

Schedule: Daily at 2 AM EST
"""

from datetime import datetime, timedelta
from typing import Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.google.cloud.operators.functions import CloudFunctionsInvokeFunctionOperator
from airflow.providers.google.cloud.operators.dataproc import DataprocCreateBatchOperator
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryCheckOperator,
    BigQueryExecuteQueryOperator,
)
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.operators.email import EmailOperator
from airflow.utils.task_group import TaskGroup

# Import custom operators
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from operators.bigquery_quality_check import BigQueryDataQualityOperator
from operators.looker_refresh import LookerMaterializedViewRefreshOperator


# Configuration
PROJECT_ID = "{{ var.value.gcp_project_id }}"
REGION = "{{ var.value.gcp_region }}"
RAW_BUCKET = "{{ var.value.gcs_raw_bucket }}"
PROCESSED_BUCKET = "{{ var.value.gcs_processed_bucket }}"
DATAPROC_BATCH_ID_PREFIX = "sec-edgar-processing"
BRONZE_DATASET = "bronze_sec"
SILVER_DATASET = "silver_sec"
GOLD_DATASET = "gold_sec"
NOTIFICATION_EMAIL = "{{ var.value.notification_email }}"

# Default DAG arguments
default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email": [NOTIFICATION_EMAIL],
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(hours=4),
}


def check_sec_updates(**context) -> Dict[str, Any]:
    """Check if new SEC data is available.

    In production, this would check SEC's update timestamps.
    For now, returns current execution date.
    """
    execution_date = context["execution_date"]

    return {
        "has_updates": True,
        "execution_year": execution_date.year,
        "execution_date": execution_date.strftime("%Y-%m-%d"),
    }


def generate_batch_id(**context) -> str:
    """Generate unique Dataproc batch ID."""
    execution_date = context["execution_date"]
    return f"{DATAPROC_BATCH_ID_PREFIX}-{execution_date.strftime('%Y%m%d-%H%M%S')}"


# Create the DAG
with DAG(
    dag_id="sec_edgar_pipeline",
    default_args=default_args,
    description="SEC EDGAR data ingestion, processing, and analytics pipeline",
    schedule_interval="0 2 * * *",  # Daily at 2 AM EST (7 AM UTC)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["sec", "edgar", "financial-data", "production"],
) as dag:

    # Task 1: Check for SEC updates
    check_updates = PythonOperator(
        task_id="check_sec_updates",
        python_callable=check_sec_updates,
        provide_context=True,
    )

    # Task Group 2: Data Ingestion
    with TaskGroup("data_ingestion", tooltip="Download SEC bulk data files") as ingestion_group:

        # Invoke Cloud Function to download companyfacts.zip
        download_companyfacts = CloudFunctionsInvokeFunctionOperator(
            task_id="download_companyfacts",
            function_name="sec-data-ingestion",
            location=REGION,
            project_id=PROJECT_ID,
            input_data={
                "file_types": ["companyfacts"],
                "year": "{{ ti.xcom_pull(task_ids='check_sec_updates')['execution_year'] }}"
            },
        )

        # Invoke Cloud Function to download submissions.zip
        download_submissions = CloudFunctionsInvokeFunctionOperator(
            task_id="download_submissions",
            function_name="sec-data-ingestion",
            location=REGION,
            project_id=PROJECT_ID,
            input_data={
                "file_types": ["submissions"],
                "year": "{{ ti.xcom_pull(task_ids='check_sec_updates')['execution_year'] }}"
            },
        )

        # Verify files were uploaded to GCS
        verify_companyfacts = GCSObjectExistenceSensor(
            task_id="verify_companyfacts_uploaded",
            bucket=RAW_BUCKET,
            object="bulk/{{ ti.xcom_pull(task_ids='check_sec_updates')['execution_year'] }}/companyfacts.zip",
            timeout=600,
            poke_interval=30,
        )

        verify_submissions = GCSObjectExistenceSensor(
            task_id="verify_submissions_uploaded",
            bucket=RAW_BUCKET,
            object="bulk/{{ ti.xcom_pull(task_ids='check_sec_updates')['execution_year'] }}/submissions.zip",
            timeout=600,
            poke_interval=30,
        )

        download_companyfacts >> verify_companyfacts
        download_submissions >> verify_submissions

    # Task Group 3: Data Processing (PySpark on Dataproc Serverless)
    with TaskGroup("data_processing", tooltip="Process XBRL data with PySpark") as processing_group:

        # Parse XBRL data
        parse_xbrl = DataprocCreateBatchOperator(
            task_id="parse_xbrl_data",
            project_id=PROJECT_ID,
            region=REGION,
            batch_id="{{ ti.xcom_pull(task_ids='generate_batch_id') }}-parse-xbrl",
            batch={
                "pyspark_batch": {
                    "main_python_file_uri": f"gs://{PROCESSED_BUCKET}/spark-jobs/parse_xbrl.py",
                    "args": [
                        f"gs://{RAW_BUCKET}/bulk/{{{{ ti.xcom_pull(task_ids='check_sec_updates')['execution_year'] }}}}/companyfacts.zip",
                        BRONZE_DATASET,
                    ],
                    "jar_file_uris": [
                        "gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.32.2.jar"
                    ],
                },
                "runtime_config": {
                    "version": "2.0",
                },
                "environment_config": {
                    "execution_config": {
                        "service_account": f"sec-dataproc-sa@{PROJECT_ID}.iam.gserviceaccount.com",
                    }
                },
            },
        )

        # Create dimension tables
        create_dimensions = DataprocCreateBatchOperator(
            task_id="create_dimension_tables",
            project_id=PROJECT_ID,
            region=REGION,
            batch_id="{{ ti.xcom_pull(task_ids='generate_batch_id') }}-dimensions",
            batch={
                "pyspark_batch": {
                    "main_python_file_uri": f"gs://{PROCESSED_BUCKET}/spark-jobs/create_dimensions.py",
                    "args": [BRONZE_DATASET, SILVER_DATASET],
                    "jar_file_uris": [
                        "gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.32.2.jar"
                    ],
                },
                "runtime_config": {
                    "version": "2.0",
                },
                "environment_config": {
                    "execution_config": {
                        "service_account": f"sec-dataproc-sa@{PROJECT_ID}.iam.gserviceaccount.com",
                    }
                },
            },
        )

        # Create fact tables
        create_facts = DataprocCreateBatchOperator(
            task_id="create_fact_tables",
            project_id=PROJECT_ID,
            region=REGION,
            batch_id="{{ ti.xcom_pull(task_ids='generate_batch_id') }}-facts",
            batch={
                "pyspark_batch": {
                    "main_python_file_uri": f"gs://{PROCESSED_BUCKET}/spark-jobs/create_facts.py",
                    "args": [BRONZE_DATASET, SILVER_DATASET],
                    "jar_file_uris": [
                        "gs://spark-lib/bigquery/spark-bigquery-with-dependencies_2.12-0.32.2.jar"
                    ],
                },
                "runtime_config": {
                    "version": "2.0",
                },
                "environment_config": {
                    "execution_config": {
                        "service_account": f"sec-dataproc-sa@{PROJECT_ID}.iam.gserviceaccount.com",
                    }
                },
            },
        )

        parse_xbrl >> create_dimensions
        parse_xbrl >> create_facts

    # Task 4: Data Quality Validation
    with TaskGroup("data_quality", tooltip="Validate data quality") as quality_group:

        # Check row counts
        check_companies_count = BigQueryCheckOperator(
            task_id="check_companies_count",
            sql=f"""
                SELECT COUNT(*) >= 100
                FROM `{PROJECT_ID}.{SILVER_DATASET}.dim_companies`
            """,
            use_legacy_sql=False,
        )

        check_financials_count = BigQueryCheckOperator(
            task_id="check_financials_count",
            sql=f"""
                SELECT COUNT(*) >= 1000
                FROM `{PROJECT_ID}.{SILVER_DATASET}.fact_financials`
            """,
            use_legacy_sql=False,
        )

        # Custom data quality checks
        quality_checks = BigQueryDataQualityOperator(
            task_id="run_data_quality_checks",
            project_id=PROJECT_ID,
            dataset_id=SILVER_DATASET,
            table_id="fact_financials",
            quality_checks=[
                {
                    "name": "null_check_critical_fields",
                    "sql": f"""
                        SELECT COUNT(*) = 0
                        FROM `{PROJECT_ID}.{SILVER_DATASET}.fact_financials`
                        WHERE cik IS NULL OR concept IS NULL OR value IS NULL
                    """,
                },
                {
                    "name": "valid_fiscal_years",
                    "sql": f"""
                        SELECT COUNT(*) = 0
                        FROM `{PROJECT_ID}.{SILVER_DATASET}.fact_financials`
                        WHERE fiscal_year < 2000 OR fiscal_year > 2030
                    """,
                },
                {
                    "name": "data_quality_flag_check",
                    "sql": f"""
                        SELECT SUM(CASE WHEN data_quality_passed THEN 1 ELSE 0 END) * 100.0 / COUNT(*) >= 95
                        FROM `{PROJECT_ID}.{BRONZE_DATASET}.raw_financials`
                    """,
                },
            ],
        )

        [check_companies_count, check_financials_count] >> quality_checks

    # Task 5: Refresh Looker Materialized Views
    with TaskGroup("refresh_looker_views", tooltip="Refresh analytics views") as looker_group:

        refresh_company_metrics = LookerMaterializedViewRefreshOperator(
            task_id="refresh_company_metrics",
            project_id=PROJECT_ID,
            dataset_id=GOLD_DATASET,
            view_id="looker_company_metrics",
        )

        refresh_financial_ratios = LookerMaterializedViewRefreshOperator(
            task_id="refresh_financial_ratios",
            project_id=PROJECT_ID,
            dataset_id=GOLD_DATASET,
            view_id="looker_financial_ratios",
        )

        refresh_peer_comparison = LookerMaterializedViewRefreshOperator(
            task_id="refresh_peer_comparison",
            project_id=PROJECT_ID,
            dataset_id=GOLD_DATASET,
            view_id="looker_peer_comparison",
        )

        refresh_timeseries = LookerMaterializedViewRefreshOperator(
            task_id="refresh_timeseries",
            project_id=PROJECT_ID,
            dataset_id=GOLD_DATASET,
            view_id="looker_timeseries",
        )

        # All refreshes can run in parallel
        [refresh_company_metrics, refresh_financial_ratios,
         refresh_peer_comparison, refresh_timeseries]

    # Task 6: Send Success Notification
    send_success_notification = EmailOperator(
        task_id="send_success_notification",
        to=[NOTIFICATION_EMAIL],
        subject="✅ SEC EDGAR Pipeline Completed - {{ ds }}",
        html_content="""
        <h3>SEC EDGAR Data Pipeline Completed Successfully</h3>
        <p><strong>Execution Date:</strong> {{ ds }}</p>
        <p><strong>Execution Time:</strong> {{ execution_date }}</p>

        <h4>Pipeline Steps Completed:</h4>
        <ul>
            <li>✅ SEC data ingestion</li>
            <li>✅ XBRL data processing</li>
            <li>✅ Dimension and fact table creation</li>
            <li>✅ Data quality validation</li>
            <li>✅ Looker materialized view refresh</li>
        </ul>

        <p><strong>Next Steps:</strong></p>
        <ul>
            <li>Review data in BigQuery datasets</li>
            <li>Check Looker dashboards for updated metrics</li>
        </ul>

        <p><em>Automated notification from Airflow DAG: sec_edgar_pipeline</em></p>
        """,
    )

    # Generate batch ID task
    gen_batch_id = PythonOperator(
        task_id="generate_batch_id",
        python_callable=generate_batch_id,
        provide_context=True,
    )

    # Define task dependencies
    check_updates >> gen_batch_id >> ingestion_group >> processing_group >> quality_group >> looker_group >> send_success_notification
