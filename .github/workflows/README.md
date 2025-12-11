# GitHub Actions CI/CD Workflows

Automated CI/CD pipelines for the SEC EDGAR Analytics Platform.

## Workflows Overview

### 1. `ci.yml` - Continuous Integration

**Triggers**: On pull requests and pushes to `main` and `develop` branches

**Jobs**:
- **Code Quality**: Black formatting, Flake8 linting, mypy type checking, Pylint, Bandit security scan
- **Tests**: pytest with >80% coverage requirement
- **Terraform Validation**: Format check, init, and validate
- **SQL Linting**: sqlfluff for BigQuery SQL

**Status Badge**:
```markdown
![CI Status](https://github.com/abhatt13/sec-edgar-analytics/actions/workflows/ci.yml/badge.svg)
```

---

### 2. `deploy-functions.yml` - Cloud Functions Deployment

**Triggers**:
- Push to `main` branch (when `src/ingestion/**` changes)
- Manual workflow dispatch

**Actions**:
- Deploys `sec-data-ingestion` Cloud Function to GCP
- Tests deployment with sample request
- Uses service account authentication

**Required Secrets**:
- `GCP_SA_KEY`: Service account JSON key
- `GCP_PROJECT_ID`: GCP project ID
- `GCP_REGION`: Deployment region
- `SEC_USER_AGENT`: SEC API user agent
- `GCS_RAW_BUCKET`: Raw data bucket name

---

### 3. `deploy-dataproc.yml` - PySpark Jobs Deployment

**Triggers**:
- Push to `main` branch (when `src/processing/spark_jobs/**` changes)
- Manual workflow dispatch

**Actions**:
- Uploads all PySpark jobs (*.py) to GCS
- Verifies successful upload
- Dry-run testing on PRs

**Required Secrets**:
- `GCP_SA_KEY`
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `GCS_PROCESSED_BUCKET`

---

### 4. `terraform-plan.yml` - Infrastructure as Code

**Triggers**:
- Pull requests to `main` (when `terraform/**` changes)
- Push to `main` (auto-applies)
- Manual workflow dispatch

**Jobs**:
- **terraform-plan**: Runs on PRs, adds plan comment to PR
- **terraform-apply**: Auto-applies on merge to main

**Required Secrets**:
- `GCP_SA_KEY`
- `GCP_PROJECT_ID`
- `GCP_REGION`
- `PROJECT_OWNER_EMAIL`
- `BILLING_ACCOUNT_ID`

---

### 5. `refresh-looker.yml` - Materialized View Refresh

**Triggers**:
- Daily schedule at 5 AM UTC (after Airflow pipeline)
- Manual workflow dispatch

**Actions**:
- Refreshes all 4 Looker materialized views in parallel
- Verifies refresh timestamps
- Reports view row counts

**Required Secrets**:
- `GCP_SA_KEY`
- `GCP_PROJECT_ID`

---

## Setup Instructions

### 1. Configure GitHub Secrets

Navigate to **Settings → Secrets and variables → Actions** and add:

```bash
GCP_SA_KEY              # Service account JSON key (entire file content)
GCP_PROJECT_ID          # your-gcp-project-id
GCP_REGION              # us-central1
SEC_USER_AGENT          # "YourCompany contact@email.com"
GCS_RAW_BUCKET          # sec-edgar-dev-raw-data-PROJECT_ID
GCS_PROCESSED_BUCKET    # sec-edgar-dev-processed-data-PROJECT_ID
PROJECT_OWNER_EMAIL     # your-email@example.com
BILLING_ACCOUNT_ID      # XXXXXX-XXXXXX-XXXXXX
```

### 2. Create GCP Service Account for GitHub Actions

```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
  --display-name="GitHub Actions CI/CD"

# Grant necessary roles
PROJECT_ID="your-project-id"
SA_EMAIL="github-actions-sa@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudfunctions.developer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/bigquery.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/dataproc.editor"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=${SA_EMAIL}

# Copy the entire content of github-actions-key.json
# and paste it as the GCP_SA_KEY secret in GitHub
```

### 3. Enable Workflows

Workflows are automatically enabled when merged to `main`. To manually trigger:

