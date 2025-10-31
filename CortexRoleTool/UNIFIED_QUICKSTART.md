# Cortex Unified Tool - Quick Start Guide

Get up and running with the Cortex Unified Tool in 5 minutes!

## What You'll Need

- ✅ Snowflake account with Cortex AI enabled
- ✅ Access to Snowsight (Snowflake UI)
- ✅ ACCOUNTADMIN or similar privileges (for initial setup)

## Step 1: Setup (2 minutes)

### Create Database and Role

Copy and paste this SQL into a Snowflake worksheet:

```sql
-- Create database and schema for the app
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- Create dedicated role for the app
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- Grant necessary privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Grant role to your user (replace with your username)
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;

-- Verify setup
USE ROLE CORTEX_ADMIN;
SELECT 'Setup complete!' as status;
```

## Step 2: Deploy App (2 minutes)

### Option A: Upload via Snowsight (Recommended)

1. Navigate to **Snowsight** → **Streamlit**
2. Click **+ Streamlit App**
3. Name it: `Cortex_Unified_Tool`
4. Select:
   - **Location:** `CORTEX_TOOLS.APPS`
   - **Warehouse:** `COMPUTE_WH`
   - **App role:** `CORTEX_ADMIN`
5. Delete the default code
6. Copy and paste the contents of `cortex_unified_tool.py`
7. Click **Run**

### Option B: Use Existing Role Checker

If you already have the role checker deployed:
- You can keep using `cortexrbac` for role-only analysis
- Deploy `cortex_unified_tool.py` as a separate app for full functionality

## Step 3: Start Using (1 minute)

### Quick Test - Check a Role

1. In the sidebar, select **"Role Permission Checker"**
2. Search for a role (e.g., type "PUBLIC")
3. Select the role
4. View the readiness score and analysis

**Expected Result:** You should see:
- Cortex Access: Yes/No
- Warehouse count
- Database count
- Readiness score (0-4)

### Quick Test - Analyze an Agent (if you have agents)

1. In the sidebar, select **"Agent Permission Generator"**
2. Choose **"Select from list"**
3. Select an agent (if available)
4. Click **"Analyze Agent"**
5. Review the generated SQL

**Expected Result:** You should see:
- Agent details
- Tool breakdown
- Generated SQL script

## Common First-Time Issues

### ❌ "Could not query roles from ACCOUNT_USAGE"

**Fix:**
```sql
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

### ❌ "No agents found"

This is normal if you haven't created any Cortex Agents yet. You can:
- Use the "Enter manually" option to test with a hypothetical agent
- Focus on the Role Permission Checker mode
- Create a test agent first

### ❌ "Application must be run as a Streamlit in Snowflake app"

**Fix:** Make sure you're running the app in Snowsight, not locally.

## What to Do Next

### For Role Analysis

1. **Audit Existing Roles**
   - Use bulk analysis with pattern `*ANALYST*`
   - Identify roles that need Cortex access
   - Download remediation SQL

2. **Compare Roles**
   - Select multiple roles
   - View comparison table
   - Identify best practices

3. **Fix Issues**
   - Download remediation SQL
   - Review in a new worksheet
   - Execute to grant permissions
   - Re-analyze to verify

### For Agent Permissions

1. **Analyze Existing Agents**
   - Select each agent
   - Review tool dependencies
   - Generate SQL for each

2. **Create Least-Privilege Roles**
   - Download generated SQL
   - Customize role names
   - Execute in Snowflake
   - Test agent access

3. **Document Permissions**
   - Export analysis as CSV
   - Keep records of generated SQL
   - Track which roles use which agents

## Example Workflows

### Workflow 1: Onboard New User to Cortex Analyst

```
1. Create new role: CREATE ROLE DATA_ANALYST_CORTEX;
2. Run Unified Tool → Role Permission Checker
3. Select DATA_ANALYST_CORTEX
4. View missing permissions
5. Download remediation SQL
6. Execute SQL to grant permissions
7. Grant role to user: GRANT ROLE DATA_ANALYST_CORTEX TO USER john_doe;
8. Verify with Combined Analysis
```

### Workflow 2: Create Role for New Agent

```
1. Create Cortex Agent in Snowflake
2. Run Unified Tool → Agent Permission Generator
3. Select the new agent
4. Review semantic views and tables
5. Customize role name (e.g., SALES_AGENT_USER)
6. Download SQL script
7. Execute SQL to create role and grants
8. Test: GRANT ROLE SALES_AGENT_USER TO USER test_user;
```

### Workflow 3: Audit All Analyst Roles

```
1. Run Unified Tool → Role Permission Checker
2. Click "Bulk Analysis"
3. Enter pattern: *ANALYST*
4. Review comparison table
5. Identify roles missing Cortex access
6. Download remediation SQL for each
7. Execute in batch
8. Export comparison report as CSV
```

## Tips for Success

### 🎯 Best Practices

1. **Start Small** - Test with one role or agent first
2. **Review SQL** - Always review generated SQL before executing
3. **Use Non-Prod** - Test in development environment first
4. **Document Changes** - Keep track of what you grant and why
5. **Regular Audits** - Re-run analysis quarterly

### 🚀 Power User Tips

1. **Use Patterns** - Bulk analyze with wildcards: `*_PROD_*`, `DEV_*`, etc.
2. **Export Everything** - Download CSV reports for documentation
3. **Compare Roles** - Use multi-select to find best-configured roles
4. **Cache Refresh** - Use "Refresh Data" button if roles/agents change
5. **Combine Modes** - Use Combined Analysis to verify role-agent compatibility

### 📊 Monitoring

Set up regular checks:
- **Weekly:** Run bulk analysis on production roles
- **Monthly:** Audit all agent permissions
- **Quarterly:** Full permission review with exports

## Getting Help

### Troubleshooting

1. **Check Permissions** - Ensure CORTEX_ADMIN has all required grants
2. **Verify Warehouse** - Make sure warehouse is running
3. **Review Errors** - Read error messages carefully
4. **Check Documentation** - See UNIFIED_TOOL_README.md for details

### Resources

- **[UNIFIED_TOOL_README.md](UNIFIED_TOOL_README.md)** - Complete documentation
- **[PERMISSIONS_SETUP.md](PERMISSIONS_SETUP.md)** - Detailed permission guide
- **[README.md](../README.md)** - Main project README

### Support

- Create an issue in the GitHub repository
- Contact Snowflake Applied Field Engineering team
- Check Snowflake documentation for Cortex AI

## Next Steps

Now that you're up and running:

1. ✅ Explore all three modes
2. ✅ Analyze your existing roles
3. ✅ Generate SQL for your agents
4. ✅ Set up regular audits
5. ✅ Share with your team

**Happy Cortex AI permission management!** 🎉

---

**Need more details?** Check out the [full documentation](UNIFIED_TOOL_README.md).

