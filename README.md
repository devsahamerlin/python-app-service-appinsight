# FastAPI Azure App Service with Application Insights - Deployment Guide

This guide walks you through deploying a FastAPI application to Azure App Service with Azure Application Insights integration for logging and monitoring.

## Prerequisites

- Azure subscription
- Azure CLI installed and logged in
- Git repository with your code
- Python 3.12+ for local development

## Project Structure

```
fastapi-azure-app/
│
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── startup.sh             # Linux startup script
├── runtime.txt            # Python version specification
└── README.md              # This file
```

## Step 1: Create Azure Resources

### 1.1 Create Resource Group
```bash
az group create --name myResourceGroup --location westeurope
```

### 1.2 Create Application Insights
```bash
az monitor app-insights component create \
  --app myFastAPIAppInsights \
  --location westeurope \
  --resource-group myResourceGroup \
  --application-type web
```

**Save the Connection String** from the output - you'll need it later.

### 1.3 Create App Service Plan
```bash
az appservice plan create \
  --name myAppServicePlan \
  --resource-group myResourceGroup \
  --location westeurope --sku P1V3 --is-linux \
  --is-linux
```

### 1.4 Create Web App
```bash
az webapp create \
  --resource-group myResourceGroup \
  --plan myAppServicePlan \
  --name myFastAPI2025App \
  --runtime "PYTHON|3.12" \
  --deployment-local-git
```

## Step 2: Configure Environment Variables

Set the Application Insights connection string:

```bash
az webapp config appsettings set \
  --resource-group myResourceGroup \
  --name myFastAPI2025App \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="YOUR_CONNECTION_STRING_HERE" PORT="8000"
```

## Configure Startup Command

Set the startup command for your FastAPI app:

```bash
az webapp config set \
  --resource-group myResourceGroup \
  --name myFastAPI2025App \
  --startup-file "python -m uvicorn main:app --host 0.0.0.0 --port 8000"
```

## Verify Deployment

1. **Check app status:**
```bash
az webapp show \
  --name myFastAPI2025App \
  --resource-group myResourceGroup \
  --query state
```

2. **Browse to your app:**
```bash
az webapp browse \
  --name myFastAPI2025App \
  --resource-group myResourceGroup
```

3. **Test endpoints:**
   - Health check: `https://yourapp.azurewebsites.net/health`
   - API docs: `https://yourapp.azurewebsites.net/docs`
   - Root: `https://yourapp.azurewebsites.net/`
  
## Monitor Logs and Metrics

### View Logs
```bash
# Stream logs
az webapp log tail \
  --name myFastAPI2025App \
  --resource-group myResourceGroup

# Download logs
az webapp log download \
  --name myFastAPI2025App \
  --resource-group myResourceGroup
```
### Application Insights

1. **Navigate to Azure Portal → Application Insights → your instance**

2. **Key monitoring areas:**
   - **Live Metrics**: Real-time performance data
   - **Application Map**: Service dependencies and performance
   - **Performance**: Response times and throughput
   - **Failures**: Exception tracking and error rates
   - **Logs**: Custom logs from your application

3. **Useful KQL queries:**
```kusto
// Custom logs from the application
traces
| where timestamp > ago(1h)
| order by timestamp desc

// Performance metrics
requests
| where timestamp > ago(1h)
| summarize avg(duration) by bin(timestamp, 5m)

// Error tracking
exceptions
| where timestamp > ago(1h)
| order by timestamp desc
```

## Scaling and Performance

### Auto-scaling
```bash
# Create autoscale setting
az monitor autoscale create \
  --resource-group myResourceGroup \
  --resource myFastAPI2025App \
  --resource-type Microsoft.Web/sites \
  --name myAutoscaleProfile \
  --min-count 1 \
  --max-count 5 \
  --count 2
```

### Performance tuning
- Use Application Insights to identify bottlenecks
- Monitor response times and error rates

## Troubleshooting

### Common Issues

1. **App won't start:**
   - Check startup command
   - Verify requirements.txt
   - Check Application Insights connection string

2. **502 Bad Gateway:**
   - Check if port is correctly configured
   - Verify uvicorn is binding to correct host/port

3. **Dependencies not installing:**
   - Ensure requirements.txt is in root directory
   - Check Python version compatibility

4. **Logs not appearing in Application Insights:**
   - Verify connection string is correct
   - Check if environment variable is set
   - Allow 5-10 minutes for logs to appear

### Debug Commands
```bash
# Check app settings
az webapp config appsettings list \
  --name myFastAPI2025App \
  --resource-group myResourceGroup

# Restart app
az webapp restart \
  --name myFastAPI2025App \
  --resource-group myResourceGroup

# SSH into container (for troubleshooting)
az webapp ssh \
  --name myFastAPI2025App \
  --resource-group myResourceGroup
```


## Security Best Practices

1. **Environment Variables**: Store sensitive data in App Settings, not in code
2. **HTTPS**: Always use HTTPS in production (enabled by default)
3. **CORS**: Configure CORS appropriately for your use case
5. **Logging**: Never log sensitive information

## Cost Optimization

1. **Right-size your App Service Plan**
2. **Use auto-scaling** to handle traffic spikes
3. **Monitor Application Insights** usage to stay within free tier limits
4. **Use staging slots** for testing before production deployment

## Next Steps

1. **Add a database** (Azure SQL Database, CosmosDB, or PostgreSQL)
2. **Set up CI/CD pipelines** with GitHub Actions or Azure DevOps

Your FastAPI application is now running on Azure App Service with logging and monitoring through Application Insights!
