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
az group create --name azureMonitoringRgDemoSm --location westeurope
```

### 1.2 Create Application Insights
```bash
az monitor app-insights component create \
  --app myFastAPIAppInsights \
  --location westeurope \
  --resource-group azureMonitoringRgDemoSm \
  --application-type web
```

**Save the Connection String** from the output - you'll need it later.

### 1.3 Create App Service Plan
```bash
az appservice plan create \
  --name myAppServicePlan \
  --resource-group azureMonitoringRgDemoSm \
  --location westeurope --sku P1V3 --is-linux \
  --is-linux
```

### 1.4 Create Web App
```bash
az webapp create \
  --resource-group azureMonitoringRgDemoSm \
  --plan myAppServicePlan \
  --name pyhtonfastapidemoapp \
  --runtime "PYTHON|3.12" \
  --deployment-local-git
```

## Step 2: Configure Environment Variables

Set the Application Insights connection string:

```bash
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name pyhtonfastapidemoapp \
  --settings APPLICATIONINSIGHTS_CONNECTION_STRING="YOUR_CONNECTION_STRING_HERE" PORT="8000"
```

Optional environment variables:
```bash
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name pyhtonfastapidemoapp \
  --settings ENVIRONMENT="production" \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true \
  ENABLE_ORYX_BUILD=true
```

## Step 3: Configure Startup Command

Set the startup command for your FastAPI app:

```bash
az webapp config set \
  --resource-group azureMonitoringRgDemoSm \
  --name pyhtonfastapidemoapp \
  --startup-file "python -m uvicorn main:app --host 0.0.0.0 --port 8000"
```

## Step 4: Deploy Your Application

### Option A: Git Deployment

1. Get the Git deployment URL:
```bash
az webapp deployment source config-local-git \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm
```

2. Add Azure as a remote:
```bash
git remote add azure <git-clone-url-from-step-1>
```

3. Deploy:
```bash
git add .
git commit -m "Deploy FastAPI app"
git push azure main
```

### Option B: ZIP Deployment

1. Create a ZIP file of your application:
```bash
zip -r myapp.zip . -x "*.git*" "*__pycache__*" "*.DS_Store*"
```

2. Deploy the ZIP:
```bash
az webapp deployment source config-zip \
  --resource-group azureMonitoringRgDemoSm \
  --name pyhtonfastapidemoapp \
  --src myapp.zip
```

### Option C: GitHub Actions (Recommended for CI/CD)

1. Create `.github/workflows/azure-webapp.yml`:

2. Get publish profile:
```bash
az webapp deployment list-publishing-profiles \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm \
  --xml
```

3. Add the publish profile as a GitHub secret named `AZUREAPPSERVICE_PUBLISHPROFILE`.

## Step 5: Verify Deployment

1. **Check app status:**
```bash
az webapp show \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm \
  --query state
```

2. **Browse to your app:**
```bash
az webapp browse \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm
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
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm

# Download logs
az webapp log download \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm
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
  --resource-group azureMonitoringRgDemoSm \
  --resource pyhtonfastapidemoapp \
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
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm

# Restart app
az webapp restart \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm

# SSH into container (for troubleshooting)
az webapp ssh \
  --name pyhtonfastapidemoapp \
  --resource-group azureMonitoringRgDemoSm
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

Your FastAPI application is now running on Azure App Service with comprehensive logging and monitoring through Application Insights!

# Azure MySQL Flexible Server Setup Guide

This guide shows how to create and configure Azure MySQL Flexible Server for your FastAPI application.

## Step 1: Create Azure MySQL Flexible Server

### 1.1 Create MySQL Server
```bash
# Create MySQL Flexible Server
az mysql flexible-server create \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --location "East US" \
  --admin-user myadmin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 8.0.21 \
  --storage-size 20 \
  --storage-auto-grow Enabled \
  --backup-retention 7 \
  --yes
```

**Important**: Save the admin username and password - you'll need them for the connection string.

### 1.2 Create Database
```bash
# Create the application database
az mysql flexible-server db create \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --database-name fastapi_db
```

