# Azure Container Apps Deployment Guide for EstimateDoc

## Overview
This guide explains how to deploy the EstimateDoc application to Azure Container Apps.

## Prerequisites
- Azure CLI installed (`brew install azure-cli` on macOS)
- Docker installed and running
- Azure subscription
- Git repository access

## Deployment Architecture
```
Resource Group: Alterspective Consulting Services
├── Container Registry: alterspectiveacr
├── Container Apps Environment: estimatedoc-container-env
└── Container App: estimatedoc-app
```

## Quick Deployment

### 1. Make the deployment script executable
```bash
chmod +x azure-deploy.sh
```

### 2. Run the deployment script
```bash
./azure-deploy.sh
```

The script will:
- Check/create the resource group
- Create an Azure Container Registry (if needed)
- Build and push the Docker image
- Create the Container Apps environment
- Deploy the application

## Manual Deployment Steps

### 1. Login to Azure
```bash
az login
```

### 2. Create Resource Group (if it doesn't exist)
```bash
az group create \
  --name "Alterspective Consulting Services" \
  --location eastus
```

### 3. Create Azure Container Registry
```bash
az acr create \
  --resource-group "Alterspective Consulting Services" \
  --name alterspectiveacr \
  --sku Basic \
  --admin-enabled true
```

### 4. Build and Push Docker Image
```bash
# Build the production application
npm run build

# Build Docker image
docker build -t estimatedoc:latest .

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name alterspectiveacr --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name alterspectiveacr --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name alterspectiveacr --query passwords[0].value -o tsv)

# Login to ACR
docker login $ACR_LOGIN_SERVER -u $ACR_USERNAME -p $ACR_PASSWORD

# Tag and push image
docker tag estimatedoc:latest $ACR_LOGIN_SERVER/estimatedoc:latest
docker push $ACR_LOGIN_SERVER/estimatedoc:latest
```

### 5. Create Container Apps Environment
```bash
az containerapp env create \
  --name estimatedoc-container-env \
  --resource-group "Alterspective Consulting Services" \
  --location eastus
```

### 6. Deploy the Container App
```bash
az containerapp create \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --environment estimatedoc-container-env \
  --image $ACR_LOGIN_SERVER/estimatedoc:latest \
  --target-port 80 \
  --ingress external \
  --registry-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 0.5 \
  --memory 1.0 \
  --min-replicas 1 \
  --max-replicas 3
```

### 7. Get the Application URL
```bash
az containerapp show \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --query properties.configuration.ingress.fqdn \
  -o tsv
```

## Updating the Application

To update the application after making changes:

```bash
# 1. Rebuild the application
npm run build

# 2. Rebuild and push the Docker image
docker build -t estimatedoc:latest .
docker tag estimatedoc:latest $ACR_LOGIN_SERVER/estimatedoc:latest
docker push $ACR_LOGIN_SERVER/estimatedoc:latest

# 3. Update the Container App
az containerapp update \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --image $ACR_LOGIN_SERVER/estimatedoc:latest
```

## GitHub Actions CI/CD (Optional)

### Setup Secrets in GitHub
1. Go to your GitHub repository
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following secrets:

#### AZURE_CREDENTIALS
Create a service principal and get credentials:
```bash
az ad sp create-for-rbac \
  --name "estimatedoc-github-actions" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/"Alterspective Consulting Services" \
  --sdk-auth
```

Copy the entire JSON output to the secret.

#### REGISTRY_USERNAME and REGISTRY_PASSWORD
```bash
az acr credential show --name alterspectiveacr --query username -o tsv
az acr credential show --name alterspectiveacr --query passwords[0].value -o tsv
```

## Application Features
Once deployed, the EstimateDoc application provides:
- 336 document templates analysis
- 748.48 total hours estimation
- Field-by-field breakdown
- Complexity analysis (Complex/Moderate/Simple)
- Interactive calculator
- Advanced analytics dashboard

## Monitoring and Logs

### View Application Logs
```bash
az containerapp logs show \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --follow
```

### View Metrics
```bash
az monitor metrics list \
  --resource /subscriptions/{subscription-id}/resourceGroups/Alterspective Consulting Services/providers/Microsoft.App/containerApps/estimatedoc-app \
  --metric "Requests" \
  --interval PT1M
```

## Cost Optimization
- The app is configured with:
  - 0.5 vCPU and 1GB RAM
  - Auto-scaling from 1 to 3 replicas
  - This should cost approximately $15-30/month

## Troubleshooting

### Container App won't start
- Check logs: `az containerapp logs show --name estimatedoc-app --resource-group "Alterspective Consulting Services"`
- Verify image exists in ACR: `az acr repository list --name alterspectiveacr`

### Cannot access the application
- Verify ingress is set to external
- Check the FQDN is correct
- Ensure no firewall rules are blocking access

### Build failures
- Ensure Node.js 20+ is installed
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`

## Support
For issues or questions about the EstimateDoc application deployment, please refer to:
- Azure Container Apps documentation: https://docs.microsoft.com/azure/container-apps/
- Application repository: [Your GitHub Repository]

## Clean Up Resources (if needed)
To remove all resources and avoid charges:
```bash
az group delete --name "Alterspective Consulting Services" --yes --no-wait
```

---
Last Updated: 2025-09-10
Estimated Total Documents: 336
Total Effort Hours: 748.48