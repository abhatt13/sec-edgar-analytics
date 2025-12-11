# Development Environment Outputs

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "environment" {
  description = "Environment name"
  value       = "dev"
}

# Storage outputs
output "raw_bucket" {
  description = "Raw data GCS bucket"
  value       = module.storage.raw_bucket_name
}

output "processed_bucket" {
  description = "Processed data GCS bucket"
  value       = module.storage.processed_bucket_name
}

output "analytics_bucket" {
  description = "Analytics data GCS bucket"
  value       = module.storage.analytics_bucket_name
}

output "dataproc_staging_bucket" {
  description = "Dataproc staging GCS bucket"
  value       = module.storage.dataproc_staging_bucket_name
}

# BigQuery outputs
output "bronze_dataset" {
  description = "BigQuery bronze dataset"
  value       = module.bigquery.bronze_dataset_id
}

output "silver_dataset" {
  description = "BigQuery silver dataset"
  value       = module.bigquery.silver_dataset_id
}

output "gold_dataset" {
  description = "BigQuery gold dataset"
  value       = module.bigquery.gold_dataset_id
}

# Service Account outputs
output "cloud_function_sa" {
  description = "Cloud Function service account email"
  value       = module.iam.cloud_function_sa_email
}

output "dataproc_sa" {
  description = "Dataproc service account email"
  value       = module.iam.dataproc_sa_email
}

output "composer_sa" {
  description = "Composer service account email"
  value       = module.iam.composer_sa_email
}

output "looker_sa" {
  description = "Looker service account email"
  value       = module.iam.looker_sa_email
}

# Summary output
output "setup_summary" {
  description = "Quick reference for infrastructure setup"
  value = <<-EOT

  ========================================
  SEC EDGAR Analytics - DEV Environment
  ========================================

  Project ID: ${var.project_id}
  Region: ${var.region}

  GCS Buckets:
  - Raw: ${module.storage.raw_bucket_name}
  - Processed: ${module.storage.processed_bucket_name}
  - Analytics: ${module.storage.analytics_bucket_name}
  - Dataproc Staging: ${module.storage.dataproc_staging_bucket_name}

  BigQuery Datasets:
  - Bronze: ${module.bigquery.bronze_dataset_id}
  - Silver: ${module.bigquery.silver_dataset_id}
  - Gold: ${module.bigquery.gold_dataset_id}

  Service Accounts:
  - Cloud Functions: ${module.iam.cloud_function_sa_email}
  - Dataproc: ${module.iam.dataproc_sa_email}
  - Composer: ${module.iam.composer_sa_email}
  - Looker: ${module.iam.looker_sa_email}

  Next Steps:
  1. Deploy Cloud Functions for data ingestion
  2. Upload PySpark jobs to GCS
  3. Create BigQuery tables
  4. Set up Cloud Composer environment
  5. Configure Looker Studio dashboards

  ========================================
  EOT
}
