"""Cloud Function entry point for SEC data ingestion."""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from google.cloud import logging as cloud_logging

from config import SECConfig
from sec_downloader import SECDownloader


# Set up Cloud Logging
cloud_logging_client = cloud_logging.Client()
cloud_logging_client.setup_logging()

logger = logging.getLogger(__name__)


def ingest_sec_data(request: Any) -> tuple[str, int]:
    """Cloud Function entry point for SEC data ingestion.

    This function can be triggered by:
    - HTTP request
    - Cloud Scheduler
    - Pub/Sub message

    Args:
        request: Flask request object or Cloud event

    Returns:
        Tuple of (response message, HTTP status code)
    """
    try:
        # Parse request
        request_json = {}
        if hasattr(request, 'get_json'):
            request_json = request.get_json(silent=True) or {}
        elif hasattr(request, 'data'):
            try:
                request_json = json.loads(request.data)
            except (json.JSONDecodeError, AttributeError):
                pass

        logger.info(f"Received request: {request_json}")

        # Get parameters
        year = request_json.get('year', datetime.now().year)
        file_types = request_json.get('file_types', ['companyfacts', 'submissions'])

        # Initialize configuration
        config = SECConfig()
        logger.info(f"Initialized config for project: {config.GCP_PROJECT_ID}")

        # Initialize downloader
        downloader = SECDownloader(config)

        # Download files
        results = {}
        if 'companyfacts' in file_types or 'all' in file_types:
            logger.info("Downloading companyfacts...")
            results['companyfacts'] = downloader.download_companyfacts(year)

        if 'submissions' in file_types or 'all' in file_types:
            logger.info("Downloading submissions...")
            results['submissions'] = downloader.download_submissions(year)

        # Close downloader
        downloader.close()

        # Prepare response
        response = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "year": year,
            "files_downloaded": len(results),
            "results": results,
        }

        logger.info(f"Ingestion completed successfully: {response}")

        return json.dumps(response), 200

    except ValueError as e:
        error_msg = f"Configuration error: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"status": "error", "message": error_msg}), 400

    except Exception as e:
        error_msg = f"Unexpected error during ingestion: {str(e)}"
        logger.exception(error_msg)
        return json.dumps({"status": "error", "message": error_msg}), 500


def main() -> None:
    """Local testing entry point."""
    from unittest.mock import Mock

    # Create mock request
    request = Mock()
    request.get_json.return_value = {
        "year": datetime.now().year,
        "file_types": ["companyfacts", "submissions"]
    }

    # Call function
    response, status = ingest_sec_data(request)
    print(f"Status: {status}")
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
