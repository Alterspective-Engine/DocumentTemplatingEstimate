# Environment Configuration Guide

## Overview
The EstimateDoc deployment now uses a `.env` file for all configuration settings, making it easy to manage different environments and keep sensitive information secure.

## Configuration File: `.env`

The deployment script reads all settings from the `.env` file in the project root. This file contains:
- Azure resource names and locations
- Container configuration
- Custom domain settings
- Resource sizing parameters

## Setup Instructions

### 1. Initial Setup
The `.env` file is already configured with your settings:
```bash
# View current configuration
cat .env
```

### 2. Configuration Values

#### Required Settings
```bash
# Azure Resource Configuration
AZURE_RESOURCE_GROUP="Alterspective Consulting Services"
AZURE_LOCATION="eastus"

# Container Apps Configuration
CONTAINER_ENV_NAME="estimatedoc-container-env"
CONTAINER_APP_NAME="estimatedoc-app"

# Azure Container Registry
REGISTRY_NAME="alterspectiveacr"
IMAGE_NAME="estimatedoc"

# Custom Domain
CUSTOM_DOMAIN="template-discoveryandestimate-mb.alterspective.com.au"
```

#### Optional Settings
```bash
# Docker image version
IMAGE_TAG="latest"

# Resource sizing
CONTAINER_CPU="0.5"      # vCPU cores
CONTAINER_MEMORY="1.0"    # GB RAM
MIN_REPLICAS="1"          # Minimum instances
MAX_REPLICAS="3"          # Maximum instances

# Azure subscription (if multiple)
# AZURE_SUBSCRIPTION_ID="your-subscription-id"
```

## How It Works

### Automatic Loading
When you run `./azure-deploy.sh`:
1. Script checks for `.env` file
2. Loads all configuration values
3. Validates required settings
4. Uses values throughout deployment

### Validation
The script validates that all required variables are present:
- If any are missing, it lists them and exits
- Provides clear error messages
- Ensures deployment won't fail due to missing config

### Fallback Behavior
- If `.env` doesn't exist but `.env.example` exists, it creates `.env` from template
- Uses default values for optional settings if not specified
- Prompts to edit configuration before proceeding

## Managing Multiple Environments

### Development Environment
Create `.env.development`:
```bash
AZURE_RESOURCE_GROUP="EstimateDoc-Dev"
CONTAINER_APP_NAME="estimatedoc-dev"
# ... other dev settings
```

### Production Environment
Use main `.env` for production:
```bash
AZURE_RESOURCE_GROUP="Alterspective Consulting Services"
CONTAINER_APP_NAME="estimatedoc-app"
# ... production settings
```

### Switching Environments
```bash
# Use development
cp .env.development .env
./azure-deploy.sh

# Use production
cp .env.production .env
./azure-deploy.sh
```

## Security Best Practices

### 1. Never Commit `.env`
The `.env` file is in `.gitignore` to prevent accidental commits:
- ✅ Commit `.env.example` (template without sensitive data)
- ❌ Never commit `.env` (contains actual configuration)

### 2. Sensitive Information
For highly sensitive data (passwords, keys):
```bash
# Option 1: Use Azure Key Vault references
KEY_VAULT_NAME="your-keyvault"

# Option 2: Set as environment variables before running
export DB_PASSWORD="secret"
./azure-deploy.sh
```

### 3. Access Control
- Keep `.env` file permissions restricted: `chmod 600 .env`
- Share `.env.example` with team members
- Each developer creates their own `.env`

## Updating Configuration

### Change a Setting
1. Edit `.env` file:
```bash
nano .env
# or
code .env
```

2. Run deployment:
```bash
./azure-deploy.sh
```

### Add New Settings
1. Add to `.env`:
```bash
echo 'NEW_SETTING="value"' >> .env
```

2. Update script to use it:
```bash
NEW_VAR="${NEW_SETTING:-default}"
```

## Troubleshooting

### Missing .env File
```bash
❌ No .env file found
```
**Solution**: Copy from template:
```bash
cp .env.example .env
# Edit with your values
nano .env
```

### Missing Variables
```bash
❌ Missing required environment variables:
   - AZURE_RESOURCE_GROUP
   - CUSTOM_DOMAIN
```
**Solution**: Add missing values to `.env`

### Invalid Values
```bash
❌ Invalid location: "invalid-region"
```
**Solution**: Check Azure documentation for valid regions

## Quick Reference

### View Current Configuration
```bash
# Show all settings (masks sensitive values)
grep -v '^#' .env | grep -v '^$'

# Check specific setting
grep "CUSTOM_DOMAIN" .env
```

### Validate Configuration
```bash
# Test configuration loading
source .env
echo "Resource Group: $AZURE_RESOURCE_GROUP"
echo "Domain: $CUSTOM_DOMAIN"
```

### Reset to Defaults
```bash
# Restore from example
cp .env.example .env
# Edit with your values
nano .env
```

## Benefits of .env Configuration

1. **Portability**: Easy to share configurations
2. **Security**: Sensitive data not in scripts
3. **Flexibility**: Quick environment switches
4. **Clarity**: All settings in one place
5. **Version Control**: Template in git, actual values local
6. **Consistency**: Same values across all scripts

## Summary

Your deployment configuration is now centralized in the `.env` file:
- **Location**: `/estimatedoc-app/.env`
- **Template**: `/estimatedoc-app/.env.example`
- **Ignored by Git**: Yes (for security)
- **Required for Deployment**: Yes
- **Can be Modified**: Anytime

The deployment script automatically reads these settings, making deployments consistent and manageable across different environments and team members.