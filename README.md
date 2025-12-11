# SEC EDGAR Financial Analytics Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-grade financial data analytics platform that ingests, processes, and visualizes SEC EDGAR filings using Google Cloud Platform, PySpark, and Looker.

## 🏗️ Architecture

```
┌─────────────────┐
│   SEC EDGAR     │
│   Bulk Data     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│           Cloud Functions (Data Ingestion)          │
│  • Rate limiting (10 req/sec)                       │
│  • Error handling & retries                         │
│  • User-Agent compliance                            │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│         Cloud Storage (GCS) - Bronze Layer          │
│  gs://sec-raw-data/{bulk,daily-index,filings}/      │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│       Dataproc Serverless (PySpark Processing)      │
│  • Parse XBRL/JSON                                  │
│  • Extract US-GAAP taxonomy                         │
│  • Flatten nested structures                        │
│  • Data quality validation                          │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│         BigQuery - Silver & Gold Layers             │
│  Bronze: Raw data                                   │
│  Silver: Cleaned & normalized                       │
│  Gold: Analytics & aggregations                     │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│              Looker Studio/Enterprise               │
│  • Executive dashboards                             │
│  • Company analysis                                 │
│  • Peer comparisons                                 │
│  • Industry analytics                               │
└─────────────────────────────────────────────────────┘

      ┌──────────────────────────────────┐
      │  Cloud Composer (Orchestration)   │
      │  Daily at 2 AM EST                │
      └──────────────────────────────────┘
```

## 🚀 Features

- **Automated Data Ingestion**: Scheduled downloads of SEC bulk data with rate limiting and error handling
- **Scalable Processing**: PySpark jobs on Dataproc Serverless for efficient XBRL/JSON parsing
- **Enterprise Data Warehouse**: Multi-layer BigQuery architecture (Bronze/Silver/Gold)
- **Advanced Analytics**: Pre-computed financial ratios, peer comparisons, and time-series metrics
- **Interactive Dashboards**: Looker visualizations for executive insights and deep-dive analysis
- **Infrastructure as Code**: Fully reproducible Terraform configurations
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Production-Ready**: Comprehensive logging, monitoring, and error handling

## 📊 Data Coverage

- **Years**: 2020-2024 (configurable)
- **Filings**: 10-K, 10-Q, 8-K, and more
- **Metrics**: Income Statement, Balance Sheet, Cash Flow, Financial Ratios
- **Companies**: All SEC-registered companies with XBRL filings
- **Taxonomy**: US-GAAP standardized accounting concepts

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Cloud Platform** | Google Cloud Platform (GCP) |
| **Languages** | Python 3.11+ |
| **Data Processing** | PySpark (Dataproc Serverless) |
| **Data Warehouse** | BigQuery |
| **Storage** | Cloud Storage (GCS) |
| **Orchestration** | Cloud Composer (Apache Airflow) |
| **Visualization** | Looker Studio / Looker Enterprise |
| **IaC** | Terraform |
| **Version Control** | GitHub |
| **CI/CD** | GitHub Actions |

## 📁 Project Structure

```
sec-edgar-analytics/
├── .github/
│   └── workflows/          # GitHub Actions CI/CD pipelines
├── terraform/
│   ├── modules/            # Reusable Terraform modules
│   └── environments/       # Dev/Prod configurations
├── src/
│   ├── ingestion/          # Cloud Functions for data ingestion
│   ├── processing/
│   │   └── spark_jobs/     # PySpark processing jobs
│   └── sql/
│       ├── schema/         # BigQuery DDL
│       └── analytics/      # Analytical queries
├── looker_studio/          # Dashboard specifications
├── airflow/
│   └── dags/               # Airflow DAGs
├── tests/
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── docs/                   # Documentation
├── config/                 # Configuration files
├── requirements.txt        # Python dependencies
├── setup.py                # Package setup
└── pyproject.toml          # Tool configurations
```

## 🚦 Getting Started

### Prerequisites

- Python 3.11+
- Google Cloud Platform account
- Terraform 1.5+
- GitHub CLI (`gh`)
- gcloud CLI

### Installation

1. **Clone the repository**
   ```bash
   gh repo clone abhatt13/sec-edgar-analytics
   cd sec-edgar-analytics
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure GCP credentials**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   gcloud auth application-default login
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Deploy infrastructure with Terraform**
   ```bash
   cd terraform/environments/dev
   terraform init
   terraform plan
   terraform apply
   ```

### Running the Pipeline

1. **Trigger data ingestion manually**
   ```bash
   gcloud functions call sec-data-ingestion --data '{}'
   ```

2. **Submit PySpark job**
   ```bash
   gcloud dataproc batches submit pyspark \
     src/processing/spark_jobs/parse_xbrl.py \
     --region=us-central1 \
     --batch=sec-processing-$(date +%s)
   ```

3. **Run Airflow DAG**
   ```bash
   # Via Composer UI or
   gcloud composer environments run COMPOSER_ENV \
     --location REGION \
     dags trigger -- sec_edgar_pipeline
   ```

## 📈 BigQuery Schema

### Core Tables

- `bronze_sec.raw_companyfacts`: Raw XBRL data from SEC
- `bronze_sec.raw_submissions`: Company submission metadata
- `silver_sec.dim_companies`: Company dimension table
- `silver_sec.dim_taxonomy`: US-GAAP taxonomy
- `silver_sec.fact_financials`: Normalized financial facts
- `gold_sec.looker_company_metrics`: Pre-aggregated metrics for dashboards
- `gold_sec.looker_financial_ratios`: Calculated financial ratios
- `gold_sec.looker_peer_comparison`: Industry benchmarks
- `gold_sec.looker_timeseries`: Time-series analytics (TTM, moving averages)

## 📊 Looker Dashboards

1. **Executive Summary**: KPIs, trends, top performers
2. **Company Deep Dive**: Full financial statements, metrics, time series
3. **Peer Comparison**: Industry benchmarking, percentile rankings
4. **Industry Analysis**: Market share, growth rates, sector trends

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_ingestion.py
```

## 🔒 Security

- No hardcoded secrets (uses Secret Manager)
- Least privilege IAM roles
- Audit logging enabled
- VPC Service Controls (optional)
- Regular dependency updates

## 💰 Cost Optimization

- Estimated monthly cost: <$500
- BigQuery query optimization with partitioning/clustering
- Dataproc Serverless auto-scaling
- Cloud Storage lifecycle policies
- Budget alerts configured

## 📝 Documentation

- [Architecture Guide](docs/architecture.md)
- [Setup Guide](docs/setup.md)
- [API Reference](docs/api_reference.md)
- [Looker Studio Setup](docs/looker_studio_setup.md)
- [Contributing Guide](docs/contributing.md)

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Commit changes: `git commit -m "feat: description"`
3. Push to branch: `git push origin feature/your-feature`
4. Open PR: `gh pr create --title "Your feature" --body "Description"`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [SEC EDGAR](https://www.sec.gov/edgar) for public financial data
- [US-GAAP Taxonomy](https://www.fasb.org/xbrl) for standardized financial concepts
- Google Cloud Platform for infrastructure

## 📧 Contact

Aakash Bhatt - [@abhatt13](https://github.com/abhatt13)

Project Link: [https://github.com/abhatt13/sec-edgar-analytics](https://github.com/abhatt13/sec-edgar-analytics)

---

**Note**: This is a public data analytics platform. No personally identifiable information (PII) is collected or processed.
