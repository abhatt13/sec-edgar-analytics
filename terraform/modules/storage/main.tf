# GCS Storage Module for SEC EDGAR Data

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Raw data bucket (Bronze layer)
resource "google_storage_bucket" "raw_data" {
  name          = "${var.bucket_prefix}-raw-data-${var.project_id}"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 90  # Move to nearline after 90 days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365  # Move to coldline after 1 year
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  labels = merge(var.labels, {
    layer = "bronze"
    data_type = "raw"
  })
}

# Processed data bucket (Silver layer)
resource "google_storage_bucket" "processed_data" {
  name          = "${var.bucket_prefix}-processed-data-${var.project_id}"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 180  # Move to nearline after 6 months
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  labels = merge(var.labels, {
    layer = "silver"
    data_type = "processed"
  })
}

# Analytics data bucket (Gold layer)
resource "google_storage_bucket" "analytics_data" {
  name          = "${var.bucket_prefix}-analytics-data-${var.project_id}"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  versioning {
    enabled = false  # Analytics outputs can be regenerated
  }

  lifecycle_rule {
    condition {
      age = 30  # Delete old analytics after 30 days (regeneratable)
    }
    action {
      type = "Delete"
    }
  }

  labels = merge(var.labels, {
    layer = "gold"
    data_type = "analytics"
  })
}

# Dataproc staging bucket
resource "google_storage_bucket" "dataproc_staging" {
  name          = "${var.bucket_prefix}-dataproc-staging-${var.project_id}"
  location      = var.region
  project       = var.project_id
  storage_class = "STANDARD"

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 7  # Delete staging files after 7 days
    }
    action {
      type = "Delete"
    }
  }

  labels = merge(var.labels, {
    purpose = "dataproc-staging"
  })
}
