# Terraform Infrastructure for SEC EDGAR Analytics

This directory contains Terraform configurations to provision all GCP infrastructure for the SEC EDGAR Analytics Platform.

## Architecture

The infrastructure is organized into three main modules:

1. **Storage Module** (`modules/storage/`): GCS buckets for data storage
2. **BigQuery Module** (`modules/bigquery/`): BigQuery datasets for analytics
3. **IAM Module** (`modules/iam/`): Service accounts and permissions

## Directory Structure

```
terraform/
├── modules/
│   ├── storage/          # GCS buckets with lifecycle policies
│   ├── bigquery/         # BigQuery datasets (bronze/silver/gold)
│   └── iam/              # Service accounts and IAM roles
├── environments/
│   ├── dev/              # Development environment
│   └── prod/             # Production environment
├── variables.tf          # Global variables
└── outputs.tf            # Global outputs
```

## Resources Created

### GCS Buckets
- **Raw Data Bucket**: Stores SEC bulk data downloads (Bronze layer)
- **Processed Data Bucket**: Stores PySpark processing outputs (Silver layer)
- **Analytics Data Bucket**: Stores analytics outputs (Gold layer)
- **Dataproc Staging Bucket**: Temporary storage for Dataproc jobs

### BigQuery Datasets
- **bronze_sec**: Raw SEC data (companyfacts, submissions)
- **silver_sec**: Cleaned dimension and fact tables
- **gold_sec**: Materialized views optimized for Looker

### Service Accounts
- **Cloud Function SA**: For data ingestion with GCS write access
- **Dataproc SA**: For PySpark jobs with BigQuery write access
- **Composer SA**: For Airflow orchestration
- **Looker SA**: For dashboard read access to BigQuery

### IAM Permissions
All service accounts follow the **principle of least privilege**:
- Cloud Functions: GCS write, Secret Manager access
- Dataproc: GCS read/write, BigQuery data editor
- Composer: Cloud Functions invoker, Dataproc editor, BigQuery editor
- Looker: BigQuery data viewer (read-only)

## Prerequisites

1. **GCP Project**: Create a new GCP project
2. **Billing Account**: Link billing account to project
3. **gcloud CLI**: Install and authenticate
4. **Terraform**: Install Terraform >= 1.5

```bash
# Install Terraform
brew install terraform  # macOS
# or download from https://www.terraform.io/downloads

# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

## Deployment

### 1. Choose Environment

Navigate to the environment directory:

```bash
cd terraform/environments/dev  # or prod
```

### 2. Configure Variables

Copy the example file and fill in your values:

```bash
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars
```

Required variables:
- `project_id`: Your GCP project ID
- `region`: GCP region (default: us-central1)
- `project_owners_email`: Your email address
- `billing_account_id`: Your GCP billing account ID

### 3. Initialize Terraform

```bash
terraform init
```

This downloads the required providers and initializes the backend.

### 4. Plan Infrastructure

```bash
terraform plan
```

Review the planned changes. Terraform will show what resources will be created.

### 5. Apply Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will create all GCP resources.

### 6. View Outputs

```bash
terraform output
```

Or for a specific output:

```bash
terraform output setup_summary
```

## Remote State Management (Recommended)

For team collaboration, use GCS backend for Terraform state:

### 1. Create state bucket

```bash
gsutil mb gs://sec-edgar-terraform-state-dev
gsutil versioning set on gs://sec-edgar-terraform-state-dev
```

### 2. Uncomment backend configuration in `main.tf`

```hcl
backend "gcs" {
  bucket = "sec-edgar-terraform-state-dev"
  prefix = "terraform/state"
}
```

### 3. Migrate state

```bash
terraform init -migrate-state
```

## Budget Alerts

Budget alerts are configured at:
- 50%, 75%, 90%, 100% of monthly budget
- Production also alerts at 110% (overage)

To create notification channels for alerts:

```bash
# Create email notification channel
gcloud alpha monitoring channels create \
  --display-name="Budget Alerts" \
  --type=email \
  --channel-labels=email_address=your-email@example.com

# Get channel ID
gcloud alpha monitoring channels list

# Add to terraform.tfvars
budget_alert_notification_channels = ["projects/PROJECT_ID/notificationChannels/CHANNEL_ID"]
```

## Cost Optimization

- GCS lifecycle policies move old data to cheaper storage classes
- BigQuery partitioning and clustering reduce query costs
- Budget alerts prevent cost overruns
- Estimated monthly cost: $100-500 depending on data volume

## Destruction

To tear down all infrastructure:

```bash
terraform destroy
```

**⚠️ WARNING**: This will delete all data. Only use for testing environments.

## Environment Differences

### Development
- Lower budget alerts
- No audit logging
- Faster lifecycle policies for testing

### Production
- Enhanced audit logging enabled
- Stricter budget monitoring
- Longer data retention periods
- All buckets have versioning

## Troubleshooting

### Error: API not enabled

If you see errors about APIs not being enabled, run:

```bash
gcloud services enable \
  storage.googleapis.com \
  bigquery.googleapis.com \
  iam.googleapis.com \
  cloudfunctions.googleapis.com \
  dataproc.googleapis.com \
  composer.googleapis.com \
  secretmanager.googleapis.com
```

### Error: Insufficient permissions

Ensure you have the following roles:
- `roles/owner` or
- `roles/editor` + `roles/iam.serviceAccountAdmin` + `roles/resourcemanager.projectIamAdmin`

### Error: Billing account required

Link a billing account to your project:

```bash
gcloud beta billing projects link PROJECT_ID \
  --billing-account=BILLING_ACCOUNT_ID
```

## Next Steps

After infrastructure is deployed:

1. Deploy Cloud Functions (`src/ingestion/`)
2. Upload PySpark jobs to GCS (`src/processing/spark_jobs/`)
3. Create BigQuery tables (`src/sql/schema/`)
4. Set up Cloud Composer environment
5. Configure Looker Studio dashboards

## Support

For issues or questions:
- Create a GitHub issue
- Review GCP documentation: https://cloud.google.com/docs
- Check Terraform docs: https://registry.terraform.io/providers/hashicorp/google/latest/docs
