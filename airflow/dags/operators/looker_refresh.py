"""Custom Operator to Refresh BigQuery Materialized Views."""

from typing import Dict, Any
from airflow.models import BaseOperator
from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.exceptions import AirflowException


class LookerMaterializedViewRefreshOperator(BaseOperator):
    """
    Refresh a BigQuery materialized view.

    :param project_id: GCP project ID
    :param dataset_id: BigQuery dataset ID
    :param view_id: Materialized view ID to refresh
    :param gcp_conn_id: Airflow connection ID for GCP
    """

    template_fields = ("project_id", "dataset_id", "view_id")

    def __init__(
        self,
        project_id: str,
        dataset_id: str,
        view_id: str,
        gcp_conn_id: str = "google_cloud_default",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.view_id = view_id
        self.gcp_conn_id = gcp_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh the materialized view."""
        hook = BigQueryHook(gcp_conn_id=self.gcp_conn_id, use_legacy_sql=False)

        full_view_id = f"{self.project_id}.{self.dataset_id}.{self.view_id}"

        self.log.info(f"Refreshing materialized view: {full_view_id}")

        refresh_sql = f"""
        CALL BQ.REFRESH_MATERIALIZED_VIEW('{full_view_id}')
        """

        try:
            # Execute the refresh
            hook.run_query(
                sql=refresh_sql,
                use_legacy_sql=False,
            )

            self.log.info(f"✅ Successfully refreshed {full_view_id}")

            # Get view metadata to confirm refresh
            view_info_sql = f"""
            SELECT
                table_name,
                last_modified_time,
                row_count,
                size_bytes
            FROM `{self.project_id}.{self.dataset_id}.__TABLES__`
            WHERE table_id = '{self.view_id}'
            """

            view_info = hook.get_pandas_df(sql=view_info_sql)

            if not view_info.empty:
                self.log.info(f"View metadata:")
                self.log.info(f"  - Last modified: {view_info.iloc[0]['last_modified_time']}")
                self.log.info(f"  - Row count: {view_info.iloc[0]['row_count']}")
                self.log.info(f"  - Size (bytes): {view_info.iloc[0]['size_bytes']}")

                return {
                    "view_id": full_view_id,
                    "last_modified": str(view_info.iloc[0]['last_modified_time']),
                    "row_count": int(view_info.iloc[0]['row_count']),
                    "size_bytes": int(view_info.iloc[0]['size_bytes']),
                    "refresh_status": "success"
                }

            return {
                "view_id": full_view_id,
                "refresh_status": "success"
            }

        except Exception as e:
            self.log.error(f"Failed to refresh materialized view {full_view_id}: {str(e)}")
            raise AirflowException(f"Materialized view refresh failed: {str(e)}")
