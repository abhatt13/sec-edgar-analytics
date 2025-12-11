# IAM Module - Service Accounts and Permissions

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Cloud Functions Service Account (Data Ingestion)
resource "google_service_account" "cloud_function_sa" {
  account_id   = "sec-ingestion-cf-sa"
  display_name = "SEC Data Ingestion Cloud Function Service Account"
  description  = "Service account for Cloud Functions that ingest SEC data"
  project      = var.project_id
}

# Grant Cloud Function SA permissions to write to GCS
resource "google_storage_bucket_iam_member" "cf_raw_bucket_writer" {
  bucket = var.raw_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Grant Cloud Function SA permissions to read secrets
resource "google_project_iam_member" "cf_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Grant Cloud Function SA permissions to write logs
resource "google_project_iam_member" "cf_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Dataproc Service Account (Data Processing)
resource "google_service_account" "dataproc_sa" {
  account_id   = "sec-dataproc-sa"
  display_name = "SEC Dataproc Processing Service Account"
  description  = "Service account for Dataproc Serverless jobs"
  project      = var.project_id
}

# Grant Dataproc SA permissions to read from raw GCS bucket
resource "google_storage_bucket_iam_member" "dataproc_raw_bucket_reader" {
  bucket = var.raw_bucket_name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

# Grant Dataproc SA permissions to write to processed GCS bucket
resource "google_storage_bucket_iam_member" "dataproc_processed_bucket_writer" {
  bucket = var.processed_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

# Grant Dataproc SA permissions to use staging bucket
resource "google_storage_bucket_iam_member" "dataproc_staging_bucket" {
  bucket = var.dataproc_staging_bucket_name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

# Grant Dataproc SA permissions to write to BigQuery
resource "google_project_iam_member" "dataproc_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

resource "google_project_iam_member" "dataproc_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

# Grant Dataproc SA permissions to write logs
resource "google_project_iam_member" "dataproc_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

# Grant Dataproc SA Dataproc Worker role
resource "google_project_iam_member" "dataproc_worker" {
  project = var.project_id
  role    = "roles/dataproc.worker"
  member  = "serviceAccount:${google_service_account.dataproc_sa.email}"
}

# Cloud Composer Service Account (Orchestration)
resource "google_service_account" "composer_sa" {
  account_id   = "sec-composer-sa"
  display_name = "SEC Cloud Composer Service Account"
  description  = "Service account for Cloud Composer/Airflow orchestration"
  project      = var.project_id
}

# Grant Composer SA permissions to trigger Cloud Functions
resource "google_project_iam_member" "composer_cf_invoker" {
  project = var.project_id
  role    = "roles/cloudfunctions.invoker"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# Grant Composer SA permissions to submit Dataproc jobs
resource "google_project_iam_member" "composer_dataproc_editor" {
  project = var.project_id
  role    = "roles/dataproc.editor"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# Grant Composer SA permissions to read/write BigQuery (for quality checks and view refresh)
resource "google_project_iam_member" "composer_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

resource "google_project_iam_member" "composer_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# Grant Composer SA permissions to write logs
resource "google_project_iam_member" "composer_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.composer_sa.email}"
}

# Looker Service Account (Visualization)
resource "google_service_account" "looker_sa" {
  account_id   = "sec-looker-sa"
  display_name = "SEC Looker Studio Service Account"
  description  = "Service account for Looker Studio/Enterprise to access BigQuery"
  project      = var.project_id
}

# Grant Looker SA read-only access to BigQuery datasets
resource "google_project_iam_member" "looker_bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.looker_sa.email}"
}

resource "google_project_iam_member" "looker_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.looker_sa.email}"
}

# Enable required APIs
resource "google_project_service" "iam_api" {
  project = var.project_id
  service = "iam.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_functions_api" {
  project = var.project_id
  service = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloud_build_api" {
  project = var.project_id
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "dataproc_api" {
  project = var.project_id
  service = "dataproc.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "composer_api" {
  project = var.project_id
  service = "composer.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secret_manager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"
  disable_on_destroy = false
}
