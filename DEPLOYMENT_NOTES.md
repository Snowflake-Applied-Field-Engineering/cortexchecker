# Snowflake Cortex Security Hub - Deployment Notes

## Latest Updates (November 6, 2025)

### Recent Commits Ready for Deployment

#### 1. **Semantic View Deep Dive Logic** (Commit: `f8058c8`)
- Added `SYSTEM$GET_SEMANTIC_MODEL_DEFINITION` function support (newer Snowflake versions)
- Fallback to `SYSTEM$READ_YAML_FROM_SEMANTIC_VIEW` for older versions
- Automatic table extraction from `INFORMATION_SCHEMA.OBJECT_DEPENDENCIES` when YAML parsing fails
- **Impact**: Now correctly identifies underlying tables (NETWORK_LOGS, QUERY_LOGS, SYSTEM_LOGS, etc.) from semantic views

#### 2. **Manual Agent Entry Mode** (Commit: `c93190e`)
- Added toggle between "Select from existing agents" and "Enter manually"
- Manual mode allows specifying agents that don't exist yet or are in different accounts
- **Impact**: No longer locked to session's current database/schema context

#### 3. **Simplified Dropdown Lists** (Commit: `fdd0a0e`)
- Replaced cascading filtered dropdowns with independent lists
- All databases, schemas, and agent names visible at once
- **Impact**: Easier agent selection, no dependency between dropdowns

### Key Features Now Working

✅ **Agent Spec Parsing**
- Handles `agent_spec` as string or dict
- Supports nested tool properties in `tool_spec`, `definition`, or `spec`
- Extracts semantic views from both `tools` array and `tool_resources`

✅ **Semantic View Analysis**
- Tries multiple YAML extraction methods
- Falls back to INFORMATION_SCHEMA for table dependencies
- Generates `GRANT SELECT ON VIEW` for semantic views
- Generates `GRANT SELECT ON TABLE` for underlying tables

✅ **Clean UI**
- Removed all debug output
- Added "Run in SQL Worksheet" button with instructions
- Manual entry mode for flexibility

### Deployment Steps

1. **Upload to Snowflake**
   ```sql
   -- In Snowsight, create a new Streamlit app
   -- Name: CORTEX_SECURITY_HUB
   -- Warehouse: Your compute warehouse
   -- App location: Your database and schema
   ```

2. **Copy Code**
   - Copy contents of `cortex_tool.py`
   - Paste into Streamlit editor in Snowsight

3. **Test Scenarios**
   - Test with existing agent (dropdown mode)
   - Test with manual entry mode
   - Verify semantic view table extraction
   - Check generated SQL includes:
     - Agent usage grants
     - Database/schema usage grants
     - Semantic view grants
     - Underlying table grants
     - Warehouse usage grants

### Known Working Configuration

- **Snowflake Version**: Compatible with Cortex AI features
- **Required Privileges**: 
  - `DESCRIBE AGENT` on target agents
  - `SELECT` on `INFORMATION_SCHEMA.OBJECT_DEPENDENCIES`
  - Access to semantic views for YAML extraction

### Files to Deploy

- **Primary**: `cortex_tool.py` (main application, Git-tracked)
- **Backup**: `cortexdemo.py` (identical copy, not tracked)

### Version

- **Current Version**: 2.0.0
- **App Name**: Snowflake Cortex Security Hub
- **GitHub**: https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker
- **Branch**: `main` (up to date with commit `fdd0a0e`)

