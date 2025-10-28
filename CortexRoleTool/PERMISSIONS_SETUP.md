# Permissions Setup Guide

## 🔐 Required Permissions for the App Owner Role

The Cortex RBAC Tool needs specific permissions to query role grants in Snowflake. This guide will help you set up the correct permissions.

---

## ⚠️ Common Error: Cannot Query ACCOUNT_USAGE

### Error Message You See:
```
❌ Failed to query ACCOUNT_USAGE views for [ROLE_NAME]
SQL compilation error: error line 4 at position 16 invalid identifier 'GRANTED_ROLE'
```

### Root Cause:
The app owner role lacks permissions to query `SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES`.

---

## ✅ Solution: Grant Necessary Permissions

### Option 1: Grant IMPORTED PRIVILEGES (Recommended)

This is the **recommended approach** as it provides read-only access to the SNOWFLAKE database.

```sql
-- Run as ACCOUNTADMIN or a role with MANAGE GRANTS privilege

-- 1. Identify your app owner role (the role that owns the Streamlit app)
-- Usually this is the role you used when creating the Streamlit app

-- 2. Grant IMPORTED PRIVILEGES on SNOWFLAKE database
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <YOUR_APP_OWNER_ROLE>;

-- Example:
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

**What this grants:**
- ✅ Read access to `SNOWFLAKE.ACCOUNT_USAGE` views
- ✅ Read access to `SNOWFLAKE.INFORMATION_SCHEMA` views
- ✅ No write or modification permissions
- ✅ Minimal security risk

---

### Option 2: Grant MANAGE GRANTS (More Permissive)

This grants broader permissions and should only be used if Option 1 doesn't work.

```sql
-- Run as ACCOUNTADMIN

GRANT MANAGE GRANTS ON ACCOUNT TO ROLE <YOUR_APP_OWNER_ROLE>;

-- Example:
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;
```

**What this grants:**
- ✅ Ability to view all grants in the account
- ⚠️ Ability to grant and revoke privileges (use with caution)
- ⚠️ Higher security risk

---

## 🎯 Complete Setup Script

Here's a complete script to set up a dedicated role for the Cortex RBAC Tool:

```sql
-- ============================================================================
-- Cortex RBAC Tool - Complete Setup Script
-- Run as ACCOUNTADMIN
-- ============================================================================

-- 1. Create a dedicated role for the app owner
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN
    COMMENT = 'Role for Cortex RBAC Tool app owner';

-- 2. Grant access to SNOWFLAKE database (for querying ACCOUNT_USAGE)
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;

-- 3. Create database and schema for the app
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS
    COMMENT = 'Database for Cortex administration tools';

CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS
    COMMENT = 'Schema for Streamlit apps';

-- 4. Grant permissions on the app database
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;

-- 5. Grant warehouse usage (needed to run queries)
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;
-- Adjust warehouse name as needed

-- 6. Grant the role to your user
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;
-- Replace <YOUR_USERNAME> with your actual username

-- 7. Verify the grants
SHOW GRANTS TO ROLE CORTEX_ADMIN;

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Test if you can query ACCOUNT_USAGE
USE ROLE CORTEX_ADMIN;
SELECT COUNT(*) AS role_count 
FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES 
WHERE DELETED_ON IS NULL;

-- If this returns a number, you're all set!
-- If it errors, you may need ACCOUNTADMIN to grant IMPORTED PRIVILEGES
```

---

## 🔍 Verify Your Setup

### Step 1: Check Current Role Grants

```sql
-- See what privileges your app owner role has
SHOW GRANTS TO ROLE <YOUR_APP_OWNER_ROLE>;
```

Look for one of these in the output:
- `IMPORTED PRIVILEGES | SNOWFLAKE | DATABASE`
- `MANAGE GRANTS | ACCOUNT`

### Step 2: Test ACCOUNT_USAGE Access

```sql
-- Switch to your app owner role
USE ROLE <YOUR_APP_OWNER_ROLE>;

-- Try to query ACCOUNT_USAGE
SELECT NAME 
FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES 
WHERE DELETED_ON IS NULL 
LIMIT 10;
```

**Expected Result:** List of roles  
**If Error:** You need to grant IMPORTED PRIVILEGES (see Option 1 above)

### Step 3: Test Grants Query

```sql
-- Test the exact query the app uses
USE ROLE <YOUR_APP_OWNER_ROLE>;

SELECT 
    GRANTED_ON,
    PRIVILEGE,
    CASE WHEN GRANTED_ON = 'ROLE' THEN NAME ELSE NULL END AS GRANTED_ROLE,
    NAME AS OBJECT_NAME
FROM SNOWFLAKE.ACCOUNT_USAGE.GRANTS_TO_ROLES
WHERE GRANTEE_NAME = 'PUBLIC'  -- Test with PUBLIC role
  AND DELETED_ON IS NULL