### 1.3 Configure Firewall (Allow Azure Services)
```bash
# Allow Azure services to access the database
az mysql flexible-server firewall-rule create \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 1.4 Allow Your Local IP (for development)
```bash
# Get your public IP
MY_IP=$(curl -s https://ipinfo.io/ip)

# Add firewall rule for your IP
az mysql flexible-server firewall-rule create \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --rule-name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP
```

## Step 2: Get Connection Information

### 2.1 Get Server Details
```bash
az mysql flexible-server show \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --query "fullyQualifiedDomainName" \
  --output tsv
```

This will return something like: `myfastapidb.mysql.database.azure.com`

### 2.2 Test Connection (Optional)
```bash
# Install MySQL client (if not already installed)
# Ubuntu/Debian: sudo apt-get install mysql-client
# macOS: brew install mysql-client

# Test connection
mysql -h myfastapidb.mysql.database.azure.com \
      -u myadmin \
      -p \
      fastapi_db
```

## Step 3: Configure App Service Environment Variables

### 3.1 Set Database Connection Variables
```bash
# Set database configuration in App Service
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp \
  --settings \
    DB_HOST="myfastapidb.mysql.database.azure.com" \
    DB_PORT="3306" \
    DB_USER="myadmin" \
    DB_PASSWORD="YourSecurePassword123!" \
    DB_NAME="fastapi_db"
```

### 3.2 Alternative: Use Connection String
```bash
# Or use a full connection string (more secure)
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp \
  --settings \
    DATABASE_URL="mysql://myadmin:YourSecurePassword123!@myfastapidb.mysql.database.azure.com:3306/fastapi_db"
```

## Step 4: Security Best Practices

### 4.1 Use Azure Key Vault (Recommended)
```bash
# Create Key Vault
az keyvault create \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIKeyVault \
  --location "East US"

# Store database password in Key Vault
az keyvault secret set \
  --vault-name myFastAPIKeyVault \
  --name "db-password" \
  --value "YourSecurePassword123!"

# Grant App Service access to Key Vault
az webapp identity assign \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp

# Get the principal ID (from the output above)
PRINCIPAL_ID=$(az webapp identity show \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp \
  --query principalId \
  --output tsv)

# Grant access to Key Vault
az keyvault set-policy \
  --name myFastAPIKeyVault \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get

# Use Key Vault reference in App Service
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp \
  --settings \
    DB_PASSWORD="@Microsoft.KeyVault(VaultName=myFastAPIKeyVault;SecretName=db-password)"
```

### 4.2 Enable SSL (Always use in production)
```bash
# SSL is enabled by default on Azure MySQL Flexible Server
# Verify SSL is required
az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name require_secure_transport \
  --value ON
```

## Step 5: Database Schema Management

### 5.1 Create Migration Script
Create `migrations/001_initial_schema.sql`:
```sql
-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    age INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

-- Insert sample data (optional)
INSERT IGNORE INTO users (name, email, age) VALUES 
('John Doe', 'john@example.com', 30),
('Jane Smith', 'jane@example.com', 25);
```

### 5.2 Run Migration Locally
```bash
# Run migration script
mysql -h myfastapidb.mysql.database.azure.com \
      -u myadmin \
      -p \
      fastapi_db < migrations/001_initial_schema.sql
```

## Step 6: Local Development Setup

### 6.1 Environment Variables for Local Development
Create `.env` file:
```env
# Database Configuration
DB_HOST=myfastapidb.mysql.database.azure.com
DB_PORT=3306
DB_USER=myadmin
DB_PASSWORD=YourSecurePassword123!
DB_NAME=fastapi_db

# Application Insights (optional for local dev)
APPLICATIONINSIGHTS_CONNECTION_STRING=""

# Environment
ENVIRONMENT=development
PORT=8000
```

### 6.2 Load Environment Variables
Update `run_local.sh`:
```bash
#!/bin/bash
echo "Setting up local development environment..."

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "Environment variables loaded from .env"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting FastAPI application locally..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 7: Monitoring and Maintenance

### 7.1 Enable Query Performance Insights
```bash
# Enable slow query log
az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name slow_query_log \
  --value ON

az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name long_query_time \
  --value 2
```

### 7.2 Monitor Database Metrics
```bash
# View database metrics
az monitor metrics list \
  --resource "/subscriptions/{subscription-id}/resourceGroups/azureMonitoringRgDemoSm/providers/Microsoft.DBforMySQL/flexibleServers/myfastapidb" \
  --metric "cpu_percent,memory_percent,io_consumption_percent"
```

### 7.3 Setup Backup Policy (Optional)
```bash
# Backups are automatic, but you can configure retention
az mysql flexible-server update \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --backup-retention 30
```

## Step 8: Testing Database Integration

### 8.1 Test API Endpoints
```bash
# Test user creation
curl -X POST "https://yourapp.azurewebsites.net/users" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test User", "email": "test@example.com", "age": 25}'

# Test getting all users
curl "https://yourapp.azurewebsites.net/users"

# Test getting specific user
curl "https://yourapp.azurewebsites.net/users/1"

# Test metrics (should show database connection status)
curl "https://yourapp.azurewebsites.net/metrics"
```

### 8.2 Verify Database Tables
```sql
-- Connect to database and verify tables
SHOW TABLES;
DESCRIBE users;
SELECT * FROM users;
```

## Step 9: Troubleshooting

### Common Issues:

1. **Connection Timeout**
   - Check firewall rules
   - Verify connection string
   - Ensure App Service can reach database

2. **Authentication Failed**
   - Verify username/password
   - Check if user exists and has proper permissions

3. **SSL Connection Issues**
   - Ensure SSL certificates are properly configured
   - Try disabling SSL for debugging (not recommended for production)

4. **Performance Issues**
   - Monitor connection pool usage
   - Check slow query log
   - Consider upgrading server tier

### Debug Commands:
```bash
# Check App Service logs
az webapp log tail --name myFastAPIApp --resource-group azureMonitoringRgDemoSm

# Check database server status
az mysql flexible-server show \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb

# Test connectivity from App Service
az webapp ssh --name myFastAPIApp --resource-group azureMonitoringRgDemoSm
# Then inside the container:
# python -c "import aiomysql; print('aiomysql imported successfully')"
```

## Step 10: Production Optimizations

### 10.1 Connection Pool Configuration
Update your `main.py` database configuration for production:
```python
# Production database configuration
DATABASE_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'db': os.environ.get('DB_NAME'),
    'charset': 'utf8mb4',
    'autocommit': True,
    'minsize': 5,  # Minimum connections in pool
    'maxsize': 20, # Maximum connections in pool
    'pool_recycle': 3600,  # Recycle connections every hour
    'connect_timeout': 10,  # Connection timeout
    'echo': False  # Set to True for debugging
}
```

### 10.2 Database Indexing
```sql
-- Add indexes for better performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_name ON users(name);

-- For full-text search (if needed)
ALTER TABLE users ADD FULLTEXT(name);
```

### 10.3 Enable Connection Pooling in MySQL
```bash
# Configure MySQL parameters for better connection handling
az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name max_connections \
  --value 100

az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name wait_timeout \
  --value 600
```

## Step 11: Advanced Features

### 11.1 Read Replicas (for high availability)
```bash
# Create a read replica
az mysql flexible-server replica create \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb-replica \
  --source-server myfastapidb
```

### 11.2 Database Maintenance Window
```bash
# Set maintenance window
az mysql flexible-server update \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --maintenance-window day=6 hour=2 minute=0
```

### 11.3 Point-in-Time Restore (if needed)
```bash
# Restore database to a specific point in time
az mysql flexible-server restore \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb-restored \
  --source-server myfastapidb \
  --restore-time "2024-01-01T12:00:00Z"
```

## Step 12: Cost Optimization

### 12.1 Right-size Your Database
```bash
# Monitor resource usage and scale accordingly
az mysql flexible-server update \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --sku-name Standard_B2s  # Upgrade if needed

# Or scale down if usage is low
az mysql flexible-server update \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --sku-name Standard_B1ms
```

### 12.2 Storage Auto-grow
```bash
# Enable auto-grow to avoid manual intervention
az mysql flexible-server update \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --storage-auto-grow Enabled
```

## Step 13: Disaster Recovery

### 13.1 Backup Strategy
```bash
# Configure geo-redundant backup (if available in region)
az mysql flexible-server update \
  --resource-group azureMonitoringRgDemoSm \
  --name myfastapidb \
  --geo-redundant-backup Enabled
```

### 13.2 Export Database Schema and Data
```bash
# Export schema
mysqldump -h myfastapidb.mysql.database.azure.com \
          -u myadmin \
          -p \
          --no-data \
          fastapi_db > schema_backup.sql

# Export data
mysqldump -h myfastapidb.mysql.database.azure.com \
          -u myadmin \
          -p \
          --no-create-info \
          fastapi_db > data_backup.sql

# Full backup
mysqldump -h myfastapidb.mysql.database.azure.com \
          -u myadmin \
          -p \
          fastapi_db > full_backup.sql
```

## Step 14: Environment-Specific Configuration

### 14.1 Development Environment
```bash
# Create a separate database for development
az mysql flexible-server db create \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --database-name fastapi_db_dev
```

### 14.2 Staging Environment
```bash
# Create staging database
az mysql flexible-server db create \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --database-name fastapi_db_staging
```

### 14.3 Multiple Environment App Settings
```bash
# Production slot
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp \
  --slot production \
  --settings DB_NAME="fastapi_db"

# Staging slot
az webapp config appsettings set \
  --resource-group azureMonitoringRgDemoSm \
  --name myFastAPIApp \
  --slot staging \
  --settings DB_NAME="fastapi_db_staging"
```

## Step 15: Monitoring Database Performance

### 15.1 Enable Performance Insights
```bash
# Enable Query Performance Insight
az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name log_output \
  --value FILE

az mysql flexible-server parameter set \
  --resource-group azureMonitoringRgDemoSm \
  --server-name myfastapidb \
  --name general_log \
  --value ON
```

### 15.2 Custom Monitoring Queries
Add to your FastAPI application:
```python
@app.get("/db-health", tags=["Monitoring"])
async def database_health_check():
    """Check database health and performance"""
    try:
        async with await get_db_connection() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                # Check connection
                await cursor.execute("SELECT 1")
                
                # Get database stats
                await cursor.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        MAX(created_at) as last_user_created,
                        MIN(created_at) as first_user_created
                    FROM users
                """)
                stats = await cursor.fetchone()
                
                # Check table status
                await cursor.execute("SHOW TABLE STATUS LIKE 'users'")
                table_info = await cursor.fetchone()
                
                return {
                    "status": "healthy",
                    "database": DATABASE_CONFIG['db'],
                    "host": DATABASE_CONFIG['host'],
                    "total_users": stats['total_users'],
                    "last_user_created": stats['last_user_created'].isoformat() if stats['last_user_created'] else None,
                    "first_user_created": stats['first_user_created'].isoformat() if stats['first_user_created'] else None,
                    "table_rows": table_info['Rows'] if table_info else 0,
                    "table_size_mb": round(table_info['Data_length'] / 1024 / 1024, 2) if table_info else 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Summary

Your FastAPI application now has:

1. ✅ **MySQL Flexible Server integration** with connection pooling
2. ✅ **Automatic table creation** on startup
3. ✅ **CRUD operations** with proper error handling
4. ✅ **Azure Application Insights logging** for database operations
5. ✅ **Health checks** for database connectivity
6. ✅ **Production-ready configuration** with environment variables
7. ✅ **Security best practices** with SSL and firewall rules
8. ✅ **Monitoring and metrics** collection

## Quick Deployment Checklist

- [ ] Create Azure MySQL Flexible Server
- [ ] Configure firewall rules
- [ ] Create application database
- [ ] Set App Service environment variables
- [ ] Deploy updated FastAPI application
- [ ] Test database connectivity
- [ ] Monitor logs and metrics
- [ ] Verify API endpoints work with database

Your application is now ready for production with persistent data storage in Azure MySQL!