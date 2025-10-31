# Cortex Unified Tool - Test Plan

## Overview

This document outlines the testing strategy for the Cortex Unified Tool, which combines role permission checking and agent permission generation.

## Test Environment Setup

### Prerequisites
- Snowflake account with Cortex AI enabled
- Test database: `CORTEX_TOOLS_TEST`
- Test warehouse: `COMPUTE_WH`
- Test roles with varying permissions
- Test Cortex Agent (optional but recommended)

### Setup Script

```sql
-- Create test environment
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS_TEST;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS_TEST.TEST_SCHEMA;

-- Create test roles with different permission levels
CREATE ROLE IF NOT EXISTS TEST_ROLE_FULL;
CREATE ROLE IF NOT EXISTS TEST_ROLE_PARTIAL;
CREATE ROLE IF NOT EXISTS TEST_ROLE_MINIMAL;
CREATE ROLE IF NOT EXISTS TEST_ROLE_NONE;

-- Grant full Cortex access
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE TEST_ROLE_FULL;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE TEST_ROLE_FULL;
GRANT USAGE ON DATABASE CORTEX_TOOLS_TEST TO ROLE TEST_ROLE_FULL;
GRANT USAGE ON SCHEMA CORTEX_TOOLS_TEST.TEST_SCHEMA TO ROLE TEST_ROLE_FULL;

-- Grant partial access (missing Cortex role)
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE TEST_ROLE_PARTIAL;
GRANT USAGE ON DATABASE CORTEX_TOOLS_TEST TO ROLE TEST_ROLE_PARTIAL;

-- Grant minimal access (only warehouse)
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE TEST_ROLE_MINIMAL;

-- TEST_ROLE_NONE has no grants

-- Create test table for SELECT grants
CREATE TABLE IF NOT EXISTS CORTEX_TOOLS_TEST.TEST_SCHEMA.TEST_TABLE (
    id NUMBER,
    name VARCHAR(100)
);

GRANT SELECT ON TABLE CORTEX_TOOLS_TEST.TEST_SCHEMA.TEST_TABLE TO ROLE TEST_ROLE_FULL;
```

## Test Cases

### Mode 1: Role Permission Checker

#### TC-1.1: View All Roles
**Objective:** Verify app can fetch and display all roles

**Steps:**
1. Launch app
2. Select "Role Permission Checker"
3. Observe role list in sidebar

**Expected Result:**
- All roles visible to app owner are displayed
- Roles are sorted alphabetically
- Count of roles is shown

**Pass Criteria:** ✅ All test roles (TEST_ROLE_FULL, TEST_ROLE_PARTIAL, etc.) are visible

---

#### TC-1.2: Search Functionality
**Objective:** Verify role search works correctly

**Steps:**
1. In Role Permission Checker mode
2. Type "TEST_ROLE" in search box
3. Observe filtered results

**Expected Result:**
- Only roles containing "TEST_ROLE" are shown
- Count updates to show filtered count
- Search is case-insensitive

**Pass Criteria:** ✅ Only test roles are displayed

---

#### TC-1.3: Analyze Fully Ready Role
**Objective:** Verify correct analysis of role with all permissions

**Steps:**
1. Select TEST_ROLE_FULL
2. Review analysis results

**Expected Result:**
- Cortex Access: ✅ Yes
- Readiness Score: 4/4 (if table grants included)
- Status: "FULLY READY"
- No issues listed
- Progress bar at 100%

**Pass Criteria:** ✅ Score is 4/4 or 3/4 depending on table grants

---

#### TC-1.4: Analyze Partially Ready Role
**Objective:** Verify correct identification of missing permissions

**Steps:**
1. Select TEST_ROLE_PARTIAL
2. Review analysis results

**Expected Result:**
- Cortex Access: ❌ No
- Readiness Score: 2/4 or less
- Status: "PARTIALLY READY" or "NOT READY"
- Issues listed: "Missing CORTEX_USER or CORTEX_ANALYST_USER role"
- Remediation SQL available

**Pass Criteria:** ✅ Missing Cortex role is identified

---

#### TC-1.5: Remediation SQL Generation
**Objective:** Verify SQL script generation for fixing issues

**Steps:**
1. Select TEST_ROLE_PARTIAL
2. Expand "View Remediation SQL"
3. Review generated SQL

**Expected Result:**
- SQL includes GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER
- SQL is syntactically correct
- Download button works
- SQL includes role name variable

**Pass Criteria:** ✅ SQL is valid and addresses identified issues

---

#### TC-1.6: Bulk Analysis
**Objective:** Verify bulk analysis with pattern matching

**Steps:**
1. Click "Bulk Analysis" in sidebar
2. Enter pattern: "TEST_ROLE_*"
3. Click "Analyze All Matching"

