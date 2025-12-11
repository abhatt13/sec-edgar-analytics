# IAM Module Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "raw_bucket_name" {
  description = "Name of the raw data GCS bucket"
  type        = string
}

variable "processed_bucket_name" {
  description = "Name of the processed data GCS bucket"
  type        = string
}

variable "dataproc_staging_bucket_name" {
  description = "Name of the Dataproc staging GCS bucket"
  type        = string
}
