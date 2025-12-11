# IAM Module Outputs

output "cloud_function_sa_email" {
  description = "Cloud Function service account email"
  value       = google_service_account.cloud_function_sa.email
}

output "cloud_function_sa_name" {
  description = "Cloud Function service account name"
  value       = google_service_account.cloud_function_sa.name
}

output "dataproc_sa_email" {
  description = "Dataproc service account email"
  value       = google_service_account.dataproc_sa.email
}

output "dataproc_sa_name" {
  description = "Dataproc service account name"
  value       = google_service_account.dataproc_sa.name
}

output "composer_sa_email" {
  description = "Cloud Composer service account email"
  value       = google_service_account.composer_sa.email
}

output "composer_sa_name" {
  description = "Cloud Composer service account name"
  value       = google_service_account.composer_sa.name
}

output "looker_sa_email" {
  description = "Looker service account email"
  value       = google_service_account.looker_sa.email
}

output "looker_sa_name" {
  description = "Looker service account name"
  value       = google_service_account.looker_sa.name
}
