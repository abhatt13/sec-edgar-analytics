"""Custom BigQuery Data Quality Check Operator."""

from typing import List, Dict, Any
from airflow.models import BaseOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.exceptions import AirflowException


class BigQueryDataQualityOperator(BaseOperator):
    """
    Execute multiple data quality checks against BigQuery tables.

    :param project_id: GCP project ID
    :param dataset_id: BigQuery dataset ID
    :param table_id: BigQuery table ID
    :param quality_checks: List of quality check definitions
    :param gcp_conn_id: Airflow connection ID for GCP
    """

    template_fields = ("project_id", "dataset_id", "table_id")

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        table_id: str,
        quality_checks: List[Dict[str, str]],
        gcp_conn_id: str = "google_cloud_default",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.quality_checks = quality_checks
        self.gcp_conn_id = gcp_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data quality checks."""
        hook = BigQueryHook(gcp_conn_id=self.gcp_conn_id, use_legacy_sql=False)

        self.log.info(
            f"Running {len(self.quality_checks)} quality checks on "
            f"{self.project_id}.{self.dataset_id}.{self.table_id}"
        )

        results = {}
        failed_checks = []

        for check in self.quality_checks:
            check_name = check["name"]
            check_sql = check["sql"]

            self.log.info(f"Executing quality check: {check_name}")

            try:
                # Run the check query
                records = hook.get_pandas_df(sql=check_sql)

                if records.empty:
                    self.log.error(f"Quality check '{check_name}' returned no results")
                    failed_checks.append(check_name)
                    results[check_name] = {"passed": False, "error": "No results returned"}
                    continue

                # Get the first column of the first row (should be a boolean)
                result = records.iloc[0, 0]

                if result:
                    self.log.info(f"✅ Quality check '{check_name}' PASSED")
                    results[check_name] = {"passed": True}
                else:
                    self.log.error(f"❌ Quality check '{check_name}' FAILED")
                    failed_checks.append(check_name)
                    results[check_name] = {"passed": False, "error": "Check condition not met"}

            except Exception as e:
                self.log.error(f"Error executing quality check '{check_name}': {str(e)}")
                failed_checks.append(check_name)
                results[check_name] = {"passed": False, "error": str(e)}

        # Summary
        total_checks = len(self.quality_checks)
        passed_checks = total_checks - len(failed_checks)

        self.log.info(f"\n{'='*60}")
        self.log.info(f"Data Quality Summary:")
        self.log.info(f"Total Checks: {total_checks}")
        self.log.info(f"Passed: {passed_checks}")
        self.log.info(f"Failed: {len(failed_checks)}")
        self.log.info(f"{'='*60}\n")

        if failed_checks:
            error_msg = f"Data quality checks failed: {', '.join(failed_checks)}"
            raise AirflowException(error_msg)

        return results
