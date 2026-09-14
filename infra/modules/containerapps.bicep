// Azure Container Apps environment + Ollama (local LLM server), backend
// (FastAPI), and frontend (Next.js) apps.
//
// Ollama runs as its own internal-only Container App in this environment so
// the backend can reach it the same way it reaches localhost:11434 in dev —
// just over the environment's internal network instead. Pulled models
// persist on an Azure Files share so they aren't re-downloaded on every
// restart/revision.
//
// IMPORTANT: this runs Ollama on CPU (no GPU workload profile configured).
// An 8B model on CPU is noticeably slower than on a local GPU/Apple Silicon
// machine — expect a full 6-agent run to take several minutes longer in
// Azure than it does locally. If that's not acceptable, look into Azure
// Container Apps GPU workload profiles (region-limited, costs more) or
// swap the backend to a hosted LLM API for the cloud deployment only.
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
param ollamaModel string = 'llama3.1:8b'
param ollamaModelReasoning string = 'deepseek-r1:8b'
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

// --- Persistent storage for pulled Ollama models --------------------------
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: toLower(replace('${namePrefix}ollamasa', '-', ''))
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

resource ollamaShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-01-01' = {
  parent: fileService
  name: 'ollama-models'
  properties: { shareQuota: 100 }
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
    // Workload-profiles-v2 environment: keeps the default Consumption
    // profile (backend, frontend, and everything else stay pay-per-use)
    // and adds one Dedicated D4 node (4 vCPU / 16GB) exclusively for
    // Ollama, which was consistently crash-looping under Consumption's
    // hard 4GB ceiling — no 8B-class model reliably fit in it. Only
    // Ollama moves to this Dedicated profile; nothing else changes cost
    // shape. minimumCount/maximumCount pinned to 1 (no autoscaling) since
    // this is a single internal LLM service, not a bursty public workload.
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
      {
        name: 'ollama-dedicated'
        workloadProfileType: 'D4'
        minimumCount: 1
        maximumCount: 1
      }
    ]
  }
}

resource envStorage 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: containerAppEnv
  name: 'ollama-model-storage'
  properties: {
    azureFile: {
      accountName: storageAccount.name
      accountKey: storageAccount.listKeys().keys[0].value
      shareName: ollamaShare.name
      accessMode: 'ReadWrite'
    }
  }
}

// --- Ollama: internal-only, not exposed to the internet -------------------
resource ollamaApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: '${namePrefix}-ollama'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: containerAppEnv.id
    workloadProfileName: 'ollama-dedicated'
    configuration: {
      ingress: {
        external: false
        targetPort: 11434
        transport: 'http'
      }
    }
    template: {
      containers: [
        {
          name: 'ollama'
          image: 'ollama/ollama:latest'
          // Running on the 'ollama-dedicated' D4 profile (4 vCPU / 16GB
          // node) instead of Consumption, which was consistently
          // crash-looping trying to load even a single 8B model within its
          // hard 4GB ceiling. Dedicated profiles aren't restricted to
          // Consumption's fixed cpu:memory ratio table, so this requests
          // most of the node's capacity, leaving a couple GB of headroom
          // for the OS/platform rather than requesting the exact full 16Gi.
          resources: { cpu: json('4.0'), memory: '14Gi' }
          command: ['/bin/sh', '-c']
          args: [
            'ollama serve & sleep 5 && ollama pull ${ollamaModel} && ollama pull ${ollamaModelReasoning} && wait'
          ]
          volumeMounts: [
            { volumeName: 'ollama-models', mountPath: '/root/.ollama' }
          ]
        }
      ]
      volumes: [
        {
          name: 'ollama-models'
          storageType: 'AzureFile'
          storageName: envStorage.name
        }
      ]
      // Keep at 1 replica: this is CPU inference behind an internal-only
      // app, not a horizontally-scaled public service. Scale the box (cpu/
      // memory above) rather than replica count if you need more headroom.
      scale: { minReplicas: 1, maxReplicas: 1 }
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
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      secrets: [
        { name: 'cosmos-key', value: cosmosKey }
        { name: 'search-key', value: searchKey }
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
            { name: 'OLLAMA_BASE_URL', value: 'https://${ollamaApp.properties.configuration.ingress.fqdn}' }
            { name: 'OLLAMA_MODEL', value: ollamaModel }
            { name: 'OLLAMA_MODEL_REASONING', value: ollamaModelReasoning }
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
    workloadProfileName: 'Consumption'
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
output ollamaFqdn string = ollamaApp.properties.configuration.ingress.fqdn
output acrLoginServer string = acr.properties.loginServer
