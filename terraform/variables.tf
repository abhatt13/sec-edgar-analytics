# Global Terraform Variables for SEC EDGAR Analytics Platform

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone for resources"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "data_start_year" {
  description = "Start year for SEC data ingestion"
  type        = number
  default     = 2020
}

variable "data_end_year" {
  description = "End year for SEC data ingestion"
  type        = number
  default     = 2024
}

variable "sec_user_agent" {
  description = "User-Agent header for SEC API requests"
  type        = string
}

variable "budget_amount" {
  description = "Monthly budget alert threshold in USD"
  type        = number
  default     = 500
}

variable "budget_alert_emails" {
  description = "Email addresses for budget alerts"
  type        = list(string)
}

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    project     = "sec-edgar-analytics"
    managed_by  = "terraform"
  }
}
