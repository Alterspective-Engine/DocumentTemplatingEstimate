#!/bin/bash

# Azure deployment script for EstimateDoc Application
# This script deploys the app to Azure Container Apps with custom domain support

# Configuration
RESOURCE_GROUP="Alterspective Consulting Services"
LOCATION="eastus"
CONTAINER_ENV_NAME="estimatedoc-container-env"
CONTAINER_APP_NAME="estimatedoc-app"
REGISTRY_NAME="alterspectiveacr"
IMAGE_NAME="estimatedoc"
IMAGE_TAG="latest"
CUSTOM_DOMAIN="template-discoveryandestimate-mb.alterspective.com.au"

echo "🚀 Starting Azure Container Apps deployment for EstimateDoc..."
echo "📍 Target domain: $CUSTOM_DOMAIN"
echo ""

# Check if logged in to Azure
echo "📝 Checking Azure login status..."
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Not logged in to Azure. Please login:"
    az login
fi

# Set the subscription (optional - remove if using default)
# az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create or verify resource group
echo "🔍 Checking resource group '$RESOURCE_GROUP'..."
az group show --name "$RESOURCE_GROUP" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📦 Creating new resource group '$RESOURCE_GROUP' in $LOCATION..."
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --tags "Application=EstimateDoc" "Environment=Production" "ManagedBy=AlterspectiveConsulting"
    
    if [ $? -eq 0 ]; then
        echo "✅ Resource group created successfully"
    else
        echo "❌ Failed to create resource group. Exiting."
        exit 1
    fi
else
    echo "✅ Resource group exists"
fi

# Create Azure Container Registry if it doesn't exist
echo "🔍 Checking Azure Container Registry..."
az acr show --name $REGISTRY_NAME --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📦 Creating Azure Container Registry..."
    az acr create \
        --resource-group "$RESOURCE_GROUP" \
        --name $REGISTRY_NAME \
        --sku Basic \
        --admin-enabled true
else
    echo "✅ Container Registry exists"
fi

# Get ACR credentials
echo "🔑 Getting ACR credentials..."
ACR_USERNAME=$(az acr credential show --name $REGISTRY_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $REGISTRY_NAME --query passwords[0].value -o tsv)
ACR_LOGIN_SERVER=$(az acr show --name $REGISTRY_NAME --query loginServer -o tsv)

# Build and push Docker image
echo "🏗️  Building Docker image..."
docker build -t $IMAGE_NAME:$IMAGE_TAG .

echo "🏷️  Tagging image for ACR..."
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

echo "🔐 Logging in to ACR..."
docker login $ACR_LOGIN_SERVER -u $ACR_USERNAME -p $ACR_PASSWORD

echo "📤 Pushing image to ACR..."
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

# Create Container Apps environment if it doesn't exist
echo "🔍 Checking Container Apps environment..."
az containerapp env show \
    --name $CONTAINER_ENV_NAME \
    --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📦 Creating Container Apps environment..."
    az containerapp env create \
        --name $CONTAINER_ENV_NAME \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION"
else
    echo "✅ Container Apps environment exists"
fi

# Create or update the Container App
echo "🔍 Checking if Container App exists..."
az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group "$RESOURCE_GROUP" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "📦 Creating Container App..."
    az containerapp create \
        --name $CONTAINER_APP_NAME \
        --resource-group "$RESOURCE_GROUP" \
        --environment $CONTAINER_ENV_NAME \
        --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
        --target-port 80 \
        --ingress external \
        --registry-server $ACR_LOGIN_SERVER \
        --registry-username $ACR_USERNAME \
        --registry-password $ACR_PASSWORD \
        --cpu 0.5 \
        --memory 1.0 \
        --min-replicas 1 \
        --max-replicas 3
else
    echo "🔄 Updating existing Container App..."
    az containerapp update \
        --name $CONTAINER_APP_NAME \
        --resource-group "$RESOURCE_GROUP" \
        --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG
fi

# Get the application URL
echo "🔍 Getting application URL..."
APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.configuration.ingress.fqdn \
    -o tsv)

# Configure custom domain
echo ""
echo "🌐 Configuring custom domain: $CUSTOM_DOMAIN"
echo ""

# Add custom domain to Container App
echo "📝 Adding custom domain to Container App..."
az containerapp hostname add \
    --name $CONTAINER_APP_NAME \
    --resource-group "$RESOURCE_GROUP" \
    --hostname $CUSTOM_DOMAIN \
    --output none 2>/dev/null

# Get the verification details
echo "🔍 Getting DNS configuration requirements..."
VERIFICATION_ID=$(az containerapp hostname list \
    --name $CONTAINER_APP_NAME \
    --resource-group "$RESOURCE_GROUP" \
    --query "[?name=='$CUSTOM_DOMAIN'].validationToken" \
    -o tsv 2>/dev/null)

echo ""
echo "=================================================================================="
echo "✅ Deployment complete!"
echo "=================================================================================="
echo ""
echo "🌐 Application URLs:"
echo "   Default Azure URL: https://$APP_URL"
echo "   Custom Domain: https://$CUSTOM_DOMAIN (after DNS configuration)"
echo ""
echo "📊 EstimateDoc Application Details:"
echo "   - Resource Group: $RESOURCE_GROUP"
echo "   - Container Environment: $CONTAINER_ENV_NAME"
echo "   - Container App: $CONTAINER_APP_NAME"
echo "   - Container Registry: $REGISTRY_NAME"
echo "   - Custom Domain: $CUSTOM_DOMAIN"
echo ""
echo "=================================================================================="
echo "📌 IMPORTANT: DNS Configuration Required"
echo "=================================================================================="
echo ""
echo "To activate your custom domain, add these DNS records at your domain provider:"
echo ""
echo "1️⃣  CNAME Record:"
echo "   Host: template-discoveryandestimate-mb"
echo "   Points to: $APP_URL"
echo "   TTL: 3600 (or your preference)"
echo ""
if [ ! -z "$VERIFICATION_ID" ]; then
    echo "2️⃣  TXT Record (for domain verification):"
    echo "   Host: asuid.template-discoveryandestimate-mb"
    echo "   Value: $VERIFICATION_ID"
    echo "   TTL: 3600"
    echo ""
fi
echo "3️⃣  After adding DNS records:"
echo "   - DNS propagation typically takes 15-60 minutes"
echo "   - SSL certificate will be automatically provisioned"
echo "   - Your app will be accessible at: https://$CUSTOM_DOMAIN"
echo ""
echo "=================================================================================="
echo "🎉 Your EstimateDoc app is now live on Azure Container Apps!"
echo "=================================================================================="