LIMIT 10;
```

**Expected Result:** List of grants  
**If Error:** Check the error message and grant appropriate permissions

---

## 🚨 Troubleshooting Specific Errors

### Error: "SQL compilation error: invalid identifier 'GRANTED_ROLE'"

**Cause:** Query syntax error or insufficient permissions

**Fix:**
```sql
-- Grant IMPORTED PRIVILEGES
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <APP_OWNER_ROLE>;
```

### Error: "Stored procedure execution error: Unsupported statement type 'SHOW GRANT'"

**Cause:** SHOW GRANTS is not supported in Streamlit in Snowflake

**Fix:** This is expected! The app will automatically fall back to INFORMATION_SCHEMA queries. However, you still need to grant IMPORTED PRIVILEGES for full functionality.

### Error: "Object does not exist, or operation cannot be performed"

**Cause:** Role doesn't have access to SNOWFLAKE database

**Fix:**
```sql
-- Grant access to SNOWFLAKE database
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <APP_OWNER_ROLE>;
```

### Error: "Insufficient privileges to operate on database 'SNOWFLAKE'"

**Cause:** You're not running as ACCOUNTADMIN or a role with sufficient privileges

**Fix:**
```sql
-- Switch to ACCOUNTADMIN first
USE ROLE ACCOUNTADMIN;

-- Then grant the privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <APP_OWNER_ROLE>;
```

---

## 🔒 Security Best Practices

### 1. Use a Dedicated Role
✅ **DO:** Create a specific role for the app (e.g., `CORTEX_ADMIN`)  
❌ **DON'T:** Use `ACCOUNTADMIN` as the app owner

### 2. Principle of Least Privilege
✅ **DO:** Grant only `IMPORTED PRIVILEGES` on SNOWFLAKE database  
❌ **DON'T:** Grant `MANAGE GRANTS` unless absolutely necessary

### 3. Document the Role
```sql
-- Add a comment explaining the role's purpose
COMMENT ON ROLE CORTEX_ADMIN IS 
'App owner role for Cortex RBAC Tool. Has read-only access to ACCOUNT_USAGE for querying role grants.';
```

### 4. Regular Audits
```sql
-- Periodically review what privileges the role has
SHOW GRANTS TO ROLE CORTEX_ADMIN;

-- Check who has this role
SHOW GRANTS OF ROLE CORTEX_ADMIN;
```

### 5. Limit Role Assignment
✅ **DO:** Grant the app owner role only to necessary users  
❌ **DON'T:** Grant it to PUBLIC or broad user groups

---

## 📋 Checklist

Before deploying the Cortex RBAC Tool, verify:

- [ ] Created a dedicated app owner role (e.g., `CORTEX_ADMIN`)
- [ ] Granted `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` to the role
- [ ] Created database and schema for the app
- [ ] Granted warehouse USAGE to the role
- [ ] Granted the role to your user
- [ ] Tested ACCOUNT_USAGE access with the role
- [ ] Tested the grants query with the role
- [ ] Documented the role's purpose
- [ ] Limited role assignment to necessary users

---

## 🎓 Understanding ACCOUNT_USAGE vs INFORMATION_SCHEMA

### ACCOUNT_USAGE (Preferred)
- **Scope:** Account-wide visibility
- **Data:** Comprehensive historical data
- **Latency:** Up to 2 hours delay
- **Access:** Requires `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE`
- **Use Case:** Full grant analysis, all roles

### INFORMATION_SCHEMA (Fallback)
- **Scope:** Current database/schema only
- **Data:** Real-time but limited
- **Latency:** None (real-time)
- **Access:** Based on current role's privileges
- **Use Case:** Limited grant visibility

**The app uses ACCOUNT_USAGE by default** for comprehensive results, with INFORMATION_SCHEMA as a fallback.

---

## 📞 Still Having Issues?

If you've followed this guide and still encounter errors:

1. **Verify you're running as ACCOUNTADMIN** when granting privileges
2. **Check the exact role name** used by your Streamlit app
3. **Review Snowflake query history** for detailed error messages
4. **Test queries manually** using the verification steps above
5. **Check Snowflake documentation** for any account-specific restrictions

### Useful Queries for Debugging

```sql
-- Who am I?
SELECT CURRENT_ROLE(), CURRENT_USER();

-- What can my current role do?
SHOW GRANTS TO ROLE IDENTIFIER(CURRENT_ROLE());

-- Can I access ACCOUNT_USAGE?
SELECT COUNT(*) FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES WHERE DELETED_ON IS NULL;

-- What roles exist in my account?
SELECT NAME FROM SNOWFLAKE.ACCOUNT_USAGE.ROLES WHERE DELETED_ON IS NULL ORDER BY NAME;
```

---

## 📚 Additional Resources

- [Snowflake ACCOUNT_USAGE Documentation](https://docs.snowflake.com/en/sql-reference/account-usage.html)
- [Snowflake Access Control](https://docs.snowflake.com/en/user-guide/security-access-control.html)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit.html)

---

**Last Updated:** October 27, 2025  
**Applies To:** Cortex RBAC Tool v2.0+

