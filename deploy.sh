#!/bin/bash

# Azure Backend Deployment Script
echo "🚀 Preparing Alert Grader Backend for Azure Deployment..."

# Create deployment package
echo "📦 Creating deployment package..."
cd /Users/priyaj/alert-grader/backend-python

# Remove virtual environment and cache files
rm -rf venv
rm -rf __pycache__
rm -rf *.pyc
rm -rf .pytest_cache

# Create ZIP file
zip -r backend-deploy.zip . -x "*.git*" "*.DS_Store*" "test_*"

echo "✅ Deployment package created: backend-deploy.zip"
echo ""
echo "📋 Next steps:"
echo "1. Go to Azure Portal"
echo "2. Create App Service with Python 3.11 runtime"
echo "3. Upload backend-deploy.zip via Deployment Center"
echo "4. Set environment variables in Configuration"
echo "5. Test your deployed API"
echo ""
echo "🌐 Your backend will be available at: https://your-app-name.azurewebsites.net"
