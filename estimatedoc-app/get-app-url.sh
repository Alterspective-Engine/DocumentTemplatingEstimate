#!/bin/bash

# Script to get the EstimateDoc application URL

echo "🔍 Getting EstimateDoc URL..."

# Get the FQDN (Fully Qualified Domain Name)
APP_URL=$(az containerapp show \
    --name estimatedoc-app \
    --resource-group "Alterspective Consulting Services" \
    --query properties.configuration.ingress.fqdn \
    -o tsv 2>/dev/null)

if [ -z "$APP_URL" ]; then
    echo "❌ App not found. It may not be deployed yet."
    echo "   Run ./azure-deploy.sh to deploy the application."
else
    echo ""
    echo "✅ Your EstimateDoc app is available at:"
    echo ""
    echo "   🌐 https://$APP_URL"
    echo ""
    echo "📋 Click the link above or copy it to your browser"
    echo ""
    
    # Try to open in default browser (macOS)
    if command -v open &> /dev/null; then
        echo "Opening in your default browser..."
        open "https://$APP_URL"
    fi
fi