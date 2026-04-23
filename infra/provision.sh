#!/usr/bin/env bash
# FinGuard Azure infrastructure provisioning — run ONCE before first deploy.
# Usage:  bash infra/provision.sh
#
# Prerequisites: az CLI logged in, correct subscription selected.
# After running, paste the printed values into GitHub Actions secrets/vars.
set -euo pipefail

# ── Configurable variables ────────────────────────────────────────────────────
APP_NAME="finguard"
LOCATION="eastus"                         # change to your preferred region
RG_STAGING="finguard-staging-rg"
RG_PROD="finguard-prod-rg"
ACR_NAME="finguardacr"                    # must be globally unique, lowercase, 5-50 chars
ACA_ENV_STAGING="finguard-staging-env"
ACA_ENV_PROD="finguard-prod-env"
STORAGE_ACCOUNT="finguardstore"           # globally unique, lowercase, 3-24 chars
FILE_SHARE_CHROMA="chromadb"
FILE_SHARE_DB="sqlitedb"
KV_NAME="finguard-kv"                     # globally unique
SP_NAME="finguard-github-oidc"
GITHUB_ORG="Harikrishna2461"              # your GitHub username / org
GITHUB_REPO="FinGuard_Agent"              # your GitHub repository name

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

echo "==> Subscription: $SUBSCRIPTION_ID  Tenant: $TENANT_ID"

# ── Resource groups ───────────────────────────────────────────────────────────
echo "==> Creating resource groups..."
az group create --name "$RG_STAGING" --location "$LOCATION" -o none
az group create --name "$RG_PROD"    --location "$LOCATION" -o none

# ── Azure Container Registry ──────────────────────────────────────────────────
echo "==> Creating Container Registry: $ACR_NAME..."
az acr create \
  --resource-group "$RG_STAGING" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true \
  -o none

ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

# ── Azure Files for persistent volumes ───────────────────────────────────────
echo "==> Creating Storage Account: $STORAGE_ACCOUNT..."
az storage account create \
  --name "$STORAGE_ACCOUNT" \
  --resource-group "$RG_STAGING" \
  --location "$LOCATION" \
  --sku Standard_LRS \
  -o none

STORAGE_KEY=$(az storage account keys list \
  --account-name "$STORAGE_ACCOUNT" \
  --resource-group "$RG_STAGING" \
  --query "[0].value" -o tsv)

az storage share create --name "$FILE_SHARE_CHROMA" \
  --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" -o none
az storage share create --name "$FILE_SHARE_DB" \
  --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" -o none

# ── Container Apps environments ───────────────────────────────────────────────
echo "==> Creating Container Apps environments..."
az containerapp env create \
  --name "$ACA_ENV_STAGING" \
  --resource-group "$RG_STAGING" \
  --location "$LOCATION" \
  -o none

# Mount Azure Files into the staging environment
az containerapp env storage set \
  --name "$ACA_ENV_STAGING" \
  --resource-group "$RG_STAGING" \
  --storage-name chromadb-storage \
  --azure-file-account-name "$STORAGE_ACCOUNT" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$FILE_SHARE_CHROMA" \
  --access-mode ReadWrite \
  -o none

az containerapp env storage set \
  --name "$ACA_ENV_STAGING" \
  --resource-group "$RG_STAGING" \
  --storage-name sqlite-storage \
  --azure-file-account-name "$STORAGE_ACCOUNT" \
  --azure-file-account-key "$STORAGE_KEY" \
  --azure-file-share-name "$FILE_SHARE_DB" \
  --access-mode ReadWrite \
  -o none

az containerapp env create \
  --name "$ACA_ENV_PROD" \
  --resource-group "$RG_PROD" \
  --location "$LOCATION" \
  -o none

# ── Key Vault + secrets ───────────────────────────────────────────────────────
echo "==> Creating Key Vault: $KV_NAME..."
az keyvault create \
  --name "$KV_NAME" \
  --resource-group "$RG_STAGING" \
  --location "$LOCATION" \
  -o none

echo ""
echo "  Add your secrets to Key Vault now:"
echo "    az keyvault secret set --vault-name $KV_NAME --name groq-api-key    --value '<YOUR_GROQ_API_KEY>'"
echo "    az keyvault secret set --vault-name $KV_NAME --name flask-secret-key --value '$(python3 -c \"import secrets; print(secrets.token_hex(32))\")'"
echo "    az keyvault secret set --vault-name $KV_NAME --name jwt-secret       --value '$(python3 -c \"import secrets; print(secrets.token_hex(32))\")'"
echo ""

# ── Service Principal for GitHub Actions (OIDC) ───────────────────────────────
echo "==> Creating Service Principal for GitHub OIDC: $SP_NAME..."
SP_APP_ID=$(az ad app create --display-name "$SP_NAME" --query appId -o tsv)
az ad sp create --id "$SP_APP_ID" -o none

# Assign Contributor on both resource groups
az role assignment create \
  --assignee "$SP_APP_ID" \
  --role Contributor \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RG_STAGING" \
  -o none
az role assignment create \
  --assignee "$SP_APP_ID" \
  --role Contributor \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RG_PROD" \
  -o none

# Also needs AcrPush to push images
az role assignment create \
  --assignee "$SP_APP_ID" \
  --role AcrPush \
  --scope "$(az acr show --name $ACR_NAME --query id -o tsv)" \
  -o none

# OIDC federated credentials so GitHub Actions can log in without a client secret
az ad app federated-credential create --id "$SP_APP_ID" --parameters "{
  \"name\": \"github-staging\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:environment:staging\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" -o none

az ad app federated-credential create --id "$SP_APP_ID" --parameters "{
  \"name\": \"github-production\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:environment:production\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" -o none

az ad app federated-credential create --id "$SP_APP_ID" --parameters "{
  \"name\": \"github-main-push\",
  \"issuer\": \"https://token.actions.githubusercontent.com\",
  \"subject\": \"repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main\",
  \"audiences\": [\"api://AzureADTokenExchange\"]
}" -o none

# ── Print GitHub secrets/vars to add ─────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  COPY THESE INTO GitHub → Settings → Secrets and Variables → Actions"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "── SECRETS (sensitive) ─────────────────────────────────────────────"
echo "  AZURE_CLIENT_ID       = $SP_APP_ID"
echo "  AZURE_TENANT_ID       = $TENANT_ID"
echo "  AZURE_SUBSCRIPTION_ID = $SUBSCRIPTION_ID"
echo "  ACR_USERNAME          = $ACR_USERNAME"
echo "  ACR_PASSWORD          = $ACR_PASSWORD"
echo "  GROQ_API_KEY          = <your Groq API key from console.groq.com>"
echo ""
echo "── VARIABLES (non-sensitive) ────────────────────────────────────────"
echo "  ACR_LOGIN_SERVER      = $ACR_LOGIN_SERVER"
echo "  AZURE_RESOURCE_GROUP  = $RG_STAGING"
echo "  ACA_ENVIRONMENT       = $ACA_ENV_STAGING"
echo "  AZURE_RESOURCE_GROUP_PROD = $RG_PROD"
echo "  ACA_ENVIRONMENT_PROD  = $ACA_ENV_PROD"
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "Done. Run 'docker compose up --build' locally to test before pushing."
