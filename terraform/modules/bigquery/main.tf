# BigQuery Module for SEC EDGAR Analytics

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Bronze Dataset - Raw SEC data
resource "google_bigquery_dataset" "bronze_sec" {
  dataset_id    = "bronze_sec"
  project       = var.project_id
  location      = var.region
  description   = "Bronze layer: Raw SEC EDGAR data from companyfacts and submissions"

  default_table_expiration_ms = null  # No expiration for raw data

  labels = merge(var.labels, {
    layer = "bronze"
    data_source = "sec-edgar"
  })

  access {
    role          = "OWNER"
    user_by_email = var.project_owners_email
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }

  access {
    role          = "WRITER"
    user_by_email = var.dataproc_sa_email
  }
}

# Silver Dataset - Cleaned and normalized data
resource "google_bigquery_dataset" "silver_sec" {
  dataset_id    = "silver_sec"
  project       = var.project_id
  location      = var.region
  description   = "Silver layer: Cleaned and normalized SEC data - dimension and fact tables"

  default_table_expiration_ms = null

  labels = merge(var.labels, {
    layer = "silver"
    data_source = "sec-edgar"
  })

  access {
    role          = "OWNER"
    user_by_email = var.project_owners_email
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }

  access {
    role          = "WRITER"
    user_by_email = var.dataproc_sa_email
  }

  access {
    role          = "READER"
    user_by_email = var.looker_sa_email
  }
}

# Gold Dataset - Analytics and aggregations for Looker
resource "google_bigquery_dataset" "gold_sec" {
  dataset_id    = "gold_sec"
  project       = var.project_id
  location      = var.region
  description   = "Gold layer: Analytics, aggregations, and materialized views optimized for Looker dashboards"

  default_table_expiration_ms = null

  labels = merge(var.labels, {
    layer = "gold"
    purpose = "analytics"
  })

  access {
    role          = "OWNER"
    user_by_email = var.project_owners_email
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }

  access {
    role          = "WRITER"
    user_by_email = var.dataproc_sa_email
  }

  access {
    role          = "WRITER"
    user_by_email = var.composer_sa_email
  }

  access {
    role          = "READER"
    user_by_email = var.looker_sa_email
  }
}

# Enable BigQuery API
resource "google_project_service" "bigquery_api" {
  project = var.project_id
  service = "bigquery.googleapis.com"

  disable_on_destroy = false
}

# BigQuery Data Transfer Service (for scheduled queries if needed)
resource "google_project_service" "bigquery_datatransfer_api" {
  project = var.project_id
  service = "bigquerydatatransfer.googleapis.com"

  disable_on_destroy = false
}
