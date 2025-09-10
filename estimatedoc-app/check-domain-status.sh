#!/bin/bash

# Domain status checker for EstimateDoc
CUSTOM_DOMAIN="template-discoveryandestimate-mb.alterspective.com.au"
RESOURCE_GROUP="Alterspective Consulting Services"
CONTAINER_APP_NAME="estimatedoc-app"

echo "=================================================================================="
echo "🔍 EstimateDoc Custom Domain Status Checker"
echo "=================================================================================="
echo ""
echo "Domain: $CUSTOM_DOMAIN"
echo "Checking time: $(date)"
echo ""

# Check if logged in to Azure
az account show > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Not logged in to Azure. Please login first:"
    echo "   az login"
    exit 1
fi

# Check DNS Resolution
echo "1️⃣  DNS Resolution Check"
echo "------------------------"
DNS_RESULT=$(nslookup $CUSTOM_DOMAIN 2>&1)
if echo "$DNS_RESULT" | grep -q "can't find"; then
    echo "❌ DNS not configured or not propagated yet"
    echo "   Please add CNAME record pointing to your Azure Container App URL"
else
    echo "✅ DNS is resolving"
    echo "$DNS_RESULT" | grep -A2 "canonical name"
fi
echo ""

# Check Azure Container App
echo "2️⃣  Azure Container App Status"
echo "------------------------------"
APP_STATUS=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group "$RESOURCE_GROUP" \
    --query "{Status:properties.provisioningState, URL:properties.configuration.ingress.fqdn}" \
    -o json 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ Container App is running"
    echo "   Azure URL: https://$(echo $APP_STATUS | jq -r .URL)"
    echo "   Status: $(echo $APP_STATUS | jq -r .Status)"
else
    echo "❌ Container App not found or not accessible"
fi
echo ""

# Check Custom Domain Binding
echo "3️⃣  Custom Domain Configuration"
echo "-------------------------------"
DOMAIN_STATUS=$(az containerapp hostname list \
    --name $CONTAINER_APP_NAME \
    --resource-group "$RESOURCE_GROUP" \
    --query "[?name=='$CUSTOM_DOMAIN']" \
    -o json 2>/dev/null)

if [ "$DOMAIN_STATUS" == "[]" ] || [ -z "$DOMAIN_STATUS" ]; then
    echo "❌ Custom domain not configured in Azure"
    echo "   Run ./azure-deploy.sh to configure the domain"
else
    VALIDATION_STATUS=$(echo $DOMAIN_STATUS | jq -r '.[0].validationStatus')
    BINDING_STATUS=$(echo $DOMAIN_STATUS | jq -r '.[0].bindingType')
    
    if [ "$VALIDATION_STATUS" == "Succeeded" ]; then
        echo "✅ Domain validation succeeded"
    else
        echo "⚠️  Domain validation status: $VALIDATION_STATUS"
        echo "   Verification token: $(echo $DOMAIN_STATUS | jq -r '.[0].validationToken')"
    fi
    echo "   Binding type: $BINDING_STATUS"
fi
echo ""

# Check HTTPS Certificate
echo "4️⃣  SSL Certificate Status"
echo "-------------------------"
CERT_CHECK=$(timeout 5 openssl s_client -connect $CUSTOM_DOMAIN:443 -servername $CUSTOM_DOMAIN 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

if [ $? -eq 0 ]; then
    echo "✅ SSL Certificate is active"
    echo "$CERT_CHECK"
else
    echo "⚠️  SSL Certificate not yet provisioned or domain not accessible"
    echo "   This is normal if DNS was recently configured (wait 15-30 minutes)"
fi
echo ""

# Test HTTP/HTTPS Access
echo "5️⃣  Accessibility Test"
echo "---------------------"
HTTP_CHECK=$(curl -s -o /dev/null -w "%{http_code}" -m 5 http://$CUSTOM_DOMAIN 2>/dev/null)
HTTPS_CHECK=$(curl -s -o /dev/null -w "%{http_code}" -m 5 https://$CUSTOM_DOMAIN 2>/dev/null)

if [ "$HTTPS_CHECK" == "200" ]; then
    echo "✅ HTTPS is working (Status: $HTTPS_CHECK)"
    echo "   Your app is live at: https://$CUSTOM_DOMAIN"
elif [ "$HTTP_CHECK" == "200" ] || [ "$HTTP_CHECK" == "301" ] || [ "$HTTP_CHECK" == "302" ]; then
    echo "⚠️  HTTP is responding (Status: $HTTP_CHECK) but HTTPS not yet ready"
    echo "   SSL certificate may still be provisioning"
else
    echo "❌ Domain not accessible yet"
    echo "   HTTP Status: $HTTP_CHECK"
    echo "   HTTPS Status: $HTTPS_CHECK"
    echo "   This is normal if DNS was recently configured"
fi
echo ""

# Summary
echo "=================================================================================="
echo "📊 Summary"
echo "=================================================================================="

if [ "$HTTPS_CHECK" == "200" ]; then
    echo "🎉 SUCCESS! Your app is live at:"
    echo "   https://$CUSTOM_DOMAIN"
else
    echo "⏳ Setup in progress. Next steps:"
    echo ""
    echo "1. Ensure DNS records are added at your domain provider:"
    echo "   - CNAME: template-discoveryandestimate-mb → [Azure App URL]"
    echo "   - TXT: asuid.template-discoveryandestimate-mb → [Verification Token]"
    echo ""
    echo "2. Wait for DNS propagation (15-60 minutes)"
    echo "3. SSL certificate will auto-provision after DNS verification"
    echo "4. Run this script again to check status"
fi
echo ""
echo "=================================================================================="