# BigQuery Module Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "BigQuery dataset location"
  type        = string
}

variable "project_owners_email" {
  description = "Email of project owner for dataset access"
  type        = string
}

variable "dataproc_sa_email" {
  description = "Dataproc service account email for write access"
  type        = string
}

variable "composer_sa_email" {
  description = "Cloud Composer service account email for orchestration"
  type        = string
}

variable "looker_sa_email" {
  description = "Looker service account email for read access"
  type        = string
}

variable "labels" {
  description = "Labels to apply to BigQuery resources"
  type        = map(string)
  default     = {}
}
