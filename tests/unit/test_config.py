"""Unit tests for configuration modules."""

import os
import pytest
from src.ingestion.config import SECConfig, StorageConfig


class TestSECConfig:
    """Test cases for SECConfig class."""

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test default configuration values."""
        monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("GCS_RAW_BUCKET", "test-bucket")

        config = SECConfig()

        assert config.RATE_LIMIT_REQUESTS == 10
        assert config.MAX_RETRIES == 3
        assert config.RETRY_DELAY_SECONDS == 5
        assert config.START_YEAR == 2020
        assert config.END_YEAR == 2024

    def test_environment_variable_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override defaults."""
        monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
        monkeypatch.setenv("GCP_PROJECT_ID", "custom-project")
        monkeypatch.setenv("GCS_RAW_BUCKET", "custom-bucket")
        monkeypatch.setenv("DATA_START_YEAR", "2018")
        monkeypatch.setenv("DATA_END_YEAR", "2023")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")

        config = SECConfig()

        assert config.GCP_PROJECT_ID == "custom-project"
        assert config.RAW_BUCKET == "custom-bucket"
        assert config.START_YEAR == 2018
        assert config.END_YEAR == 2023
        assert config.LOG_LEVEL == "DEBUG"

    def test_missing_user_agent_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing USER_AGENT raises ValueError."""
        monkeypatch.delenv("SEC_USER_AGENT", raising=False)
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("GCS_RAW_BUCKET", "test-bucket")

        with pytest.raises(ValueError, match="SEC_USER_AGENT must be set"):
            SECConfig()

    def test_missing_project_id_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing GCP_PROJECT_ID raises ValueError."""
        monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
        monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
        monkeypatch.setenv("GCS_RAW_BUCKET", "test-bucket")

        with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
            SECConfig()

    def test_missing_bucket_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing GCS_RAW_BUCKET raises ValueError."""
        monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.delenv("GCS_RAW_BUCKET", raising=False)

        with pytest.raises(ValueError, match="GCS_RAW_BUCKET"):
            SECConfig()

    def test_invalid_year_range_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that invalid year range raises ValueError."""
        monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("GCS_RAW_BUCKET", "test-bucket")
        monkeypatch.setenv("DATA_START_YEAR", "2024")
        monkeypatch.setenv("DATA_END_YEAR", "2020")

        with pytest.raises(ValueError, match="START_YEAR must be less than"):
            SECConfig()

    def test_url_constants(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that URL constants are correctly set."""
        monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
        monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
        monkeypatch.setenv("GCS_RAW_BUCKET", "test-bucket")

        config = SECConfig()

        assert "sec.gov" in config.COMPANYFACTS_URL
        assert "sec.gov" in config.SUBMISSIONS_URL
        assert "companyfacts.zip" in config.COMPANYFACTS_URL
        assert "submissions.zip" in config.SUBMISSIONS_URL


class TestStorageConfig:
    """Test cases for StorageConfig class."""

    def test_prefix_constants(self) -> None:
        """Test storage prefix constants."""
        assert StorageConfig.BULK_PREFIX == "bulk"
        assert StorageConfig.DAILY_INDEX_PREFIX == "daily-index"
        assert StorageConfig.FILINGS_PREFIX == "filings"

    def test_get_bulk_path_without_year(self) -> None:
        """Test bulk path generation without year."""
        path = StorageConfig.get_bulk_path("test.zip")
        assert path == "bulk/test.zip"

    def test_get_bulk_path_with_year(self) -> None:
        """Test bulk path generation with year."""
        path = StorageConfig.get_bulk_path("test.zip", 2023)
        assert path == "bulk/2023/test.zip"

    def test_get_daily_index_path(self) -> None:
        """Test daily index path generation."""
        path = StorageConfig.get_daily_index_path(2023, 6, 15, "index.json")
        assert path == "daily-index/2023/06/15/index.json"

    def test_get_daily_index_path_padding(self) -> None:
        """Test that month and day are zero-padded."""
        path = StorageConfig.get_daily_index_path(2023, 1, 5, "index.json")
        assert path == "daily-index/2023/01/05/index.json"

    def test_get_filings_path(self) -> None:
        """Test filings path generation."""
        path = StorageConfig.get_filings_path("0000123456", "0001234567-23-000001", "filing.xml")
        assert path == "filings/0000123456/0001234567-23-000001/filing.xml"
