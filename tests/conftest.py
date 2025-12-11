"""Shared pytest fixtures and configuration."""

import pytest
import os


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up test environment variables."""
    monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("GCS_RAW_BUCKET", "test-raw-bucket")
    monkeypatch.setenv("GCS_PROCESSED_BUCKET", "test-processed-bucket")
    monkeypatch.setenv("GCS_ANALYTICS_BUCKET", "test-analytics-bucket")
    monkeypatch.setenv("BQ_BRONZE_DATASET", "bronze_sec")
    monkeypatch.setenv("BQ_SILVER_DATASET", "silver_sec")
    monkeypatch.setenv("BQ_GOLD_DATASET", "gold_sec")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
