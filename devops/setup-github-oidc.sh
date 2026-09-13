#!/usr/bin/env bash
# ============================================================================
# ONE-TIME setup: run this once locally (with `az login` already done) to
# prepare Azure + GitHub for CI/CD via OpenID Connect (OIDC). No client
# secret or password is ever stored — GitHub exchanges a short-lived OIDC
# token for an Azure access token on every workflow run.
#
# Safe to re-run: every step checks whether the resource already exists
# before trying to create it, so a partial/failed previous run won't error
# out on the second attempt.
#
# Usage: ./devops/setup-github-oidc.sh <github-org-or-username> <github-repo> [location]
# Example: ./devops/setup-github-oidc.sh tanmaychakraborty content-pipeline eastus
# ============================================================================
set -euo pipefail

GITHUB_ORG="${1:?Usage: setup-github-oidc.sh <github-org-or-username> <github-repo> [location]}"
GITHUB_REPO="${2:?Usage: setup-github-oidc.sh <github-org-or-username> <github-repo> [location]}"
LOCATION="${3:-eastus}"

RESOURCE_GROUP="rg-content-pipeline-dev"
# Must exactly match what Bicep generates: toLower(replace('${projectName}-${environmentName}acr','-','')).
# Default projectName=contentpipe, environmentName=dev -> "contentpipedevacr". Change here AND in
# .github/workflows/ci-cd.yml's ACR_NAME if you use different project/environment names.
ACR_NAME="contentpipedevacr"
APP_NAME="content-pipeline-github-oidc"

# --- Resource providers -------------------------------------------------------
# On newer/free-tier subscriptions these namespaces often aren't registered
# until the first time something tries to use them, which is exactly the
# MissingSubscriptionRegistration error this avoids. Registering is async and
# idempotent — safe to call every run, and a no-op once already registered.
echo "==> Registering required resource providers (safe to re-run, no-op if already done)"
for NAMESPACE in Microsoft.ContainerRegistry Microsoft.App Microsoft.OperationalInsights \
                 Microsoft.Insights Microsoft.DocumentDB Microsoft.Search Microsoft.Storage; do
  STATE=$(az provider show --namespace "$NAMESPACE" --query registrationState -o tsv 2>/dev/null || echo "NotRegistered")
  if [ "$STATE" == "Registered" ]; then
    echo "    $NAMESPACE: already registered"
  else
    echo "    $NAMESPACE: registering..."
    az provider register --namespace "$NAMESPACE" --output none
  fi
done

echo "    Waiting for registration to finish (usually under a minute)..."
for NAMESPACE in Microsoft.ContainerRegistry Microsoft.App Microsoft.OperationalInsights \
                 Microsoft.Insights Microsoft.DocumentDB Microsoft.Search Microsoft.Storage; do
  for i in $(seq 1 30); do
    STATE=$(az provider show --namespace "$NAMESPACE" --query registrationState -o tsv)
    [ "$STATE" == "Registered" ] && break
    sleep 5
  done
  echo "    $NAMESPACE: $STATE"
done

# --- Resource group ---------------------------------------------------------
echo "==> Resource group: $RESOURCE_GROUP"
if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
  EXISTING_LOCATION=$(az group show --name "$RESOURCE_GROUP" --query location -o tsv)
  if [ "$EXISTING_LOCATION" != "$LOCATION" ]; then
    echo "    Already exists in '$EXISTING_LOCATION' (you asked for '$LOCATION')."
    echo "    A resource group's region can't be changed after creation, so using '$EXISTING_LOCATION'."
    echo "    Remember to set infra/parameters.json's \"location\" to \"$EXISTING_LOCATION\" too."
    LOCATION="$EXISTING_LOCATION"
  else
    echo "    Already exists in '$LOCATION' — skipping creation."
  fi
else
  echo "    Creating in '$LOCATION'..."
  az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
fi

# --- Container Registry ------------------------------------------------------
echo "==> Azure Container Registry: $ACR_NAME"
if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
  echo "    Already exists — skipping creation."
else
  echo "    Creating..."
  az acr create \
    --resource-group "$RESOURCE_GROUP" \
    --name "$ACR_NAME" \
    --sku Basic \
    --admin-enabled true \
    --output none
fi

# --- Azure AD app registration -----------------------------------------------
echo "==> Azure AD app registration: $APP_NAME"
APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)
if [ -n "$APP_ID" ]; then
  echo "    Already exists (appId: $APP_ID) — skipping creation."
else
  echo "    Creating..."
  az ad app create --display-name "$APP_NAME" --output none
  APP_ID=$(az ad app list --display-name "$APP_NAME" --query "[0].appId" -o tsv)
fi