**Expected Result:**
- All TEST_ROLE_* roles are found
- Count is displayed
- Roles are automatically selected

**Pass Criteria:** ✅ All 4 test roles are matched

---

#### TC-1.7: Multi-Role Comparison
**Objective:** Verify comparison table for multiple roles

**Steps:**
1. Select multiple roles (TEST_ROLE_FULL, TEST_ROLE_PARTIAL, TEST_ROLE_NONE)
2. Review comparison table

**Expected Result:**
- Comparison table shows all selected roles
- Columns: Role, Cortex Access, Warehouses, Databases, Readiness, Status
- Data is accurate for each role
- Export CSV button works

**Pass Criteria:** ✅ Comparison accurately reflects permission differences

---

#### TC-1.8: Export Functionality
**Objective:** Verify data export in multiple formats

**Steps:**
1. Select TEST_ROLE_FULL
2. Expand "View All Grants"
3. Download CSV, JSON, and HTML

**Expected Result:**
- All three formats download successfully
- Data is complete and accurate
- Files are properly formatted

**Pass Criteria:** ✅ All exports contain correct grant data

---

### Mode 2: Agent Permission Generator

#### TC-2.1: Agent Discovery
**Objective:** Verify automatic agent discovery

**Steps:**
1. Select "Agent Permission Generator"
2. Choose "Select from list"
3. Observe agent dropdown

**Expected Result:**
- All accessible agents are listed
- Format: DATABASE.SCHEMA.AGENT_NAME
- If no agents: "No agents found" message

**Pass Criteria:** ✅ Existing agents are displayed OR appropriate message shown

---

#### TC-2.2: Manual Agent Entry
**Objective:** Verify manual agent specification

**Steps:**
1. Choose "Enter manually"
2. Enter: Database=TEST_DB, Schema=TEST_SCHEMA, Agent=TEST_AGENT
3. Click "Analyze Agent"

**Expected Result:**
- Fields accept input
- Analysis attempts to describe agent
- Appropriate error if agent doesn't exist

**Pass Criteria:** ✅ Manual entry works, error handling is graceful

---

#### TC-2.3: Agent Analysis (with real agent)
**Objective:** Verify complete agent analysis

**Prerequisites:** Requires a real Cortex Agent

**Steps:**
1. Select an existing agent
2. Click "Analyze Agent"
3. Review results

**Expected Result:**
- Agent details displayed (database, schema, name, owner, created date)
- Tools categorized (Analyst, Search, Generic)
- Tool counts shown
- Semantic views listed (if any)
- Search services listed (if any)
- Procedures listed (if any)

**Pass Criteria:** ✅ All agent components are identified

---

#### TC-2.4: Semantic View Processing
**Objective:** Verify YAML parsing and table extraction

**Prerequisites:** Agent with semantic views

**Steps:**
1. Analyze agent with semantic views
2. Review semantic view section
3. Expand table details

**Expected Result:**
- Each semantic view is listed
- Tables used by each view are shown
- Table names are fully qualified (DB.SCHEMA.TABLE)

**Pass Criteria:** ✅ Tables are correctly extracted from YAML

---

#### TC-2.5: SQL Generation for Agent
**Objective:** Verify comprehensive SQL script generation

**Steps:**
1. Analyze an agent
2. Review generated SQL
3. Verify completeness

**Expected Result:**
SQL includes:
- Role creation
- Agent USAGE grant
- Database USAGE grants
- Schema USAGE grants
- Semantic view SELECT grants
- Table SELECT grants
- Search service USAGE grants
- Procedure USAGE grants
- Warehouse USAGE grant
- Optional user creation (commented)

**Pass Criteria:** ✅ SQL is complete and syntactically correct

---

#### TC-2.6: Custom Role Name
**Objective:** Verify role name customization

**Steps:**
1. Analyze an agent
2. Change role name from default to "CUSTOM_AGENT_ROLE"
3. Review generated SQL

**Expected Result:**
- SQL uses custom role name
- Variable SET AGENT_ROLE_NAME = 'CUSTOM_AGENT_ROLE'
- All grants reference the variable

**Pass Criteria:** ✅ Custom role name is used throughout SQL

---

#### TC-2.7: SQL Download
**Objective:** Verify SQL script download

**Steps:**
1. Analyze an agent
2. Click "Download SQL Script"
3. Open downloaded file

**Expected Result:**
- File downloads successfully
- Filename: {AGENT_NAME}_permissions.sql
- Content matches displayed SQL
- File is UTF-8 encoded

**Pass Criteria:** ✅ Downloaded file is valid SQL

---

### Mode 3: Combined Analysis

#### TC-3.1: Role-Agent Compatibility Check
**Objective:** Verify compatibility analysis

