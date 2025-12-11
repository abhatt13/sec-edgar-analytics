"""SEC data downloader with rate limiting and error handling."""

import logging
import time
from typing import Optional, Dict, Any
from pathlib import Path

import requests
from google.cloud import storage
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .config import SECConfig, StorageConfig
from .rate_limiter import RateLimiter


logger = logging.getLogger(__name__)


class SECDownloadError(Exception):
    """Custom exception for SEC download errors."""
    pass


class SECDownloader:
    """Download SEC bulk data files with rate limiting and error handling."""

    def __init__(self, config: SECConfig) -> None:
        """Initialize SEC downloader.

        Args:
            config: SEC configuration object
        """
        self.config = config
        self.rate_limiter = RateLimiter(requests_per_second=config.RATE_LIMIT_REQUESTS)
        self.storage_client = storage.Client(project=config.GCP_PROJECT_ID)
        self.bucket = self.storage_client.bucket(config.RAW_BUCKET)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": config.USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov",
        })

        logger.info(
            f"Initialized SECDownloader with bucket: {config.RAW_BUCKET}, "
            f"rate limit: {config.RATE_LIMIT_REQUESTS} req/s"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((requests.RequestException, SECDownloadError)),
    )
    def _download_file(self, url: str) -> bytes:
        """Download file from URL with retry logic.

        Args:
            url: URL to download from

        Returns:
            File contents as bytes

        Raises:
            SECDownloadError: If download fails after retries
        """
        self.rate_limiter.acquire()

        logger.info(f"Downloading from {url}")

        try:
            response = self.session.get(
                url,
                timeout=self.config.TIMEOUT_SECONDS,
                stream=True,
            )
            response.raise_for_status()

            # Read content
            content = response.content
            logger.info(f"Downloaded {len(content)} bytes from {url}")

            return content

        except requests.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit hit (429), backing off...")
                time.sleep(10)
                raise SECDownloadError(f"Rate limit exceeded: {e}")
            elif e.response.status_code >= 500:
                logger.warning(f"Server error {e.response.status_code}, will retry")
                raise SECDownloadError(f"Server error: {e}")
            else:
                logger.error(f"HTTP error {e.response.status_code}: {e}")
                raise SECDownloadError(f"HTTP error: {e}")

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise SECDownloadError(f"Request failed: {e}")

    def _upload_to_gcs(
        self,
        content: bytes,
        destination_path: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """Upload content to GCS.

        Args:
            content: File content as bytes
            destination_path: GCS destination path (without bucket name)
            metadata: Optional metadata to attach to the blob
        """
        blob = self.bucket.blob(destination_path)

        if metadata:
            blob.metadata = metadata

        blob.upload_from_string(content)
        logger.info(f"Uploaded {len(content)} bytes to gs://{self.config.RAW_BUCKET}/{destination_path}")

    def download_companyfacts(self, year: Optional[int] = None) -> str:
        """Download companyfacts.zip bulk file.

        Args:
            year: Optional year for partitioning (uses current year if None)

        Returns:
            GCS path where file was uploaded
        """
        url = self.config.COMPANYFACTS_URL
        filename = "companyfacts.zip"

        logger.info(f"Starting download of {filename}")

        # Download file
        content = self._download_file(url)

        # Generate GCS path
        gcs_path = StorageConfig.get_bulk_path(filename, year)

        # Upload to GCS
        metadata = {
            "source": "sec-edgar",
            "file_type": "companyfacts",
            "download_timestamp": str(int(time.time())),
        }
        self._upload_to_gcs(content, gcs_path, metadata)

        return f"gs://{self.config.RAW_BUCKET}/{gcs_path}"

    def download_submissions(self, year: Optional[int] = None) -> str:
        """Download submissions.zip bulk file.

        Args:
            year: Optional year for partitioning (uses current year if None)

        Returns:
            GCS path where file was uploaded
        """
        url = self.config.SUBMISSIONS_URL
        filename = "submissions.zip"

        logger.info(f"Starting download of {filename}")

        # Download file
        content = self._download_file(url)

        # Generate GCS path
        gcs_path = StorageConfig.get_bulk_path(filename, year)

        # Upload to GCS
        metadata = {
            "source": "sec-edgar",
            "file_type": "submissions",
            "download_timestamp": str(int(time.time())),
        }
        self._upload_to_gcs(content, gcs_path, metadata)

        return f"gs://{self.config.RAW_BUCKET}/{gcs_path}"

    def download_all_bulk_files(self, year: Optional[int] = None) -> Dict[str, str]:
        """Download all bulk files.

        Args:
            year: Optional year for partitioning

        Returns:
            Dictionary mapping file type to GCS path
        """
        results = {}

        try:
            logger.info("Starting bulk file downloads")

            results["companyfacts"] = self.download_companyfacts(year)
            results["submissions"] = self.download_submissions(year)

            logger.info(f"Successfully downloaded {len(results)} bulk files")

        except Exception as e:
            logger.error(f"Error during bulk downloads: {e}")
            raise

        return results

    def close(self) -> None:
        """Close the downloader and clean up resources."""
        self.session.close()
        logger.info("SECDownloader closed")
