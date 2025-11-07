# Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Setup Snowflake (2 minutes)

Copy and paste this SQL into a Snowflake worksheet:

```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- Create app role
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- Grant privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Grant role to your user
GRANT ROLE CORTEX_ADMIN TO USER IDENTIFIER(CURRENT_USER());
```

## Step 2: Deploy App (2 minutes)

1. In Snowsight, go to **Projects → Streamlit**
2. Click **+ Streamlit App**
3. Configure:
   - **Name:** `Cortex_Access_Checker`
   - **Location:** `CORTEX_TOOLS.APPS`
   - **Warehouse:** `COMPUTE_WH`
   - **Role:** `CORTEX_ADMIN`
4. Copy and paste the contents of `cortex_tool.py`
5. Click **Run**

## Step 3: Start Using (1 minute)

### Check a Role
1. Select **"Role Permission Checker"** from sidebar
2. Search for a role (e.g., "PUBLIC")
3. View readiness score and permissions

### Analyze an Agent
1. Select **"Agent Permission Generator"** from sidebar
2. Choose an agent from the list
3. Click **"Generate Permission Script"**
4. Review the SQL and click **"Execute SQL"** or download

## Common Issues

**"Could not query roles"**
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

**"No agents found"**
- Normal if you haven't created any agents yet
- Use manual entry mode to test

## Next Steps

- Analyze your existing roles for Cortex readiness
- Generate SQL for your agents
- Use Execute SQL button for quick permission fixes

For more details, see [README.md](README.md)
