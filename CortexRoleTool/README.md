# Cortex Analyst Role Access Checker

A Streamlit application that analyzes Snowflake roles to assess their readiness for using **Snowflake Cortex Analyst**.

## Overview

This tool helps administrators quickly evaluate whether a role has the necessary permissions to use Cortex Analyst features. It provides:

- ✅ **Cortex Role Verification** - Checks for CORTEX_USER or CORTEX_ANALYST_USER roles
- 🏢 **Warehouse Access Analysis** - Verifies USAGE privileges on warehouses
- 📊 **Database & Schema Access** - Reviews database and schema permissions
- 📑 **Table/View Access** - Checks SELECT privileges on data objects
- 📈 **Readiness Score** - Overall assessment with actionable recommendations
- 📥 **Export Capabilities** - Download grant details as CSV

## Prerequisites

### Snowflake Requirements
- Snowflake account with Cortex AI enabled
- Streamlit in Snowflake (SiS) environment
- App owner role must have one of:
  - `MANAGE GRANTS` privilege
  - `ACCOUNTADMIN` role
  - Access to `SNOWFLAKE.ACCOUNT_USAGE` schema

### Python Requirements
```
streamlit==1.29.0
snowflake-snowpark-python==1.11.1
pandas==2.1.4
```

## Installation

### Deploy to Snowflake (Recommended)

1. **Create a Streamlit app in Snowsight:**
```sql
-- Create database and schema for the app
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- Create the Streamlit app
CREATE STREAMLIT CORTEX_TOOLS.APPS.ROLE_CHECKER
  ROOT_LOCATION = '@CORTEX_TOOLS.APPS.STREAMLIT_STAGE'
  MAIN_FILE = 'cortexrbac'
  QUERY_WAREHOUSE = 'COMPUTE_WH';
```

2. **Upload the file:**
   - Navigate to Snowsight → Streamlit
   - Upload `cortexrbac` file
   - Run the app

### Local Testing (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SNOWFLAKE_ACCOUNT="your_account"
export SNOWFLAKE_USER="your_user"
export SNOWFLAKE_PASSWORD="your_password"

# Run locally (limited functionality)
streamlit run cortexrbac
```

## Usage

### Basic Workflow

1. **Select Role(s)**
   - Use the sidebar to select one or more roles to analyze
   - Multiple roles can be compared side-by-side

2. **Review Readiness Summary**
   - View the Cortex Analyst access status
   - Check the overall readiness score (0-4)

3. **Analyze Details**
   - Warehouse access
   - Database and schema permissions
   - Table/view SELECT privileges

4. **Export Results**
   - Download grant details as CSV for reporting
   - Share with stakeholders

### Understanding the Readiness Score

The app calculates a readiness score based on four criteria:

| Score | Status | Description |
|-------|--------|-------------|
| 4/4 | 🎉 FULLY READY | All requirements met |
| 3/4 | ⚠️ MOSTLY READY | Minor issues to address |
| 2/4 | ⚠️ PARTIALLY READY | Several missing permissions |
| 0-1/4 | ❌ NOT READY | Major permissions missing |

### Required Permissions for Cortex Analyst

For a role to successfully use Cortex Analyst, it needs:

1. **Cortex Database Role** (Required)
   - `SNOWFLAKE.CORTEX_USER` OR
   - `SNOWFLAKE.CORTEX_ANALYST_USER`

2. **Compute Resources** (Required)
   - `USAGE` on at least one warehouse

3. **Data Access** (Required)
   - `USAGE` on database(s)
   - `USAGE` on schema(s)
   - `SELECT` on table(s)/view(s)

## Features

### 🔍 Intelligent Grant Detection

The app uses multiple strategies to fetch role grants:

1. **Primary Method**: Queries `SNOWFLAKE.ACCOUNT_USAGE` views
   - Most comprehensive
   - Requires elevated privileges

2. **Fallback Method**: Uses `SHOW GRANTS TO ROLE`
   - Works with standard privileges
   - May have limited visibility

### 📊 Visual Analysis

- **Color-coded status indicators** for quick assessment
- **Progress bars** showing readiness percentage
- **Expandable sections** for detailed information
- **Filterable grant tables** for easy navigation

### 🎯 Multi-Role Comparison

- Select multiple roles to compare
- Tabbed interface for easy switching
- Consistent analysis across all roles

### 📥 Export & Reporting

- Download grant details as CSV
- Unique filename per role
- All columns included for comprehensive reporting

## Troubleshooting

### "Could not query roles from ACCOUNT_USAGE"

**Cause**: App owner lacks access to `SNOWFLAKE.ACCOUNT_USAGE`

**Solution**:
```sql
-- Grant IMPORTED PRIVILEGES to app owner role
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <APP_OWNER_ROLE>;
```

### "Could not retrieve grants for role"

**Cause**: App owner cannot view grants for the selected role

**Solution**:
```sql
-- Grant MANAGE GRANTS privilege
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE <APP_OWNER_ROLE>;
```

### "No roles found to analyze"

**Cause**: App owner has no visibility to roles

**Solution**:
- Ensure app owner has appropriate privileges
- Try running as ACCOUNTADMIN for testing

### Empty or Missing Data

**Cause**: Role may not have any grants, or fallback methods are limited

**Solution**:
- Verify the role exists and has grants
- Check app owner privileges
- Review Snowflake query history for errors

## Best Practices

### For App Owners

1. **Use a service role** with appropriate privileges:
```sql
CREATE ROLE CORTEX_ADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

2. **Grant minimal necessary privileges** - don't use ACCOUNTADMIN

3. **Document the app owner role** in your security documentation

### For Users

1. **Start with one role** to understand the interface
2. **Use filters** on the grants table to find specific permissions
3. **Export results** before making permission changes
4. **Compare roles** to understand permission differences

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI                       │
├─────────────────────────────────────────────────────┤
│  Role Selection → Grant Fetching → Analysis         │
│                                                      │
│  ┌────────────────┐    ┌──────────────────┐        │
│  │ ACCOUNT_USAGE  │───▶│ Pandas DataFrame │        │
│  │    (Primary)   │    └──────────────────┘        │
│  └────────────────┘              │                  │
│         │ Fallback               ▼                  │
│         ▼                  ┌──────────┐             │
│  ┌────────────────┐        │ Analysis │             │
│  │  SHOW GRANTS   │───────▶│ Functions│             │
│  │  (Secondary)   │        └──────────┘             │
│  └────────────────┘              │                  │
│                                  ▼                  │
│                        ┌──────────────────┐         │
│                        │ Readiness Score  │         │
│                        │ Visualizations   │         │
│                        │ Export CSV       │         │
│                        └──────────────────┘         │
└─────────────────────────────────────────────────────┘
```

## Contributing

Suggestions and improvements are welcome! Key areas for enhancement:

- [ ] Role hierarchy traversal
- [ ] Historical grant analysis
- [ ] Automated remediation suggestions
- [ ] Integration with Snowflake governance tools
- [ ] Batch role analysis with summary report

## License

MIT License - See main repository LICENSE file

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review Snowflake documentation on Cortex Analyst
3. Verify app owner privileges
4. Check Snowflake query history for detailed errors

---

**Note**: This tool provides a point-in-time analysis. Role permissions may change. Always verify current permissions before granting Cortex Analyst access to users.

