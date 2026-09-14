// ============================================================================
// Main orchestrator: deploys the full CrewAI content pipeline infra on Azure
//   - Container Apps environment (backend API + optional frontend)
//   - Cosmos DB (jobs + content)
//   - Azure AI Search (vector/semantic)
//   - Log Analytics + Application Insights (Azure Monitor)
//   - Azure Container Registry
// ============================================================================
targetScope = 'resourceGroup'

@description('Short project name used as a resource-name prefix')
param projectName string = 'contentpipe'

@description('Deployment environment')
@allowed(['dev', 'staging', 'prod'])
param environmentName string = 'dev'

@description('Azure region for all resources')
param location string = resourceGroup().location

@description('Azure region for Cosmos DB specifically — independent from the main location, since Cosmos DB serverless account creation can be capacity-restricted per subscription per region, and a working region may differ from where your other resources live')
param cosmosLocation string = 'westus2'

@description('Azure region for Azure AI Search specifically — independent from the main location, since Semantic Search is only available in a subset of regions (South India is not one of them)')
param searchLocation string = 'westus2'

@description('Container image for the backend API (e.g. myregistry.azurecr.io/content-backend:latest)')
param backendImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Container image for the frontend (Next.js)')
param frontendImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Ollama tool-calling model, pulled automatically on first Ollama container start')
param ollamaModel string = 'llama3.1:8b'

@description('Ollama writing/reasoning model, pulled automatically on first Ollama container start')
param ollamaModelReasoning string = 'deepseek-r1:8b'

@secure()
@description('Shared bearer token the frontend uses to call the backend API')
param apiAuthToken string

var namePrefix = '${projectName}-${environmentName}'
var tags = {
  project: projectName
  environment: environmentName
  managedBy: 'bicep'
}

module monitor 'modules/monitor.bicep' = {
  name: 'monitorDeploy'
  params: {
    namePrefix: namePrefix
    location: location
    tags: tags
  }
}

module cosmos 'modules/cosmosdb.bicep' = {
  name: 'cosmosDeploy'
  params: {
    namePrefix: namePrefix
    location: cosmosLocation
    tags: tags
  }
}

module search 'modules/aisearch.bicep' = {
  name: 'searchDeploy'
  params: {
    namePrefix: namePrefix
    location: searchLocation
    tags: tags
  }
}

module containerApps 'modules/containerapps.bicep' = {
  name: 'containerAppsDeploy'
  params: {
    namePrefix: namePrefix
    location: location
    tags: tags
    backendImage: backendImage
    frontendImage: frontendImage
    ollamaModel: ollamaModel
    ollamaModelReasoning: ollamaModelReasoning
    apiAuthToken: apiAuthToken
    logAnalyticsWorkspaceId: monitor.outputs.logAnalyticsWorkspaceId
    appInsightsConnectionString: monitor.outputs.appInsightsConnectionString
    cosmosEndpoint: cosmos.outputs.cosmosEndpoint
    cosmosKey: cosmos.outputs.cosmosPrimaryKey
    searchEndpoint: search.outputs.searchEndpoint
    searchKey: search.outputs.searchAdminKey
  }
}

output backendUrl string = containerApps.outputs.backendFqdn
output frontendUrl string = containerApps.outputs.frontendFqdn
output ollamaUrl string = containerApps.outputs.ollamaFqdn
output cosmosAccountName string = cosmos.outputs.cosmosAccountName
output searchServiceName string = search.outputs.searchServiceName

