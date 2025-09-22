# 🚀 Git Deployment Guide for Azure App Service

## **Step 1: Set Up Git Repository**

✅ **Already Done**: Git repository initialized and committed

## **Step 2: Configure Azure App Service for Git Deployment**

### **Option A: Local Git (Recommended)**

1. **Go to Azure Portal** → Your App Service
2. **Deployment Center** → **Local Git**
3. **Configure**:
   - **Source**: Local Git
   - **Branch**: master
4. **Save** - This will give you a Git URL

### **Option B: GitHub Integration**

1. **Deployment Center** → **GitHub**
2. **Authorize** your GitHub account
3. **Select Repository**: Choose your backend repository
4. **Branch**: master

## **Step 3: Deploy via Git**

### **For Local Git Deployment:**

```bash
# Add Azure as remote origin
git remote add azure <your-azure-git-url>

# Deploy to Azure
git push azure master
```

### **For GitHub Deployment:**

```bash
# Push to GitHub
git remote add origin <your-github-repo-url>
git push -u origin master
```

## **Step 4: Configure Environment Variables**

In Azure Portal:
1. **Settings** → **Configuration** → **Application settings**
2. **Add**:
   - **Name**: `BLOB_ACCOUNT_URL`
   - **Value**: `https://agstorage11.blob.core.windows.net`

## **Step 5: Test Deployment**

Your backend will be available at: `https://your-app-name.azurewebsites.net`

Test:
```bash
curl https://your-app-name.azurewebsites.net/api/health
```

## **🔄 Continuous Deployment**

Once set up, every `git push` will automatically deploy your changes!

## **📋 Files Included in Deployment**

- ✅ `app.py` - Flask application
- ✅ `requirements.txt` - Python dependencies
- ✅ `startup.py` - Azure startup script
- ✅ `.deployment` - Deployment configuration
- ✅ `web.config` - IIS configuration
- ✅ `.gitignore` - Git ignore rules

## **🚨 Important Notes**

1. **No venv/ folder** - Azure will install dependencies from requirements.txt
2. **Automatic builds** - Azure detects Python and installs dependencies
3. **Environment variables** - Set in Azure Portal Configuration
4. **Logs** - Available in Azure Portal → Monitoring → Log stream

## **🔧 Troubleshooting**

### **Common Issues:**

1. **Build fails**: Check requirements.txt syntax
2. **Import errors**: Ensure all dependencies are listed
3. **Port issues**: Azure sets PORT environment variable automatically
4. **Authentication**: Ensure App Service has access to storage account

### **View Logs:**
- **Azure Portal** → **App Service** → **Monitoring** → **Log stream**
- **Deployment logs**: **Deployment Center** → **Logs**

## **🎯 Next Steps After Deployment**

1. **Test API endpoints**
2. **Update frontend** to use production backend URL
3. **Set up monitoring** and alerts
4. **Configure custom domain** (optional)
