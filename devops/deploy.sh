#!/usr/bin/env bash
# Manual/local deployment helper — provisions infra and deploys both apps.
# For automated CI/CD, use .github/workflows/ci-cd.yml instead (this script
# is for one-off manual deploys or the very first bootstrap run).
# Usage: ./devops/deploy.sh <resource-group> <location> <anthropic-api-key>
set -euo pipefail

RESOURCE_GROUP="${1:?Usage: deploy.sh <resource-group> <location> <anthropic-api-key>}"
LOCATION="${2:-eastus}"
ANTHROPIC_API_KEY="${3:?Provide your Anthropic API key as the 3rd argument (from https://console.anthropic.com/settings/keys)}"
API_AUTH_TOKEN="${4:-$(openssl rand -hex 32)}"

echo "==> Creating resource group: $RESOURCE_GROUP ($LOCATION)"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "==> Deploying Bicep infrastructure"
az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file infra/main.bicep \
  --parameters infra/parameters.json \
  --parameters location="$LOCATION" apiAuthToken="$API_AUTH_TOKEN" anthropicApiKey="$ANTHROPIC_API_KEY"

echo "==> Building and pushing images via ACR Tasks"
ACR_NAME=$(az deployment group show -g "$RESOURCE_GROUP" -n main --query properties.outputs.acrLoginServer.value -o tsv 2>/dev/null || true)

az acr build --registry "$ACR_NAME" --image content-backend:latest ./backend
az acr build --registry "$ACR_NAME" --image content-frontend:latest ./frontend

echo "==> Done. Fetch app URLs with: az containerapp list -g $RESOURCE_GROUP -o table"
echo "==> API auth token (save this — it's also what the frontend uses to call the backend):"
echo "    $API_AUTH_TOKEN"