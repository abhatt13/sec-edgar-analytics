# Storage Module Outputs

output "raw_bucket_name" {
  description = "Name of the raw data bucket"
  value       = google_storage_bucket.raw_data.name
}

output "raw_bucket_url" {
  description = "URL of the raw data bucket"
  value       = google_storage_bucket.raw_data.url
}

output "processed_bucket_name" {
  description = "Name of the processed data bucket"
  value       = google_storage_bucket.processed_data.name
}

output "processed_bucket_url" {
  description = "URL of the processed data bucket"
  value       = google_storage_bucket.processed_data.url
}

output "analytics_bucket_name" {
  description = "Name of the analytics data bucket"
  value       = google_storage_bucket.analytics_data.name
}

output "analytics_bucket_url" {
  description = "URL of the analytics data bucket"
  value       = google_storage_bucket.analytics_data.url
}

output "dataproc_staging_bucket_name" {
  description = "Name of the Dataproc staging bucket"
  value       = google_storage_bucket.dataproc_staging.name
}

output "dataproc_staging_bucket_url" {
  description = "URL of the Dataproc staging bucket"
  value       = google_storage_bucket.dataproc_staging.url
}