# --- Service principal --------------------------------------------------------
echo "==> Service principal for the app"
if az ad sp show --id "$APP_ID" &>/dev/null; then
  echo "    Already exists — skipping creation."
else
  echo "    Creating..."
  az ad sp create --id "$APP_ID" --output none
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# --- Role assignment -----------------------------------------------------------
echo "==> Contributor role assignment on the resource group"
SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP"
EXISTING_ROLE=$(az role assignment list --assignee "$APP_ID" --scope "$SCOPE" \
  --query "[?roleDefinitionName=='Contributor'] | [0].id" -o tsv 2>/dev/null || true)
if [ -n "$EXISTING_ROLE" ]; then
  echo "    Already assigned — skipping."
else
  echo "    Assigning..."
  az role assignment create \
    --assignee "$APP_ID" \
    --role "Contributor" \
    --scope "$SCOPE" \
    --output none
fi

# --- Federated credentials -----------------------------------------------------
# GitHub changed its default OIDC subject format for repos created/renamed on
# or after July 15, 2026: newer repos embed immutable numeric owner/repo IDs
# ("repo:OWNER@OWNER_ID/REPO@REPO_ID:...") instead of just names, to prevent
# subject recycling if a repo/org name is later reused by someone else. Older
# repos may still use the plain-name format. Rather than detect which one
# applies, this creates federated credentials for BOTH formats — unused ones
# are simply inert, and this way it works regardless of when the repo was
# created or whether GitHub changes the default again later.
create_federated_credential() {
  local cred_name="$1"
  local subject="$2"
  local existing
  existing=$(az ad app federated-credential list --id "$APP_ID" \
    --query "[?name=='$cred_name'] | [0].name" -o tsv 2>/dev/null || true)
  if [ -n "$existing" ]; then
    echo "    '$cred_name' already exists — skipping."
  else
    echo "    Creating '$cred_name'..."
    az ad app federated-credential create --id "$APP_ID" --parameters "{
      \"name\": \"$cred_name\",
      \"issuer\": \"https://token.actions.githubusercontent.com\",
      \"subject\": \"$subject\",
      \"audiences\": [\"api://AzureADTokenExchange\"]
    }" --output none
  fi
}

echo "==> Federated credentials: pushes to main (name-based format)"
create_federated_credential "github-main-branch" "repo:${GITHUB_ORG}/${GITHUB_REPO}:ref:refs/heads/main"

echo "==> Federated credentials: 'production' GitHub Environment (name-based format)"
create_federated_credential "github-production-environment" "repo:${GITHUB_ORG}/${GITHUB_REPO}:environment:production"

echo "==> Looking up immutable owner/repo IDs from the GitHub API (for repos on the new subject format)"
REPO_JSON=$(curl -sf "https://api.github.com/repos/${GITHUB_ORG}/${GITHUB_REPO}" || true)
if [ -n "$REPO_JSON" ] && echo "$REPO_JSON" | python3 -c "import json,sys; json.load(sys.stdin)['id']" &>/dev/null; then
  OWNER_ID=$(echo "$REPO_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['owner']['id'])")
  REPO_ID=$(echo "$REPO_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
  echo "    Found owner_id=$OWNER_ID repo_id=$REPO_ID"

  echo "==> Federated credentials: pushes to main (immutable-ID format)"
  create_federated_credential "github-main-branch-immutable" \
    "repo:${GITHUB_ORG}@${OWNER_ID}/${GITHUB_REPO}@${REPO_ID}:ref:refs/heads/main"

  echo "==> Federated credentials: 'production' GitHub Environment (immutable-ID format)"
  create_federated_credential "github-production-environment-immutable" \
    "repo:${GITHUB_ORG}@${OWNER_ID}/${GITHUB_REPO}@${REPO_ID}:environment:production"
else
  echo "    Couldn't fetch repo info from the public GitHub API (private repo, rate limit, or"
  echo "    typo in org/repo name). If your workflow later fails with 'No matching federated"
  echo "    identity record found', the error message shows the exact subject GitHub sent —"
  echo "    copy the owner_id/repo_id numbers from it and re-run this script, or add the"
  echo "    federated credential manually using those values."
fi

# --- Summary ---------------------------------------------------------------
echo ""
echo "==> Done. Add these as GitHub repo secrets (Settings > Secrets and variables > Actions):"
echo "AZURE_CLIENT_ID:       $APP_ID"
echo "AZURE_TENANT_ID:       $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
echo ""
echo "Also add this secret if you don't already have one saved from a previous run:"
echo "API_AUTH_TOKEN:        $(openssl rand -hex 32)"
echo ""
echo "Also create a GitHub Environment named 'production' (Settings > Environments) if you haven't."
echo ""
echo "Region used: $LOCATION"
echo "Make sure infra/parameters.json's \"location\" value matches this."