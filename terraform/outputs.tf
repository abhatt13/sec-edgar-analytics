# Terraform Outputs

output "gcs_raw_bucket" {
  description = "GCS bucket for raw SEC data"
  value       = module.storage.raw_bucket_name
}

output "gcs_processed_bucket" {
  description = "GCS bucket for processed data"
  value       = module.storage.processed_bucket_name
}

output "gcs_analytics_bucket" {
  description = "GCS bucket for analytics data"
  value       = module.storage.analytics_bucket_name
}

output "bigquery_bronze_dataset" {
  description = "BigQuery bronze dataset ID"
  value       = module.bigquery.bronze_dataset_id
}

output "bigquery_silver_dataset" {
  description = "BigQuery silver dataset ID"
  value       = module.bigquery.silver_dataset_id
}

output "bigquery_gold_dataset" {
  description = "BigQuery gold dataset ID"
  value       = module.bigquery.gold_dataset_id
}

output "cloud_function_sa_email" {
  description = "Cloud Function service account email"
  value       = module.iam.cloud_function_sa_email
}

output "dataproc_sa_email" {
  description = "Dataproc service account email"
  value       = module.iam.dataproc_sa_email
}

output "composer_sa_email" {
  description = "Cloud Composer service account email"
  value       = module.iam.composer_sa_email
}

output "looker_sa_email" {
  description = "Looker service account email"
  value       = module.iam.looker_sa_email
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}
