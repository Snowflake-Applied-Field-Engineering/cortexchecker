# Cortex Tool - Snowflake Cortex AI Permission Management

A Streamlit application for managing Snowflake Cortex AI permissions. Analyze role permissions for Cortex Analyst and generate least-privilege SQL for Cortex Agents.

## Overview

Cortex Tool combines two utilities:
- **Role Permission Checker** - Analyze roles for Cortex Analyst readiness
- **Agent Permission Generator** - Generate SQL for Cortex Agent permissions

## Quick Setup
<img width="1606" height="1107" alt="image" src="https://github.com/user-attachments/assets/08995955-062b-43fb-918e-b697a15f18f4" />
<img width="1666" height="889" alt="image" src="https://github.com/user-attachments/assets/b333e6bd-2d60-4728-a45c-d8031fa89d3f" />
<img width="1624" height="1072" alt="image" src="https://github.com/user-attachments/assets/46441200-eef7-4769-ac26-a0771a84002e" />



### Prerequisites

- Snowflake account with Cortex AI enabled
- Access to Snowsight (Snowflake web UI)
- ACCOUNTADMIN or equivalent privileges

### Step 1: Setup Snowflake Environment

Run this SQL in a Snowflake worksheet:

```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- Create app owner role
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- Grant necessary privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Grant role to your user (replace with your username)
GRANT ROLE CORTEX_ADMIN TO USER IDENTIFIER(CURRENT_USER());
```

### Step 2: Deploy Streamlit App

1. **Navigate to Streamlit**
   - Log into Snowsight
   - Go to Projects → Streamlit
   - Click "+ Streamlit App"

2. **Configure App**
   - **App name:** `Cortex_Tool`
   - **Location:** `CORTEX_TOOLS.APPS`
   - **Warehouse:** `COMPUTE_WH`
   - **App role:** `CORTEX_ADMIN`

3. **Upload Code**
   - Delete the default code
   - Copy the contents of `cortex_tool.py`
   - Paste into the editor
   - Click "Run"

### Step 3: Verify Setup

Once the app loads:
1. Select "Role Permission Checker" from the sidebar
2. Search for a role (e.g., "PUBLIC")
3. View the analysis results

## Features

### Mode 1: Role Permission Checker

Analyze Snowflake roles for Cortex Analyst readiness:
- View all grants for a role
- Check Cortex database role assignment
- Verify warehouse, database, and table access
- Generate remediation SQL for missing permissions
- Export grants as CSV, JSON, or HTML

### Mode 2: Agent Permission Generator

Generate least-privilege SQL for Cortex Agents:
- Discover agents automatically or enter manually
- Analyze agent tools and dependencies
- Extract semantic views and base tables
- Generate complete SQL script with all required grants
- Download ready-to-execute SQL

### Mode 3: Combined Analysis

Check if a specific role can use a specific agent:
- Select role and agent
- Verify compatibility
- Generate fix SQL for missing permissions

## Usage Examples

### Check Role Readiness

```
1. Select "Role Permission Checker"
2. Search for "DATA_ANALYST"
3. View readiness score (0-4 points)
4. Download remediation SQL if needed
5. Execute SQL in Snowflake worksheet
```

### Generate Agent Permissions

```
1. Select "Agent Permission Generator"
2. Choose agent from list or enter manually
3. Click "Analyze Agent"
4. Review tools and dependencies
5. Download generated SQL
6. Execute in Snowflake worksheet
```

### Verify Role-Agent Compatibility

```
1. Select "Combined Analysis"
2. Choose role and agent
3. Click "Analyze Compatibility"
4. Review results
5. Download fix SQL if needed
```

## Readiness Scoring

Roles are scored on 4 criteria:

| Score | Status | Meaning |
|-------|--------|---------|
| 4/4 | FULLY READY | All permissions present |
| 3/4 | MOSTLY READY | One permission missing |
| 2/4 | PARTIALLY READY | Two permissions missing |
| 0-1/4 | NOT READY | Multiple permissions missing |

