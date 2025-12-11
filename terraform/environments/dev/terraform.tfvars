# SEC EDGAR Analytics Platform - Development Environment
# Cost-Optimized Configuration for <$20/month budget

# GCP Project Configuration
project_id = "sec-edgar-analytics"
region     = "us-central1"
zone       = "us-central1-a"

# Billing Configuration
billing_account_id = "016728-105AC9-14CAEE"
project_owners_email = "aakashbhatt13@gmail.com"

# Budget Alert - $20/month hard limit
budget_amount = 20

# Budget alert notification channels (email)
budget_alert_notification_channels = []

# Data Scope - LIMITED TO 2 YEARS FOR COST SAVINGS
# Starting with 2023-2024 instead of 2020-2024
# This reduces storage and processing costs by 60%
data_start_year = 2023
data_end_year   = 2024

# SEC API Configuration
sec_user_agent = "SEC-EDGAR-Analytics aakashbhatt13@gmail.com"

# Environment Labels
labels = {
  project     = "sec-edgar-analytics"
  managed_by  = "terraform"
  environment = "dev"
  owner       = "abhatt13"
  cost_center = "personal"
}
