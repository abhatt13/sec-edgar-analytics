# Development Environment Variables

variable "project_id" {
  description = "GCP Project ID for development environment"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "project_owners_email" {
  description = "Email of the project owner"
  type        = string
}

variable "billing_account_id" {
  description = "GCP Billing Account ID for budget alerts"
  type        = string
}

variable "budget_amount" {
  description = "Monthly budget threshold in USD"
  type        = number
  default     = 500
}

variable "budget_alert_notification_channels" {
  description = "List of notification channel IDs for budget alerts"
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Common labels for all resources"
  type        = map(string)
  default = {
    project    = "sec-edgar-analytics"
    managed_by = "terraform"
  }
}
