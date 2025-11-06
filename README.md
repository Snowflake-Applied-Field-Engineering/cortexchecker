# Snowflake Intelligence & Cortex Access Checker

Intelligent permission management for Snowflake Cortex AI Agents.

## Overview

A Streamlit application that helps you manage permissions for Snowflake Cortex AI by:
- **Analyzing roles** for Cortex Analyst readiness
- **Generating SQL scripts** for Cortex Agent permissions
- **Validating compatibility** between roles and agents

## Quick Start

### 1. Setup Snowflake

Run this SQL in a Snowflake worksheet:

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

### 2. Deploy Streamlit App

1. In Snowsight, go to **Projects → Streamlit**
2. Click **+ Streamlit App**
3. Configure:
   - **Name:** `Cortex_Access_Checker`
   - **Location:** `CORTEX_TOOLS.APPS`
   - **Warehouse:** `COMPUTE_WH`
   - **Role:** `CORTEX_ADMIN`
4. Copy and paste the contents of `cortex_tool.py`
5. Click **Run**

## Features

### Role Analysis
- Check if a role is ready for Cortex Analyst
- View all grants and permissions
- Generate SQL to fix missing permissions
- Export results as CSV/JSON

### Agent Permission Generator
- Automatically discover agents in your account
- Parse agent tools and dependencies
- Extract semantic views and base tables
- Generate least-privilege SQL scripts
- Support for semantic model files in stages

### Combined Analysis
- Verify role-agent compatibility
- Identify missing permissions
- Generate remediation SQL

## How It Works

The tool uses SQL-based parsing to:
1. **Describe agents** using `DESCRIBE AGENT`
2. **Parse tool specifications** with `LATERAL FLATTEN` and `PARSE_JSON`
3. **Extract semantic views** and read YAML definitions
4. **Discover base tables** from semantic model files
5. **Generate comprehensive SQL** with all required grants

## Screenshot

*Add your screenshot here*

## Troubleshooting

**"Could not query roles"**
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

**"No agents found"**
- Use manual entry mode to specify agent details
- Verify agents exist: `SHOW AGENTS IN ACCOUNT;`

**"Could not read YAML from stage"**
- Ensure the app role has READ access to the stage
- Verify the semantic model file path is correct

## Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup instructions
- [QUICKSTART.md](QUICKSTART.md) - Quick start guide
- [PERMISSIONS_SETUP.md](PERMISSIONS_SETUP.md) - Permissions reference

## License

MIT License - See [LICENSE](LICENSE) file for details

## Credits

Inspired by the [CART (Cortex Agent Role Tool)](https://github.com/sfc-gh-amelatti/cortex_agents_role_tool_CART) project.