1. Go to **Actions** tab in GitHub
2. Select workflow from left sidebar
3. Click **"Run workflow"** → **"Run workflow"** button

---

## Workflow Execution

### Automatic Triggers

| Workflow | Trigger | When |
|----------|---------|------|
| CI | PR to main | Code changes |
| Deploy Functions | Push to main | src/ingestion/** changes |
| Deploy Dataproc | Push to main | src/processing/** changes |
| Terraform Plan | PR to main | terraform/** changes |
| Terraform Apply | Merge to main | terraform/** changes |
| Refresh Looker | Schedule | Daily at 5 AM UTC |

### Manual Triggers

All workflows support manual execution via `workflow_dispatch`:

```bash
# Using GitHub CLI
gh workflow run ci.yml
gh workflow run deploy-functions.yml
gh workflow run deploy-dataproc.yml
gh workflow run terraform-plan.yml
gh workflow run refresh-looker.yml
```

---

## Monitoring and Logs

### View Workflow Runs

```bash
# List recent workflow runs
gh run list --workflow=ci.yml --limit=10

# View specific run
gh run view RUN_ID

# View logs
gh run view RUN_ID --log
```

### Workflow Status Badges

Add to README.md:

```markdown
![CI](https://github.com/abhatt13/sec-edgar-analytics/actions/workflows/ci.yml/badge.svg)
![Deploy Functions](https://github.com/abhatt13/sec-edgar-analytics/actions/workflows/deploy-functions.yml/badge.svg)
![Deploy Dataproc](https://github.com/abhatt13/sec-edgar-analytics/actions/workflows/deploy-dataproc.yml/badge.svg)
![Terraform](https://github.com/abhatt13/sec-edgar-analytics/actions/workflows/terraform-plan.yml/badge.svg)
```

---

## Best Practices

### 1. Branch Protection

Enable branch protection on `main`:

```bash
# Via GitHub web UI:
# Settings → Branches → Add branch protection rule
# - Require status checks to pass before merging
# - Require pull request reviews before merging
```

### 2. Environment Secrets

For production deployments, use GitHub Environments:

1. **Settings** → **Environments** → **New environment**
2. Create `production` environment
3. Add protection rules (required reviewers)
4. Add environment-specific secrets

### 3. Cost Monitoring

Monitor GitHub Actions usage:
- **Settings** → **Billing and plans** → **Actions**
- Free tier: 2000 minutes/month for public repos
- Paid plans available for private repos

### 4. Caching

All workflows use caching for:
- Python pip dependencies
- Terraform providers
- Reduces execution time by ~50%

---

## Troubleshooting

### Workflow Fails with "Access Denied"

- Verify `GCP_SA_KEY` secret is correctly set
- Check service account has necessary IAM roles
- Ensure service account key is not expired

### Terraform Apply Fails

- Check `terraform.tfvars` values
- Verify billing account is linked to project
- Ensure all required APIs are enabled

### Cloud Function Deployment Fails

- Check function code syntax
- Verify all environment variables are set
- Review Cloud Build logs in GCP console

### Tests Fail with Coverage < 80%

- Add more unit tests
- Check for untested code paths
- Review pytest output for specific failures

---

## Security Considerations

### Secrets Management

- ✅ All sensitive data stored in GitHub Secrets
- ✅ Service account keys never committed to git
- ✅ Least privilege IAM roles assigned
- ❌ Never hardcode credentials in workflow files

### Code Scanning

The CI workflow includes:
- **Bandit**: Python security linter
- (Optional) **CodeQL**: Advanced security scanning

Enable CodeQL:
```yaml
# Add to .github/workflows/codeql.yml
name: "CodeQL"
uses: github/codeql-action/analyze@v2
```

---

## Future Enhancements

Potential workflow improvements:

- [ ] Automated integration testing with test BigQuery dataset
- [ ] Performance benchmarking for PySpark jobs
- [ ] Automated changelog generation
- [ ] Slack/Discord notifications on deployment
- [ ] Canary deployments for Cloud Functions
- [ ] Blue-green deployments for infrastructure
- [ ] Automated rollback on failure

---

## Support

For issues with GitHub Actions:
- Review workflow logs in Actions tab
- Check GitHub Actions documentation
- File issue in this repository