**Prerequisites:** At least one role and one agent

**Steps:**
1. Select "Combined Analysis"
2. Choose a role (e.g., TEST_ROLE_FULL)
3. Choose an agent
4. Click "Analyze Compatibility"

**Expected Result:**
- Three checks performed:
  - Agent Access
  - Cortex Role
  - Warehouse Access
- Each check shows ✅ or ❌
- Overall verdict displayed

**Pass Criteria:** ✅ Compatibility checks are accurate

---

#### TC-3.2: Incompatible Role Detection
**Objective:** Verify detection of missing permissions

**Steps:**
1. Select TEST_ROLE_NONE
2. Select any agent
3. Click "Analyze Compatibility"

**Expected Result:**
- All three checks show ❌
- Overall verdict: "Role needs additional permissions"
- "View Fix SQL" expander available

**Pass Criteria:** ✅ All missing permissions identified

---

#### TC-3.3: Fix SQL Generation
**Objective:** Verify fix SQL for compatibility issues

**Steps:**
1. Analyze incompatible role-agent pair
2. Expand "View Fix SQL"
3. Review generated SQL

**Expected Result:**
SQL includes:
- GRANT USAGE ON AGENT (if missing)
- GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER (if missing)
- GRANT USAGE ON WAREHOUSE (if missing)

**Pass Criteria:** ✅ Fix SQL addresses all identified gaps

---

### Cross-Cutting Tests

#### TC-4.1: Cache Refresh
**Objective:** Verify cache clearing works

**Steps:**
1. Analyze a role
2. Click "Refresh Data" in sidebar
3. Re-analyze the same role

**Expected Result:**
- Cache is cleared
- Data is re-fetched
- Results are consistent

**Pass Criteria:** ✅ Refresh works without errors

---

#### TC-4.2: Error Handling - No Permissions
**Objective:** Verify graceful handling of insufficient permissions

**Steps:**
1. Deploy app with role lacking IMPORTED PRIVILEGES
2. Attempt to fetch roles

**Expected Result:**
- Error message displayed
- Fallback to INFORMATION_SCHEMA attempted
- Helpful instructions provided

**Pass Criteria:** ✅ App doesn't crash, shows helpful error

---

#### TC-4.3: Error Handling - Invalid Agent
**Objective:** Verify handling of non-existent agent

**Steps:**
1. Enter manual agent: DB=FAKE, Schema=FAKE, Agent=FAKE
2. Click "Analyze Agent"

**Expected Result:**
- Error message: "Failed to analyze agent"
- Suggestion to check agent exists
- App remains functional

**Pass Criteria:** ✅ Error is caught and displayed gracefully

---

#### TC-4.4: Performance - Large Role List
**Objective:** Verify performance with many roles

**Steps:**
1. In account with 100+ roles
2. Load Role Permission Checker
3. Search for roles

**Expected Result:**
- Initial load completes within 5 seconds
- Search is responsive
- No timeouts

**Pass Criteria:** ✅ App remains responsive

---

#### TC-4.5: UI Responsiveness
**Objective:** Verify UI works on different screen sizes

**Steps:**
1. Test on wide screen (>1920px)
2. Test on standard screen (1366px)
3. Test on narrow screen (1024px)

**Expected Result:**
- Layout adjusts appropriately
- All buttons visible
- Text is readable
- No horizontal scrolling

**Pass Criteria:** ✅ UI is usable on all tested sizes

---

## Regression Tests

Run these tests after any code changes:

1. **Basic Functionality**
   - TC-1.1, TC-1.3, TC-2.1, TC-3.1

2. **SQL Generation**
   - TC-1.5, TC-2.5, TC-3.3

3. **Error Handling**
   - TC-4.2, TC-4.3

## Test Results Template

```
Test Run: [Date]
Tester: [Name]
Environment: [Snowflake Account]
App Version: v3.0.0

| Test ID | Test Name | Status | Notes |
|---------|-----------|--------|-------|
| TC-1.1  | View All Roles | ✅ PASS | |
| TC-1.2  | Search Functionality | ✅ PASS | |
| ... | ... | ... | ... |

Issues Found:
1. [Description]
2. [Description]

Overall Status: ✅ PASS / ⚠️ PASS WITH ISSUES / ❌ FAIL
```

## Automated Testing (Future)

Potential areas for automation:
- SQL syntax validation
- Grant query correctness
- YAML parsing accuracy
- Export file format validation

## Sign-Off

**Tested By:** ___________________  
**Date:** ___________________  
**Version:** ___________________  
**Status:** ✅ APPROVED / ❌ NEEDS WORK  

---

**Note:** This test plan should be executed before each major release and after significant code changes.

