# Quick Start Guide - Cortex RBAC Tool

## 🚀 Get Started in 5 Minutes

### Step 1: Setup Snowflake Environment

```sql
-- Run these commands in a Snowflake worksheet as ACCOUNTADMIN

-- 1. Create database for the app
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- 2. Create a stage for the Streamlit app
CREATE STAGE IF NOT EXISTS CORTEX_TOOLS.APPS.STREAMLIT_STAGE;

-- 3. Create a role for the app owner (recommended)
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- 4. Grant necessary privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- 5. Grant role to your user
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;
```

### Step 2: Upload the Application

**Option A: Using Snowsight UI**
1. Navigate to Snowsight → Projects → Streamlit
2. Click "+ Streamlit App"
3. Name: `Cortex_Role_Checker`
4. Database: `CORTEX_TOOLS`
5. Schema: `APPS`
6. Warehouse: `COMPUTE_WH`
7. App role: `CORTEX_ADMIN`
8. Copy and paste the contents of `cortexrbac` file
9. Click "Create"

**Option B: Using SnowSQL**
```bash
# Upload file to stage
snowsql -q "PUT file:///path/to/cortexrbac @CORTEX_TOOLS.APPS.STREAMLIT_STAGE AUTO_COMPRESS=FALSE OVERWRITE=TRUE"

# Create Streamlit app
snowsql -q "
CREATE STREAMLIT CORTEX_TOOLS.APPS.ROLE_CHECKER
  ROOT_LOCATION = '@CORTEX_TOOLS.APPS.STREAMLIT_STAGE'
  MAIN_FILE = 'cortexrbac'
  QUERY_WAREHOUSE = 'COMPUTE_WH'
  TITLE = 'Cortex Analyst Role Access Checker'
"
```

### Step 3: Run the Application

1. Navigate to Snowsight → Projects → Streamlit
2. Click on "Cortex_Role_Checker"
3. Wait for the app to load (first load may take 30 seconds)
4. Select a role from the sidebar
5. Review the analysis!

## 📊 Understanding the Results

### Readiness Score Interpretation

```
🎉 FULLY READY (4/4)
├─ ✅ Has Cortex database role
├─ ✅ Has warehouse access
├─ ✅ Has database/schema access
└─ ✅ Has table SELECT privileges
→ Role is ready to use Cortex Analyst!

⚠️ MOSTLY READY (3/4)
├─ ✅ Has Cortex database role
├─ ✅ Has warehouse access
├─ ✅ Has database/schema access
└─ ❌ Missing table SELECT privileges
→ Grant SELECT on specific tables

⚠️ PARTIALLY READY (2/4)
├─ ✅ Has Cortex database role
├─ ❌ No warehouse access
├─ ✅ Has database/schema access
└─ ❌ Missing table SELECT privileges
→ Multiple permissions needed

❌ NOT READY (0-1/4)
├─ ❌ Missing Cortex database role
├─ ❌ No warehouse access
├─ ❌ No database/schema access
└─ ❌ Missing table SELECT privileges
→ Role needs significant permissions
```

## 🔧 Common Use Cases

### Use Case 1: Check if a Role Can Use Cortex Analyst

```
1. Select the role from sidebar
2. Look at "Cortex Analyst Readiness Summary"
3. If ✅ ACCESS GRANTED → Role is ready
4. If ❌ ACCESS MISSING → Grant the Cortex role
```

**Fix Missing Cortex Role:**
```sql
-- Grant Cortex User role
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <ROLE_NAME>;

-- OR grant Cortex Analyst User role
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_ANALYST_USER TO ROLE <ROLE_NAME>;
```

### Use Case 2: Identify Missing Permissions

```
1. Select the role
2. Scroll to "Detailed Access Analysis"
3. Note any ⚠️ warnings
4. Use the SQL commands below to fix
```

**Fix Missing Warehouse:**
```sql
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE <ROLE_NAME>;
```

**Fix Missing Database/Schema:**
```sql
GRANT USAGE ON DATABASE <DB_NAME> TO ROLE <ROLE_NAME>;
GRANT USAGE ON SCHEMA <DB_NAME>.<SCHEMA_NAME> TO ROLE <ROLE_NAME>;
```

**Fix Missing Table Access:**
```sql
GRANT SELECT ON TABLE <DB_NAME>.<SCHEMA_NAME>.<TABLE_NAME> TO ROLE <ROLE_NAME>;

-- Or grant on all tables in schema
GRANT SELECT ON ALL TABLES IN SCHEMA <DB_NAME>.<SCHEMA_NAME> TO ROLE <ROLE_NAME>;
```

### Use Case 3: Compare Multiple Roles

```
1. Select 2+ roles from sidebar
2. Click through tabs to compare
3. Identify which role has better permissions
4. Use as template for other roles
```

### Use Case 4: Export for Reporting

```
1. Select a role
2. Scroll to "All Grants Detail"
3. Apply filters if needed
4. Click "📥 Download Grants as CSV"
5. Share with stakeholders
```

## ⚠️ Troubleshooting

### Problem: "No roles found to analyze"

**Cause**: App owner role lacks permissions

**Fix**:
```sql
-- Grant necessary privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

### Problem: "Could not retrieve grants for role"

**Cause**: App owner cannot view grants for selected role

**Fix**:
```sql
-- Grant MANAGE GRANTS privilege
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

### Problem: App shows "Failed to query ACCOUNT_USAGE"

**Cause**: Normal - app is using fallback method

**Impact**: Still works, but may have limited visibility

**Optional Fix**:
```sql
-- Grant access to ACCOUNT_USAGE (requires ACCOUNTADMIN)
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

### Problem: Empty grants table

**Cause**: Role genuinely has no grants

**Fix**: Grant necessary permissions to the role

## 📝 Best Practices

### For Administrators

1. **Create a dedicated app owner role** (don't use ACCOUNTADMIN)
2. **Test with a known role first** to verify functionality
3. **Document your app owner role** and its privileges
4. **Export results before making changes** for audit trail
5. **Use the readiness score** to prioritize permission grants

### For Security

1. **Review role permissions regularly** using this tool
2. **Follow principle of least privilege** - only grant what's needed
3. **Document why roles have Cortex access** in your security policies
4. **Use role hierarchy** to simplify permission management
5. **Audit exported CSV files** for compliance reporting

## 🎯 Next Steps

After getting started:

1. ✅ Test with your own roles
2. ✅ Identify roles that need Cortex access
3. ✅ Grant necessary permissions
4. ✅ Export results for documentation
5. ✅ Share with your team

## 📚 Additional Resources

- [Full README](README.md) - Comprehensive documentation
- [Improvements](IMPROVEMENTS.md) - What was enhanced
- [Snowflake Cortex Docs](https://docs.snowflake.com/en/user-guide/snowflake-cortex) - Official documentation
- [Cortex Analyst Guide](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) - Analyst-specific docs

## 💡 Pro Tips

1. **Bookmark the app** in Snowsight for quick access
2. **Create a dashboard** with multiple roles pre-selected
3. **Schedule regular reviews** of role permissions
4. **Use CSV exports** for change tracking over time
5. **Share the app link** with other administrators

---

**Need Help?** Check the [README](README.md) for detailed troubleshooting or review the [Improvements](IMPROVEMENTS.md) document to understand all features.

