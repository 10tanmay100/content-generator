// Azure Container Apps environment + backend (FastAPI) and frontend
// (Next.js) apps. Both run on the default Consumption profile — pay only
// for active usage.
//
// The backend calls Anthropic's Claude API directly for every agent (no
// self-hosted model server), which is why this is dramatically simpler
// than earlier versions of this file: no Ollama container, no persistent
// model storage, no Dedicated workload profile, no memory tuning. Claude
// runs on Anthropic's infrastructure, not ours.
param namePrefix string
param location string
param tags object

param backendImage string
param frontendImage string
param logAnalyticsWorkspaceId string
param appInsightsConnectionString string
param cosmosEndpoint string
@secure()
param cosmosKey string
param searchEndpoint string
@secure()
param searchKey string
@secure()
param anthropicApiKey string
param anthropicModel string = 'claude-sonnet-5'
@secure()
param apiAuthToken string

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2023-09-01' existing = {
  name: last(split(logAnalyticsWorkspaceId, '/'))
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: toLower(replace('${namePrefix}acr', '-', ''))
  location: location
  tags: tags
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: true }
}

resource containerAppEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${namePrefix}-env'
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// --- Backend: FastAPI, public ----------------------------------------------
resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-backend'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        { name: 'cosmos-key', value: cosmosKey }
        { name: 'search-key', value: searchKey }
        { name: 'anthropic-api-key', value: anthropicApiKey }
        { name: 'api-auth-token', value: apiAuthToken }
        { name: 'acr-password', value: acr.listCredentials().passwords[0].value }
      ]
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: { cpu: json('1.0'), memory: '2Gi' }
          env: [
            { name: 'ENVIRONMENT', value: 'production' }
            { name: 'ANTHROPIC_API_KEY', secretRef: 'anthropic-api-key' }
            { name: 'ANTHROPIC_MODEL', value: anthropicModel }
            { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
            { name: 'COSMOS_KEY', secretRef: 'cosmos-key' }
            { name: 'AZURE_SEARCH_ENDPOINT', value: searchEndpoint }
            { name: 'AZURE_SEARCH_API_KEY', secretRef: 'search-key' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
            { name: 'PUBLIC_BASE_URL', value: 'https://${namePrefix}-backend.${containerAppEnv.properties.defaultDomain}' }
            { name: 'CORS_ORIGINS', value: 'https://${namePrefix}-frontend.${containerAppEnv.properties.defaultDomain}' }
            { name: 'API_AUTH_TOKEN', secretRef: 'api-auth-token' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/api/v1/health', port: 8000 }
              initialDelaySeconds: 15
            }
            {
              type: 'Readiness'
              httpGet: { path: '/api/v1/health/ready', port: 8000 }
              initialDelaySeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scale'
            http: { metadata: { concurrentRequests: '20' } }
          }
        ]
      }
    }
  }
}

// --- Frontend: Next.js, public ----------------------------------------------
resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-frontend'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          username: acr.listCredentials().username
          passwordSecretRef: 'acr-password'
        }
      ]
      secrets: [
        { name: 'acr-password', value: acr.listCredentials().passwords[0].value }
        { name: 'api-auth-token', value: apiAuthToken }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'NEXT_PUBLIC_API_BASE_URL', value: 'https://${backendApp.properties.configuration.ingress.fqdn}/api/v1' }
            { name: 'BACKEND_API_TOKEN', secretRef: 'api-auth-token' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}

output backendFqdn string = backendApp.properties.configuration.ingress.fqdn
output frontendFqdn string = frontendApp.properties.configuration.ingress.fqdn
output acrLoginServer string = acr.properties.loginServer
