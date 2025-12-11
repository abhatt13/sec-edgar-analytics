"""Configuration for SEC data ingestion."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class SECConfig:
    """Configuration for SEC API access."""

    # SEC API endpoints
    BULK_DATA_BASE_URL: str = "https://www.sec.gov/Archives/edgar/daily-index"
    COMPANYFACTS_URL: str = f"{BULK_DATA_BASE_URL}/xbrl/companyfacts.zip"
    SUBMISSIONS_URL: str = f"{BULK_DATA_BASE_URL}/bulkdata/submissions.zip"

    # API Configuration
    RATE_LIMIT_REQUESTS: int = 10  # requests per second
    USER_AGENT: str = os.getenv("SEC_USER_AGENT", "")

    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    RAW_BUCKET: str = os.getenv("GCS_RAW_BUCKET", "")

    # Data Configuration
    START_YEAR: int = int(os.getenv("DATA_START_YEAR", "2020"))
    END_YEAR: int = int(os.getenv("DATA_END_YEAR", "2024"))

    # Retry Configuration
    MAX_RETRIES: int = 3
    RETRY_DELAY_SECONDS: int = 5
    TIMEOUT_SECONDS: int = 300

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.USER_AGENT:
            raise ValueError(
                "SEC_USER_AGENT must be set. Format: 'CompanyName contact@email.com'"
            )
        if not self.GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        if not self.RAW_BUCKET:
            raise ValueError("GCS_RAW_BUCKET environment variable is required")
        if self.START_YEAR > self.END_YEAR:
            raise ValueError("START_YEAR must be less than or equal to END_YEAR")


@dataclass
class StorageConfig:
    """Configuration for GCS storage paths."""

    BULK_PREFIX: str = "bulk"
    DAILY_INDEX_PREFIX: str = "daily-index"
    FILINGS_PREFIX: str = "filings"

    @staticmethod
    def get_bulk_path(filename: str, year: Optional[int] = None) -> str:
        """Generate GCS path for bulk data files.

        Args:
            filename: Name of the file
            year: Optional year for partitioning

        Returns:
            GCS path string
        """
        base = f"{StorageConfig.BULK_PREFIX}"
        if year:
            return f"{base}/{year}/{filename}"
        return f"{base}/{filename}"

    @staticmethod
    def get_daily_index_path(year: int, month: int, day: int, filename: str) -> str:
        """Generate GCS path for daily index files.

        Args:
            year: Year
            month: Month (1-12)
            day: Day (1-31)
            filename: Name of the file

        Returns:
            GCS path string
        """
        return f"{StorageConfig.DAILY_INDEX_PREFIX}/{year}/{month:02d}/{day:02d}/{filename}"

    @staticmethod
    def get_filings_path(cik: str, accession: str, filename: str) -> str:
        """Generate GCS path for individual filing files.

        Args:
            cik: Company CIK number
            accession: Accession number
            filename: Name of the file

        Returns:
            GCS path string
        """
        return f"{StorageConfig.FILINGS_PREFIX}/{cik}/{accession}/{filename}"
