"""Unit tests for SECDownloader."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.ingestion.sec_downloader import SECDownloader, SECDownloadError
from src.ingestion.config import SECConfig


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch) -> SECConfig:
    """Create a mock SEC configuration for testing."""
    monkeypatch.setenv("SEC_USER_AGENT", "TestCompany test@example.com")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")
    monkeypatch.setenv("GCS_RAW_BUCKET", "test-bucket")
    return SECConfig()


@pytest.fixture
def mock_storage_client() -> Mock:
    """Create a mock GCS storage client."""
    mock_client = Mock()
    mock_bucket = Mock()
    mock_blob = Mock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    return mock_client


class TestSECDownloader:
    """Test cases for SECDownloader class."""

    @patch("src.ingestion.sec_downloader.storage.Client")
    def test_initialization(
        self,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test downloader initialization."""
        mock_storage_class.return_value = mock_storage_client

        downloader = SECDownloader(mock_config)

        assert downloader.config == mock_config
        assert downloader.rate_limiter is not None
        assert downloader.session.headers["User-Agent"] == mock_config.USER_AGENT

    @patch("src.ingestion.sec_downloader.storage.Client")
    @patch("src.ingestion.sec_downloader.requests.Session")
    def test_download_file_success(
        self,
        mock_session_class: Mock,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test successful file download."""
        # Setup mocks
        mock_storage_class.return_value = mock_storage_client

        mock_response = Mock()
        mock_response.content = b"test content"
        mock_response.status_code = 200

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        # Create downloader and patch session
        downloader = SECDownloader(mock_config)
        downloader.session = mock_session

        # Download file
        content = downloader._download_file("https://test.url/file.zip")

        assert content == b"test content"
        mock_session.get.assert_called_once()

    @patch("src.ingestion.sec_downloader.storage.Client")
    @patch("src.ingestion.sec_downloader.requests.Session")
    def test_download_file_http_error(
        self,
        mock_session_class: Mock,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test file download with HTTP error."""
        # Setup mocks
        mock_storage_class.return_value = mock_storage_client

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("HTTP 404")

        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        # Create downloader
        downloader = SECDownloader(mock_config)
        downloader.session = mock_session

        # Should raise SECDownloadError after retries
        with pytest.raises(Exception):
            downloader._download_file("https://test.url/file.zip")

    @patch("src.ingestion.sec_downloader.storage.Client")
    def test_upload_to_gcs(
        self,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test uploading content to GCS."""
        mock_storage_class.return_value = mock_storage_client
        mock_blob = Mock()
        mock_storage_client.bucket.return_value.blob.return_value = mock_blob

        downloader = SECDownloader(mock_config)

        content = b"test content"
        path = "bulk/test.zip"
        metadata = {"source": "test"}

        downloader._upload_to_gcs(content, path, metadata)

        mock_blob.upload_from_string.assert_called_once_with(content)
        assert mock_blob.metadata == metadata

    @patch("src.ingestion.sec_downloader.storage.Client")
    def test_download_companyfacts(
        self,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test downloading companyfacts file."""
        mock_storage_class.return_value = mock_storage_client

        downloader = SECDownloader(mock_config)

        # Mock the download and upload methods
        downloader._download_file = Mock(return_value=b"companyfacts data")
        downloader._upload_to_gcs = Mock()

        result = downloader.download_companyfacts(2023)

        assert "companyfacts.zip" in result
        assert "gs://" in result
        downloader._download_file.assert_called_once()
        downloader._upload_to_gcs.assert_called_once()

    @patch("src.ingestion.sec_downloader.storage.Client")
    def test_download_submissions(
        self,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test downloading submissions file."""
        mock_storage_class.return_value = mock_storage_client

        downloader = SECDownloader(mock_config)

        # Mock the download and upload methods
        downloader._download_file = Mock(return_value=b"submissions data")
        downloader._upload_to_gcs = Mock()

        result = downloader.download_submissions(2023)

        assert "submissions.zip" in result
        assert "gs://" in result
        downloader._download_file.assert_called_once()
        downloader._upload_to_gcs.assert_called_once()

    @patch("src.ingestion.sec_downloader.storage.Client")
    def test_download_all_bulk_files(
        self,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test downloading all bulk files."""
        mock_storage_class.return_value = mock_storage_client

        downloader = SECDownloader(mock_config)

        # Mock the individual download methods
        downloader.download_companyfacts = Mock(return_value="gs://bucket/companyfacts.zip")
        downloader.download_submissions = Mock(return_value="gs://bucket/submissions.zip")

        results = downloader.download_all_bulk_files(2023)

        assert len(results) == 2
        assert "companyfacts" in results
        assert "submissions" in results
        downloader.download_companyfacts.assert_called_once_with(2023)
        downloader.download_submissions.assert_called_once_with(2023)

    @patch("src.ingestion.sec_downloader.storage.Client")
    def test_close(
        self,
        mock_storage_class: Mock,
        mock_config: SECConfig,
        mock_storage_client: Mock,
    ) -> None:
        """Test closing the downloader."""
        mock_storage_class.return_value = mock_storage_client

        downloader = SECDownloader(mock_config)
        downloader.session = Mock()

        downloader.close()

        downloader.session.close.assert_called_once()
