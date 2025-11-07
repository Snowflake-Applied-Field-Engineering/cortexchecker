# Setup Guide

Complete setup instructions for Snowflake Intelligence & Cortex Access Checker.

## Prerequisites

- Snowflake account with Cortex AI enabled
- Access to Snowsight (Snowflake web UI)
- ACCOUNTADMIN or SECURITYADMIN privileges

## Installation

### 1. Create Database and Schema

```sql
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;
```

### 2. Create App Role

```sql
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;
```

### 3. Grant Privileges

```sql
-- Required: Access to account metadata
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;

-- Required: App location
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;

-- Required: Compute
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Optional: For executing SQL directly
GRANT CREATE ROLE ON ACCOUNT TO ROLE CORTEX_ADMIN;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

### 4. Grant Role to Users

```sql
GRANT ROLE CORTEX_ADMIN TO USER IDENTIFIER(CURRENT_USER());
```

## Deploy Streamlit App

### Via Snowsight

1. Navigate to **Projects → Streamlit**
2. Click **+ Streamlit App**
3. Configure:
   - **App name:** `Cortex_Access_Checker`
   - **Location:** `CORTEX_TOOLS.APPS`
   - **Warehouse:** `COMPUTE_WH`
   - **App role:** `CORTEX_ADMIN`
4. Delete default code
5. Copy contents of `cortex_tool.py`
6. Paste into editor
7. Click **Run**

## Verify Installation

1. App should load without errors
2. Select "Role Permission Checker"
3. Search for "PUBLIC" role
4. You should see role analysis

## Troubleshooting

### "Could not query roles from ACCOUNT_USAGE"

**Cause:** Missing IMPORTED PRIVILEGES

**Fix:**
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

### "Could not retrieve grants for role"

**Cause:** Missing MANAGE GRANTS privilege

**Fix:**
```sql
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

### "No agents found"

**Cause:** No agents exist or role lacks access

**Solutions:**
- Verify agents exist: `SHOW AGENTS IN ACCOUNT;`
- Use manual entry mode
- Grant access to agent databases

### "Execute SQL" button fails

**Cause:** Insufficient privileges to create roles/grants

**Fix:**
```sql
GRANT CREATE ROLE ON ACCOUNT TO ROLE CORTEX_ADMIN;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

## Permissions Reference

### Minimum Required
- `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE`
- `USAGE ON DATABASE CORTEX_TOOLS`
- `ALL ON SCHEMA CORTEX_TOOLS.APPS`
- `USAGE ON WAREHOUSE COMPUTE_WH`

### Recommended for Full Functionality
- `CREATE ROLE ON ACCOUNT`
- `MANAGE GRANTS ON ACCOUNT`

### For Agent Analysis
- `USAGE` on agent databases
- `USAGE` on agent schemas
- `DESCRIBE` on agents

## Upgrading

To upgrade to the latest version:

1. Pull latest code from GitHub
2. In Streamlit app, delete all code
3. Paste new `cortex_tool.py` contents
4. Click **Run**

No database changes required.

## Uninstalling

To remove the app:

```sql
-- Drop Streamlit app (via Snowsight UI or SQL)
DROP STREAMLIT CORTEX_TOOLS.APPS.CORTEX_ACCESS_CHECKER;

-- Optional: Remove database
DROP DATABASE CORTEX_TOOLS;

-- Optional: Remove role
DROP ROLE CORTEX_ADMIN;
```

## Next Steps

See [QUICKSTART.md](QUICKSTART.md) for usage examples.
