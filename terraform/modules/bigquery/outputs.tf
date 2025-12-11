# BigQuery Module Outputs

output "bronze_dataset_id" {
  description = "Bronze dataset ID"
  value       = google_bigquery_dataset.bronze_sec.dataset_id
}

output "bronze_dataset_name" {
  description = "Bronze dataset full name"
  value       = google_bigquery_dataset.bronze_sec.id
}

output "silver_dataset_id" {
  description = "Silver dataset ID"
  value       = google_bigquery_dataset.silver_sec.dataset_id
}

output "silver_dataset_name" {
  description = "Silver dataset full name"
  value       = google_bigquery_dataset.silver_sec.id
}

output "gold_dataset_id" {
  description = "Gold dataset ID"
  value       = google_bigquery_dataset.gold_sec.dataset_id
}

output "gold_dataset_name" {
  description = "Gold dataset full name"
  value       = google_bigquery_dataset.gold_sec.id
}
