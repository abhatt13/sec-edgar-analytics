# Storage Module Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for buckets"
  type        = string
}

variable "bucket_prefix" {
  description = "Prefix for bucket names"
  type        = string
  default     = "sec-edgar"
}

variable "labels" {
  description = "Labels to apply to storage resources"
  type        = map(string)
  default     = {}
}
