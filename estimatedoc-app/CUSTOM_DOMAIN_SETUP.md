# Custom Domain Setup Guide
## template-discoveryandestimate-mb.alterspective.com.au

This guide explains how to configure the custom domain for your EstimateDoc application on Azure Container Apps.

## 🌐 Custom Domain Details
- **Full Domain**: `template-discoveryandestimate-mb.alterspective.com.au`
- **Subdomain**: `template-discoveryandestimate-mb`
- **Root Domain**: `alterspective.com.au`

## 📋 Prerequisites
1. Access to DNS management for `alterspective.com.au`
2. Azure Container App deployed (run `./azure-deploy.sh` first)
3. DNS provider account credentials

## 🚀 Automatic Setup (During Deployment)
The `azure-deploy.sh` script automatically:
1. Creates all required Azure resources
2. Deploys the application
3. Configures the custom domain in Azure
4. Provides DNS records to add at your provider

## 📝 Manual DNS Configuration Steps

### Step 1: Run Deployment
```bash
./azure-deploy.sh
```

After deployment, you'll receive:
- The Azure Container App URL (e.g., `estimatedoc-app.politedesert-xxxxx.eastus.azurecontainerapps.io`)
- DNS configuration instructions
- Domain verification token

### Step 2: Add DNS Records
Log into your DNS provider (where `alterspective.com.au` is managed) and add:

#### 1. CNAME Record
```
Type: CNAME
Host/Name: template-discoveryandestimate-mb
Value/Points to: [Your Azure Container App URL]
TTL: 3600 (1 hour)
```

#### 2. TXT Record (for verification)
```
Type: TXT
Host/Name: asuid.template-discoveryandestimate-mb
Value: [Verification token from deployment output]
TTL: 3600 (1 hour)
```

### Step 3: Verify Domain Configuration
After adding DNS records, run:
```bash
# Check DNS propagation
nslookup template-discoveryandestimate-mb.alterspective.com.au

# Verify in Azure
az containerapp hostname list \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services"
```

### Step 4: SSL Certificate
Azure automatically provisions a free SSL certificate once DNS is configured. This process:
- Starts after DNS verification
- Takes 5-15 minutes
- Provides HTTPS automatically

## 🔍 DNS Providers - Specific Instructions

### GoDaddy
1. Log into GoDaddy account
2. Go to "My Products" → "DNS"
3. Click "Add" → Choose record type
4. Enter the values above

### Cloudflare
1. Log into Cloudflare
2. Select your domain
3. Go to "DNS" tab
4. Click "Add record"
5. **Important**: Set proxy status to "DNS only" (gray cloud)

### AWS Route 53
1. Open Route 53 console
2. Select your hosted zone
3. Click "Create record"
4. Enter the values above

### Azure DNS
```bash
# CNAME Record
az network dns record-set cname set-record \
  --resource-group [DNS-RG] \
  --zone-name alterspective.com.au \
  --record-set-name template-discoveryandestimate-mb \
  --cname [Azure-App-URL]

# TXT Record
az network dns record-set txt add-record \
  --resource-group [DNS-RG] \
  --zone-name alterspective.com.au \
  --record-set-name asuid.template-discoveryandestimate-mb \
  --value "[Verification-Token]"
```

## ✅ Verification Checklist

### DNS Propagation (15-60 minutes)
- [ ] CNAME record resolves correctly
- [ ] TXT record is visible
- [ ] Domain verification in Azure succeeds

### SSL Certificate (5-15 minutes after DNS)
- [ ] Certificate provisioned
- [ ] HTTPS works without warnings
- [ ] Automatic HTTP to HTTPS redirect

### Testing
```bash
# Test DNS resolution
dig template-discoveryandestimate-mb.alterspective.com.au

# Test HTTPS
curl -I https://template-discoveryandestimate-mb.alterspective.com.au

# Check certificate
openssl s_client -connect template-discoveryandestimate-mb.alterspective.com.au:443 -servername template-discoveryandestimate-mb.alterspective.com.au
```

## 🔧 Troubleshooting

### DNS Not Resolving
- Wait up to 48 hours for full propagation
- Clear DNS cache: `sudo dscacheutil -flushcache` (macOS)
- Try different DNS servers: `nslookup template-discoveryandestimate-mb.alterspective.com.au 8.8.8.8`

### Certificate Errors
- Ensure DNS records are correct
- Wait for automatic provisioning (up to 8 hours)
- Check domain ownership verification

### Domain Not Working
```bash
# Re-bind the domain
az containerapp hostname bind \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --hostname template-discoveryandestimate-mb.alterspective.com.au

# Check binding status
az containerapp hostname list \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services"
```

## 📊 Expected Timeline
1. **Deployment**: 5-10 minutes
2. **DNS Addition**: 5 minutes (manual)
3. **DNS Propagation**: 15-60 minutes
4. **SSL Provisioning**: 5-15 minutes
5. **Total**: ~30-90 minutes

## 🎯 Final Result
Once complete, your EstimateDoc application will be accessible at:
```
https://template-discoveryandestimate-mb.alterspective.com.au
```

With:
- ✅ Full HTTPS encryption
- ✅ Automatic certificate renewal
- ✅ Professional custom domain
- ✅ 336 documents analyzed
- ✅ 748.48 total hours estimation

## 🆘 Support Commands

### Get Current Status
```bash
# Check app status
az containerapp show \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --query "{URL:properties.configuration.ingress.fqdn, Status:properties.provisioningState}"

# Check custom domain status
az containerapp hostname list \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --query "[].{Domain:name, Status:validationStatus}" \
  --output table
```

### Remove Custom Domain (if needed)
```bash
az containerapp hostname delete \
  --name estimatedoc-app \
  --resource-group "Alterspective Consulting Services" \
  --hostname template-discoveryandestimate-mb.alterspective.com.au \
  --yes
```

---
**Note**: Keep your DNS records even after successful setup. They're required for the domain to continue working.