**Required for Cortex Analyst:**
1. Cortex database role (CORTEX_USER or CORTEX_ANALYST_USER)
2. USAGE on at least one warehouse
3. USAGE on database(s) and schema(s)
4. SELECT on table(s)/view(s)

## Troubleshooting

### "Could not query roles from ACCOUNT_USAGE"

**Solution:**
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

### "Could not retrieve grants for role"

**Solution:**
```sql
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

### "No agents found"

**Causes:**
- No agents exist in your account
- App owner role lacks access to agents

**Solution:**
1. Verify agents exist: `SHOW AGENTS IN ACCOUNT;`
2. Use manual entry mode to specify agent details

### "App won't load"

**Checks:**
- Warehouse is running
- Role has necessary privileges
- No syntax errors in code

## Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick reference
- **[PERMISSIONS_SETUP.md](PERMISSIONS_SETUP.md)** - Permissions guide
- **[TEST_PLAN.md](TEST_PLAN.md)** - Testing procedures

## Architecture

```
Cortex Tool
├── Role Permission Checker
│   ├── Query ACCOUNT_USAGE for grants
│   ├── Analyze Cortex readiness
│   └── Generate remediation SQL
│
├── Agent Permission Generator
│   ├── Discover/describe agents
│   ├── Parse semantic views
│   └── Generate permission SQL
│
└── Combined Analysis
    ├── Check role-agent compatibility
    └── Generate fix SQL
```

## Required Privileges

**For App Owner Role (CORTEX_ADMIN):**
- IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE
- USAGE ON DATABASE CORTEX_TOOLS
- ALL ON SCHEMA CORTEX_TOOLS.APPS
- USAGE ON WAREHOUSE COMPUTE_WH

**For App Users:**
- USAGE ON DATABASE CORTEX_TOOLS
- USAGE ON SCHEMA CORTEX_TOOLS.APPS
- USAGE ON STREAMLIT CORTEX_TOOLS.APPS.CORTEX_TOOL

## Common SQL Commands

### Grant Cortex Access
```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <ROLE_NAME>;
```

### Grant Warehouse
```sql
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE <ROLE_NAME>;
```

### Grant Database/Schema
```sql
GRANT USAGE ON DATABASE <DB_NAME> TO ROLE <ROLE_NAME>;
GRANT USAGE ON SCHEMA <DB_NAME>.<SCHEMA_NAME> TO ROLE <ROLE_NAME>;
```

### Grant Table Access
```sql
GRANT SELECT ON TABLE <DB>.<SCHEMA>.<TABLE> TO ROLE <ROLE_NAME>;
-- Or all tables in schema:
GRANT SELECT ON ALL TABLES IN SCHEMA <DB>.<SCHEMA> TO ROLE <ROLE_NAME>;
```

### Grant Agent Access
```sql
GRANT USAGE ON AGENT <DB>.<SCHEMA>.<AGENT> TO ROLE <ROLE_NAME>;
```

## Version History

- **v3.0.0** (2025-10-31) - Combined Tool Release
  - Integrated CART (Cortex Agent Role Tool) functionality
  - Added Agent Permission Generator mode
  - Added Combined Analysis mode
  - Enhanced SQL generation for both roles and agents
  - Three operational modes with unified navigation

- **v2.1.0** (2025-10-28) - Major feature release
  - Added search and bulk analysis
  - Auto-generated remediation SQL
  - Smart recommendations
  - Multi-format export
  - Role comparison

- **v2.0.0** (2025-10-27) - Complete overhaul
  - Fixed critical bugs
  - Enhanced UI/UX
  - Comprehensive documentation

## License

MIT License - See LICENSE file for details

## Support

- **Repository:** https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker
- **Issues:** https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker/issues

## Credits

Built with:
- Streamlit - Web framework
- Snowflake Snowpark - Database connectivity
- Pandas - Data manipulation

Combines features from:
- CortexChecker - Role permission analysis
- CART - Cortex Agent Role Tool
