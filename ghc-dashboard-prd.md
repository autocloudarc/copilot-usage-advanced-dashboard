# GitHub Copilot Usage Advanced Dashboard - Product Requirements Document

**Document Version:** 1.0  
**Date Created:** October 27, 2025  
**Purpose:** Deployment and Setup Instructions for Copilot Usage Advanced Dashboard

---

## Table of Contents

1. [Overview](#overview)
2. [Solution Description](#solution-description)
3. [Prerequisites](#prerequisites)
4. [Deployment Architecture](#deployment-architecture)
5. [Deployment Instructions](#deployment-instructions)
6. [Authentication & Access Control](#authentication--access-control)
7. [Post-Deployment Steps](#post-deployment-steps)
8. [Features & Capabilities](#features--capabilities)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The **GitHub Copilot Usage Advanced Dashboard** is a comprehensive analytics solution that provides multi-dimensional insights into GitHub Copilot usage across organizations and teams. Unlike native GitHub dashboards that only show the past 28 days of data, this solution provides:

- **Historical data persistence** - Retain and analyze usage data beyond 28 days
- **Multi-organizational support** - Monitor multiple GitHub organizations simultaneously
- **Advanced filtering** - Filter by organization, team, language, and editor
- **Rich visualization** - Custom Grafana dashboards with flexible styling and themes
- **Alerting capabilities** - Set rules for usage anomalies (e.g., inactive users)
- **Elasticsearch integration** - Scalable data storage and querying

### Key Differentiators

- Data persisted in **Elasticsearch** (not ephemeral)
- Visualized in **Grafana** with customizable dashboards
- Generates unique hash keys for data idempotency
- Two dashboard designs available simultaneously
- Built-in alerting and third-party integration capability

---

## Solution Description

### Architecture Components

The solution comprises the following Azure and open-source components:

1. **Azure Container Apps** - Serverless container orchestration
2. **Elasticsearch** - Time-series data storage and indexing
3. **Grafana** - Data visualization and dashboard platform
4. **Python Applications** - Data fetching and transformation
5. **Azure Key Vault** - Secure credential management
6. **Azure Container Registry** - Container image repository
7. **User-Assigned Managed Identity** - Credential-less authentication

### Data Flow

```
GitHub Copilot APIs
    ↓
Python Data Fetcher (cpuad-updater)
    ↓
Elasticsearch (Data Persistence)
    ↓
Grafana Dashboards (Visualization)
    ↓
End Users (Viewers)
```

### Available Dashboards

1. **Copilot Usage Advanced Dashboard** - Modern multi-dimensional analytics
2. **Copilot Usage Advanced Dashboard Original** - Alternative design with team/language focus

Both dashboards can coexist in a single Grafana instance.

---

## Prerequisites

### Required Access & Credentials

- ✅ **Global Admin** or **Owner** role on target Azure subscription
- ✅ **Azure Developer CLI (azd)** installed locally
- ✅ **GitHub Personal Access Token (PAT)** - Fine-grained recommended
- ✅ **GitHub Organization Admin** access to the organizations you want to monitor
- ✅ **Azure Entra ID** tenant access (for optional SSO configuration)

### Required Subscriptions & Services

- Active **Azure subscription**
- **GitHub Enterprise Cloud** organization (for Copilot metrics API access)
- Access to **GitHub Copilot seat management** data

### GitHub PAT Requirements

#### **Fine-Grained PAT (Recommended) ✅**

**Why Fine-Grained:**
- More secure - limited to specific repositories and permissions
- Better control - grant only exact permissions needed
- Shorter expiration - configurable max 1 year
- Modern approach - GitHub's recommended standard

**How to Create:**

1. Navigate to: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click **"Generate new token"**
3. Configure as follows:
   - **Token name:** `copilot-usage-dashboard`
   - **Expiration:** 90 days or 6 months (recommended)
   - **Repository access:** "All repositories" (or specific ones if preferred)
   - **Permissions:**
     - Organization permissions: Read access to organization data
     - Include Copilot-specific scopes if available
4. Copy the token immediately (only shown once)
5. Store securely - never commit to version control

#### **Classic PAT (Not Recommended) ❌**

- No expiration limit (security risk)
- All-or-nothing permissions
- Deprecated by GitHub

**Conclusion:** Always use Fine-Grained PAT for this deployment.

---

## Deployment Architecture

### Azure Resources Created

| Resource | Purpose | Configuration |
|----------|---------|---|
| **Container App (Elasticsearch)** | Time-series data storage | 1 container instance, auto-scale |
| **Container App (Grafana)** | Visualization platform | 1 container instance, auto-scale |
| **Container App Jobs** | Background data fetch tasks | Scheduled execution |
| **Key Vault** | Credential storage | RBAC-protected access |
| **Container Registry** | Container image storage | Private registry |
| **User-Assigned Managed Identity** | Workload authentication | RBAC role assignments |
| **Virtual Network** (optional) | Network isolation | Security boundary |
| **Storage Account** (optional) | File shares for containers | SMB configuration |
| **Log Analytics** | Monitoring & observability | Container Apps insights |

### RBAC Role Requirements

**For Deployment:**
- `User Access Administrator` or `Owner` (for role assignments)
- OR `Contributor` with `AZURE_ROLE_ASSIGNMENTS=false` (manual role assignment required post-deployment)

**Post-Deployment Roles (auto-assigned):**
- **Key Vault Secrets Officer** - On KeyVault (for User Assigned Identity)
- **AcrPull** - On Container Registry (for User Assigned Identity)
- **Storage File Data SMB Share Contributor** - On Storage Account (for User Assigned Identity)

---

## Deployment Instructions

### Step 1: Environment Setup

Initialize your deployment environment:

```powershell
# Navigate to repository directory
cd copilot-usage-advanced-dashboard

# Initialize azd project (if not already done)
azd init

# Authenticate to Azure
az login

# Set GitHub credentials
azd env set GH_PAT <your-fine-grained-pat>
azd env set GH_ORGANIZATION_SLUGS <org-name>  # e.g., "my-org" or "org1,org2,org3"

# Set Azure subscription and region
azd env set AZURE_SUBSCRIPTION_ID <your-subscription-id>
azd env set AZURE_LOCATION <azure-region>  # e.g., "eastus2", "westus", etc.

# Set custom Grafana credentials
azd env set GRAFANA_USERNAME <username>
azd env set GRAFANA_PASSWORD <password>

# Verify all variables are set
Get-Content .\.azure\dev\.env
```

**Example with actual values:**
```powershell
azd env set GH_PAT github_pat_••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••
azd env set GH_ORGANIZATION_SLUGS ms-mfg-community
azd env set AZURE_SUBSCRIPTION_ID ••••••••-••••-••••-••••-••••••••••••
azd env set AZURE_LOCATION eastus2
azd env set GRAFANA_USERNAME demouser
azd env set GRAFANA_PASSWORD demouser
```

### Step 2: Basic Deployment (Without Entra ID SSO)

For a quick deployment without Azure AD authentication:

```powershell
# Deploy infrastructure and containers
azd up
```

**What happens:**
1. Creates Azure resource group
2. Deploys Bicep infrastructure templates
3. Builds and pushes container images to ACR
4. Deploys Container Apps
5. Runs post-deployment scripts to initialize Grafana and data fetchers
6. Outputs Grafana URL and credentials

### Step 3: Deployment with Entra ID SSO (Recommended for Admin Access)

For enterprise authentication and access control:

#### 3.1 Create Entra ID App Registration

1. Go to **Azure Portal** → **Entra ID** → **App registrations** → **New registration**
2. Configure:
   - **Name:** `copilot-usage-advanced-dashboard`
   - **Supported account types:** Accounts in this organizational directory only (Single tenant)
   - **Redirect URI:** Leave blank (update after deployment)

3. Copy and save:
   - **Application (client) ID**
   - **Directory (tenant) ID**

#### 3.2 Configure API Permissions

1. In the app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph** → **Delegated permissions**
4. Search for and add:
   - `openid`
   - `profile`
   - `offline_access`
   - `User.Read`

#### 3.3 Enable OpenID Connect

1. Go to **Authentication**
2. Under **Implicit grant and hybrid flows**, check:
   - ✅ **ID tokens**

#### 3.4 Deploy with Entra ID Configuration

```powershell
# Set Entra ID environment variables
azd env set AZURE_AUTHENTICATION_ENABLED true
azd env set AZURE_AUTHENTICATION_CLIENT_ID <your-app-registration-client-id>
azd env set AZURE_AUTHENTICATION_OPEN_ID_ISSUER "https://login.microsoftonline.com/<your-tenant-id>/v2.0"

# Deploy with Entra ID enabled
azd up
```

#### 3.5 Update Entra ID App Registration (Post-Deployment)

After deployment completes:

1. In the app registration, go to **Authentication**
2. Update **Redirect URI** to: `https://<your-container-app-name>.<location>.azurecontainerapps.io/.auth/login/aad/callback`
   - Example: `https://cpuad-grafana-eastus.azurecontainerapps.io/.auth/login/aad/callback`

3. (Optional) Go to **Certificates & secrets** → **Federated credentials** → **Add credential**
   - **Scenario:** Managed Identity
   - **Managed identity:** Select the Container App's managed identity
   - **Name:** `copilot-usage-advanced-dashboard`

---

## Authentication & Access Control

### Grafana Access Methods

#### Without Entra ID SSO
- **Default Credentials:**
  - Username: `admin`
  - Password: Retrieved from Key Vault (check Azure Portal)
- ⚠️ Credentials are automatically generated and not secure - **change immediately**

#### With Entra ID SSO
- Users sign in with their **Microsoft/Entra ID credentials**
- All authenticated users get **Viewer** role (read-only access)
- No Copilot data is visible without authentication

### Fine-Grained Access Control (Optional)

To restrict Grafana access to specific Entra ID groups:

1. In Azure Portal, create/identify Entra ID security group for dashboard access
2. In the app registration, add **Application role** for differentiated access levels
3. Configure Grafana's Entra ID settings to enforce group membership

---

## Post-Deployment Steps

### 1. Verify Deployment Success

```powershell
# Check Container Apps status
az containerapp list -g <resource-group-name>

# View logs
az containerapp logs show -n grafana -g <resource-group-name>
az containerapp logs show -n elasticsearch -g <resource-group-name>
```

### 2. Access Grafana Dashboard

1. Get the Grafana URL from deployment output
2. Login with configured credentials (or Entra ID)
3. Navigate to **Dashboards** to view available dashboards

### 3. Retrieve Grafana Credentials (If Needed)

Credentials are stored in Key Vault:

```powershell
# List Key Vault secrets
az keyvault secret list --vault-name <vault-name>

# Get Grafana password
az keyvault secret show --vault-name <vault-name> --name grafana-password --query value -o tsv
```

### 4. Monitor Data Collection

The deployment includes automated background jobs:

- **Update Grafana Job** - Initializes Grafana dashboards (runs on schedule)
- **CPU Ad Updater Job** - Fetches Copilot metrics and stores in Elasticsearch (runs periodically)

Check job status:

```powershell
# View container app jobs
az containerapp job list -g <resource-group-name>

# View job execution history
az containerapp job execution list --name cpuad-updater -g <resource-group-name>
```

### 5. Configure Data Refresh Schedule

Edit the Container App Jobs to adjust the execution schedule:

```powershell
# Current default: Runs every 1 hour
# To modify frequency, update the cron expression in the Container App Job
```

### 6. Secure Key Vault Access

Ensure only authorized identities can access secrets:

```powershell
# View current RBAC assignments
az role assignment list --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault-name>

# Grant additional access if needed
az role assignment create --role "Key Vault Secrets Officer" --assignee <user-or-group-id> --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault-name>
```

---

## Features & Capabilities

### 1. Organization-Level Analytics
- **Metrics:** Acceptance rate, total suggestions, active users, lines accepted
- **Aggregation:** Sums team-level metrics to organization totals
- **Filter:** By organization slug

### 2. Team-Level Breakdown
- **Metrics:** Teams ranked by acceptance rate and suggestion volume
- **Comparison:** Side-by-side team performance metrics
- **Filter:** By team slug

### 3. Language Analytics
- **Metrics:** Performance by programming language
- **Ranking:** Top languages by adoption and acceptance
- **Breakdown:** Lines suggested/accepted per language

### 4. Editor Analytics
- **Metrics:** Performance by code editor (VS Code, JetBrains, etc.)
- **Ranking:** Top editors by adoption and acceptance
- **Breakdown:** Suggestion/acceptance rates per editor

### 5. Copilot Chat Insights
- **Chat Metrics:** Turns, acceptances, active chat users
- **Acceptance Rate:** Chat-specific acceptance calculations
- **Trend Analysis:** Chat adoption over time

### 6. Seat Analysis
- **Seat Distribution:** Enterprise vs. Business plan breakdown
- **Utilization:** Active, inactive, and never-used seats
- **User Ranking:** Inactive user identification (≥2 days inactive)
- **Trend Analysis:** Seat activation trends

### 7. Language × Editor Heatmap
- **2D Analysis:** Combined language and editor performance
- **Acceptance Rates:** By count and by lines
- **Optimization:** Identify best language/editor combinations

### 8. Data Persistence
- **Historical Data:** Retain data beyond GitHub's 28-day window
- **Data Integrity:** Unique hash keys prevent duplicate records
- **Query Flexibility:** Analyze any date range

### 9. Alerting
- **Custom Rules:** Define thresholds for usage anomalies
- **Notification Channels:** Email, Slack, PagerDuty integration
- **Examples:** Alert on inactive users, low adoption, acceptance rate drops

---

## Troubleshooting

### Common Issues & Solutions

#### Issue: Deployment fails with "Insufficient permissions"

**Cause:** Your Azure account doesn't have `User Access Administrator` or `Owner` role

**Solution:**
```powershell
# Deploy without automatic role assignments
azd env set AZURE_ROLE_ASSIGNMENTS false
azd up

# After deployment, manually assign roles via Azure Portal:
# 1. Key Vault Secrets Officer on KeyVault (to managed identity)
# 2. AcrPull on Container Registry (to managed identity)
# 3. Storage File Data SMB Share Contributor on Storage Account (to managed identity)
```

#### Issue: Grafana shows "No data"

**Cause:** Copilot metrics haven't been fetched yet or GitHub PAT is invalid

**Solution:**
```powershell
# Verify GitHub PAT is set
azd env list | grep GH_PAT

# Check container app logs
az containerapp logs show -n cpuad-updater -g <resource-group-name>

# Manually trigger data fetch job
az containerapp job start --name cpuad-updater -g <resource-group-name>

# Wait 2-5 minutes, then refresh Grafana
```

#### Issue: Cannot login to Grafana

**Cause:** Wrong credentials or Entra ID misconfiguration

**Solution (Without SSO):**
```powershell
# Get correct credentials from Key Vault
az keyvault secret show --vault-name <vault-name> --name grafana-username --query value
az keyvault secret show --vault-name <vault-name> --name grafana-password --query value

# Reset Grafana admin password if needed:
az containerapp exec --name grafana -g <resource-group-name> \
  --command grafana-cli admin reset-admin-password <new-password>
```

**Solution (With Entra ID SSO):**
1. Verify Entra ID app registration redirect URI matches Grafana URL
2. Check Azure Portal → App registrations → API permissions → All permissions granted
3. Ensure user account is in the authorized Entra ID group (if configured)

#### Issue: Elasticsearch connection fails

**Cause:** Elasticsearch container not running or networking issue

**Solution:**
```powershell
# Check Elasticsearch container status
az containerapp show -n elasticsearch -g <resource-group-name> --query properties.provisioningState

# View Elasticsearch logs
az containerapp logs show -n elasticsearch -g <resource-group-name>

# Restart Elasticsearch container
az containerapp update -n elasticsearch -g <resource-group-name>
```

#### Issue: GitHub PAT authorization errors

**Cause:** PAT doesn't have required permissions or has expired

**Solution:**
1. Generate new Fine-Grained PAT (verify permissions listed in [GitHub PAT Requirements](#github-pat-requirements))
2. Update PAT in environment: `azd env set GH_PAT <new-token>`
3. Restart container apps: `az containerapp restart -n cpuad-updater -g <resource-group-name>`

#### Issue: High costs on Azure bill

**Cause:** Container Apps auto-scaling to handle load, or long-running jobs

**Solution:**
1. Check Container Apps metrics in Azure Portal
2. Adjust auto-scaling rules in resource configuration
3. Review job execution frequency - reduce if running too often
4. Consider reserving capacity for predictable workloads

---

## Configuration Reference

### Environment Variables

| Variable | Required | Example | Description |
|----------|----------|---------|---|
| `GH_PAT` | ✅ Yes | `ghp_xxx...` | GitHub Personal Access Token (fine-grained recommended) |
| `GH_ORGANIZATION_SLUGS` | ✅ Yes | `my-org` or `org1,org2` | GitHub organization(s) to monitor |
| `GRAFANA_USERNAME` | ❌ No | `admin` | Grafana admin username (auto-generated if not set) |
| `GRAFANA_PASSWORD` | ❌ No | `P@ssw0rd!` | Grafana admin password (auto-generated if not set) |
| `AZURE_AUTHENTICATION_ENABLED` | ❌ No | `true` or `false` | Enable Entra ID SSO |
| `AZURE_AUTHENTICATION_CLIENT_ID` | ❌ No | `xxxxxxxx-xxxx...` | Entra ID app registration client ID |
| `AZURE_AUTHENTICATION_OPEN_ID_ISSUER` | ❌ No | `https://login.microsoftonline.com/...` | Entra ID OpenID issuer URL |
| `AZURE_ROLE_ASSIGNMENTS` | ❌ No | `true` or `false` | Auto-assign RBAC roles (requires Owner role) |
| `AZURE_ENV_NAME` | ❌ No | `cpuad-dev` | Azure environment name |
| `AZURE_LOCATION` | ❌ No | `eastus` | Azure region |
| `AZURE_RESOURCE_GROUP` | ❌ No | `copilot-dashboard-rg` | Resource group name |

### Bicep Parameters

Configure infrastructure via `infra/main.parameters.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environmentName": {
      "value": "cpuad-dev"
    },
    "location": {
      "value": "eastus"
    },
    "doRoleAssignments": {
      "value": true
    }
  }
}
```

---

## Deployment Configuration (This Deployment)

**Deployment Date:** October 27, 2025  
**Deployment Owner:** Prestopa  
**Deployment Status:** ✅ **SUCCESSFUL**  
**Total Deployment Time:** 11 minutes 42 seconds

### Environment Variables Set

| Variable | Value |
|----------|-------|
| **GH_PAT** | `github_pat_••••••••••••••••••••••••••••••••••••••••` (masked for security) |
| **GH_ORGANIZATION_SLUGS** | `ms-mfg-community` |
| **AZURE_SUBSCRIPTION_ID** | `••••••••-••••-••••-••••-••••••••••••` (masked for security) |
| **AZURE_LOCATION** | `eastus2` |
| **GRAFANA_USERNAME** | `demouser` |
| **GRAFANA_PASSWORD** | `demouser` |
| **AZURE_ENV_NAME** | `dev` |

### Deployment Type
- ✅ **Simple Deployment** (without Entra ID SSO)
- Single dashboard instance
- Basic Grafana authentication with demo credentials

### Azure Resources Provisioned

| Resource Type | Resource Name | Purpose |
|---|---|---|
| **Resource Group** | `rg-ghc-dashboard` | Container for all resources |
| **Container Apps Environment** | `cae-5qntvmowb5mai` | Managed environment for containers |
| **Container App** | `elasticsearch` | Time-series data storage |
| **Container App** | `grafana` | Visualization and dashboards |
| **Container App Job** | `update-grafana` | Manual trigger to initialize Grafana |
| **Container App Job** | `cpuad-updater` | Scheduled job (hourly) to fetch Copilot metrics |
| **Container Registry** | `cr5qntvmowb5mai` | Private Docker image repository |
| **Key Vault** | `kv-5qntvmowb5mai` | Secrets storage (GitHub PAT, Grafana credentials) |
| **Managed Identity** | `id-5qntvmowb5mai` | Workload authentication (User-Assigned) |
| **Application Insights** | (auto-created) | Monitoring and observability |

### GitHub Organization Monitored
- **Organization:** `ms-mfg-community`
- **Copilot Metrics:** All teams, languages, editors, and seat assignments will be tracked
- **Data Update Schedule:** Every 1 hour (cron: `0 */1 * * *`)

### Accessing Grafana

To get your Grafana URL:

```powershell
az containerapp show -n grafana -g rg-ghc-dashboard --query "properties.configuration.ingress.fqdn" -o tsv
```

**Grafana URL:**
```
https://grafana.blueglacier-a006242b.eastus2.azurecontainerapps.io
```

**Login Credentials:**
- **Username:** `demouser`
- **Password:** `demouser`

**What to Expect:**

✅ **Immediate Access:**
- Grafana is live and ready to access
- The `update-grafana` job has already run to initialize dashboards

⏳ **Data Collection:**
- The `cpuad-updater` job is running on a schedule (every hour)
- **First data should appear in 5-10 minutes** once the job completes
- Monitor data will start populating from the `ms-mfg-community` GitHub organization

🔍 **Dashboards Available:**
- Copilot Usage Advanced Dashboard
- Copilot Usage Advanced Dashboard Original

**Next Steps:**
1. Open the URL in your browser
2. Login with the credentials above
3. Navigate to **Dashboards** section
4. Select either dashboard to view Copilot usage analytics
5. Give the background jobs a few minutes to fetch and display data

---

### Documentation Links
- [Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Developer CLI](https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [GitHub Copilot REST API](https://docs.github.com/en/rest/copilot/copilot-metrics)

### Repository Resources
- **Source:** https://github.com/autocloudarc/copilot-usage-advanced-dashboard
- **Original:** https://github.com/satomic/copilot-usage-advanced-dashboard
- **Issues:** Report bugs or request features in GitHub Issues
- **Discussions:** Join community discussions

### Getting Help
1. Check the troubleshooting section above
2. Review Azure logs via: `az containerapp logs show -n <app-name> -g <resource-group>`
3. Check Grafana settings page (⚙️ → Settings)
4. Open a GitHub issue with logs and configuration details

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-27 | Initial PRD - Deployment instructions, prerequisites, architecture overview, authentication guide |

---

**Document prepared for:** Deployment of GitHub Copilot Usage Advanced Dashboard  
**Last Updated:** October 27, 2025  
**Owner:** Repository Maintainers
