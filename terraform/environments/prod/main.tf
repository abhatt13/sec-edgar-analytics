# Production Environment Configuration

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Uncomment and configure for remote state management
  # backend "gcs" {
  #   bucket = "sec-edgar-terraform-state-prod"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  environment = "prod"
  labels = merge(var.labels, {
    environment = local.environment
  })
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  project_id    = var.project_id
  region        = var.region
  bucket_prefix = "sec-edgar-${local.environment}"
  labels        = local.labels
}

# IAM Module (Service Accounts)
module "iam" {
  source = "../../modules/iam"

  project_id                   = var.project_id
  raw_bucket_name              = module.storage.raw_bucket_name
  processed_bucket_name        = module.storage.processed_bucket_name
  dataproc_staging_bucket_name = module.storage.dataproc_staging_bucket_name

  depends_on = [module.storage]
}

# BigQuery Module
module "bigquery" {
  source = "../../modules/bigquery"

  project_id            = var.project_id
  region                = var.region
  project_owners_email  = var.project_owners_email
  dataproc_sa_email     = module.iam.dataproc_sa_email
  composer_sa_email     = module.iam.composer_sa_email
  looker_sa_email       = module.iam.looker_sa_email
  labels                = local.labels

  depends_on = [module.iam]
}

# Budget Alert (stricter monitoring for production)
resource "google_billing_budget" "sec_budget" {
  billing_account = var.billing_account_id
  display_name    = "SEC EDGAR Analytics - ${upper(local.environment)} Budget"

  budget_filter {
    projects = ["projects/${data.google_project.project.number}"]
    labels = {
      environment = local.environment
    }
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(var.budget_amount)
    }
  }

  threshold_rules {
    threshold_percent = 0.5  # Alert at 50%
  }

  threshold_rules {
    threshold_percent = 0.75  # Alert at 75%
  }

  threshold_rules {
    threshold_percent = 0.9  # Alert at 90%
  }

  threshold_rules {
    threshold_percent = 1.0  # Alert at 100%
  }

  threshold_rules {
    threshold_percent = 1.1  # Alert at 110% (over budget)
    spend_basis       = "CURRENT_SPEND"
  }

  all_updates_rule {
    monitoring_notification_channels = var.budget_alert_notification_channels
  }
}

# Get project data
data "google_project" "project" {
  project_id = var.project_id
}

# Enable audit logging for production
resource "google_project_iam_audit_config" "audit_logging" {
  project = var.project_id
  service = "allServices"

  audit_log_config {
    log_type = "ADMIN_READ"
  }

  audit_log_config {
    log_type = "DATA_WRITE"
  }

  audit_log_config {
    log_type = "DATA_READ"
  }
}
