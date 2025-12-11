"""Configuration for PySpark XBRL processing jobs."""

import os
from dataclasses import dataclass
from typing import List


@dataclass
class SparkConfig:
    """Configuration for Spark jobs."""

    # GCP Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")

    # GCS Buckets
    RAW_BUCKET: str = os.getenv("GCS_RAW_BUCKET", "")
    PROCESSED_BUCKET: str = os.getenv("GCS_PROCESSED_BUCKET", "")

    # BigQuery Datasets
    BRONZE_DATASET: str = os.getenv("BQ_BRONZE_DATASET", "bronze_sec")
    SILVER_DATASET: str = os.getenv("BQ_SILVER_DATASET", "silver_sec")
    GOLD_DATASET: str = os.getenv("BQ_GOLD_DATASET", "gold_sec")

    # Spark Configuration
    APP_NAME: str = "SEC-XBRL-Processing"
    EXECUTOR_MEMORY: str = "4g"
    EXECUTOR_CORES: int = 2
    DRIVER_MEMORY: str = "2g"

    # Processing Configuration
    PARTITION_COLUMN: str = "fiscal_year"
    CLUSTER_COLUMNS: List[str] = None

    def __post_init__(self) -> None:
        """Initialize default values and validate configuration."""
        if self.CLUSTER_COLUMNS is None:
            self.CLUSTER_COLUMNS = ["cik", "concept"]

        if not self.GCP_PROJECT_ID:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        if not self.RAW_BUCKET:
            raise ValueError("GCS_RAW_BUCKET environment variable is required")
        if not self.PROCESSED_BUCKET:
            raise ValueError("GCS_PROCESSED_BUCKET environment variable is required")


@dataclass
class XBRLConfig:
    """Configuration for XBRL parsing."""

    # US-GAAP Taxonomy concepts to extract
    INCOME_STATEMENT_CONCEPTS: List[str] = None
    BALANCE_SHEET_CONCEPTS: List[str] = None
    CASH_FLOW_CONCEPTS: List[str] = None

    # Valid units to process
    VALID_UNITS: List[str] = None

    # Valid forms
    VALID_FORMS: List[str] = None

    def __post_init__(self) -> None:
        """Initialize default concept lists."""
        if self.INCOME_STATEMENT_CONCEPTS is None:
            self.INCOME_STATEMENT_CONCEPTS = [
                "Revenues",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "CostOfRevenue",
                "GrossProfit",
                "OperatingIncomeLoss",
                "NetIncomeLoss",
                "EarningsPerShareBasic",
                "EarningsPerShareDiluted",
                "OperatingExpenses",
                "ResearchAndDevelopmentExpense",
                "SellingGeneralAndAdministrativeExpense",
                "InterestExpense",
                "IncomeTaxExpenseBenefit",
            ]

        if self.BALANCE_SHEET_CONCEPTS is None:
            self.BALANCE_SHEET_CONCEPTS = [
                "Assets",
                "AssetsCurrent",
                "AssetsNoncurrent",
                "CashAndCashEquivalentsAtCarryingValue",
                "AccountsReceivableNetCurrent",
                "InventoryNet",
                "Liabilities",
                "LiabilitiesCurrent",
                "LiabilitiesNoncurrent",
                "AccountsPayableCurrent",
                "LongTermDebtNoncurrent",
                "StockholdersEquity",
                "RetainedEarningsAccumulatedDeficit",
                "CommonStockValue",
            ]

        if self.CASH_FLOW_CONCEPTS is None:
            self.CASH_FLOW_CONCEPTS = [
                "NetCashProvidedByUsedInOperatingActivities",
                "NetCashProvidedByUsedInInvestingActivities",
                "NetCashProvidedByUsedInFinancingActivities",
                "PaymentsToAcquirePropertyPlantAndEquipment",
                "PaymentsOfDividends",
                "ProceedsFromIssuanceOfLongTermDebt",
                "RepaymentsOfLongTermDebt",
            ]

        if self.VALID_UNITS is None:
            self.VALID_UNITS = ["USD", "shares", "pure"]

        if self.VALID_FORMS is None:
            self.VALID_FORMS = ["10-K", "10-Q", "8-K", "20-F", "40-F"]

    def get_all_concepts(self) -> List[str]:
        """Get all configured concepts.

        Returns:
            List of all concept names
        """
        return (
            self.INCOME_STATEMENT_CONCEPTS
            + self.BALANCE_SHEET_CONCEPTS
            + self.CASH_FLOW_CONCEPTS
        )
