# Cortex Unified Tool

## Overview

The **Cortex Unified Tool** combines the best features of two powerful Snowflake utilities:
- **CortexChecker** - Role permission analysis and Cortex Analyst readiness assessment
- **CART (Cortex Agent Role Tool)** - Automated least-privilege SQL generation for Cortex Agents

This unified tool provides a comprehensive solution for managing Snowflake Cortex AI permissions, whether you're working with roles, agents, or both.

## Key Features

### 🎯 Three Operational Modes

#### 1. Role Permission Checker
- **Comprehensive Grant Analysis** - View all permissions for any role
- **Cortex Readiness Scoring** - 4-point assessment (Cortex role, warehouse, database, tables)
- **Smart Recommendations** - Context-aware suggestions based on role patterns
- **Auto-Generated Remediation SQL** - Ready-to-run scripts to fix missing permissions
- **Search & Filter** - Find roles quickly with real-time search
- **Bulk Analysis** - Analyze multiple roles matching patterns (e.g., `ANALYST_*`)
- **Role Comparison** - Side-by-side comparison of multiple roles
- **Multi-Format Export** - Export grants as CSV, JSON, or HTML

#### 2. Agent Permission Generator
- **Agent Discovery** - Automatically find all Cortex Agents in your account
- **Tool Analysis** - Identify Cortex Analyst, Search, and Generic tools
- **Semantic View Processing** - Extract table dependencies from semantic views
- **YAML Parsing** - Analyze semantic model definitions
- **Comprehensive SQL Generation** - Create complete least-privilege scripts
- **Manual or Automatic** - Select from list or enter agent details manually

#### 3. Combined Analysis
- **Compatibility Checking** - Verify if a role can use a specific agent
- **Gap Analysis** - Identify missing permissions
- **Quick Fixes** - Generate SQL to grant missing permissions

## Installation

### Prerequisites

- Snowflake account with Cortex AI enabled
- Streamlit in Snowflake (SiS) environment
- App owner role with appropriate privileges:
  - `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` (recommended)
  - OR `MANAGE GRANTS` privilege

### Setup Steps

1. **Create Database and Schema**
```sql
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;
```

2. **Create App Owner Role**
```sql
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- Grant necessary privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Grant role to your user
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;
```

3. **Deploy to Snowflake**
   - Navigate to Snowsight → Streamlit
   - Create new Streamlit app
   - Upload `cortex_unified_tool.py` file
   - Set app role to `CORTEX_ADMIN`
   - Run the app

## Usage Guide

### Mode 1: Role Permission Checker

**Use Case:** Verify if a role is ready to use Cortex Analyst

**Steps:**
1. Select "Role Permission Checker" from the sidebar
2. Use search or bulk analysis to find roles
3. Select one or more roles to analyze
4. Review readiness score and detailed grants
5. Download remediation SQL if issues are found

**Example Workflow:**
```
1. Search for "DATA_ANALYST"
2. View readiness score (e.g., 3/4)
3. Identify missing permission: "No SELECT privileges on tables/views"
4. Expand "View Remediation SQL"
5. Download and execute SQL script
6. Re-analyze to confirm fixes
```

**Readiness Criteria:**
- ✅ **Cortex Role** - CORTEX_USER or CORTEX_ANALYST_USER
- ✅ **Warehouse Access** - USAGE on at least one warehouse
- ✅ **Database Access** - USAGE on database(s) and schema(s)
- ✅ **Table Access** - SELECT on table(s)/view(s)

### Mode 2: Agent Permission Generator

**Use Case:** Create least-privilege role for a Cortex Agent

**Steps:**
1. Select "Agent Permission Generator" from the sidebar
2. Choose agent selection method:
   - **Select from list** - Automatically discover agents
   - **Enter manually** - Specify database, schema, and agent name
3. Click "Analyze Agent"
4. Review agent tools and dependencies
5. Customize role name (optional)
6. Download generated SQL script
7. Execute in Snowflake worksheet

**Generated SQL Includes:**
- Role creation
- Agent USAGE grant
- Database and schema USAGE grants
- Semantic view SELECT grants
- Table SELECT grants (from YAML analysis)
- Cortex Search service USAGE grants
- Stored procedure USAGE grants
- Warehouse USAGE grant
- Optional user creation

**Example Output:**
```sql
-- AUTO-GENERATED LEAST-PRIVILEGE SCRIPT FOR AGENT: DB.SCHEMA.MY_AGENT
SET AGENT_ROLE_NAME = 'MY_AGENT_USER_ROLE';
SET WAREHOUSE_NAME = 'COMPUTE_WH';

CREATE ROLE IF NOT EXISTS IDENTIFIER($AGENT_ROLE_NAME);
GRANT USAGE ON AGENT DB.SCHEMA.MY_AGENT TO ROLE IDENTIFIER($AGENT_ROLE_NAME);
GRANT SELECT ON VIEW DB.SCHEMA.METRICS_VIEW TO ROLE IDENTIFIER($AGENT_ROLE_NAME);
GRANT SELECT ON TABLE DB.SCHEMA.BASE_TABLE TO ROLE IDENTIFIER($AGENT_ROLE_NAME);
-- ... additional grants ...
```

### Mode 3: Combined Analysis

**Use Case:** Check if a specific role can use a specific agent

**Steps:**
1. Select "Combined Analysis" from the sidebar
2. Choose a role from the dropdown
3. Choose an agent from the dropdown
4. Click "Analyze Compatibility"
5. Review compatibility results
6. Download fix SQL if needed

**Compatibility Checks:**
- ✅ Agent USAGE permission
- ✅ Cortex database role
- ✅ Warehouse access

## Features Comparison

| Feature | Role Checker | Agent Generator | Combined |
|---------|-------------|-----------------|----------|
| Role analysis | ✅ | ❌ | ✅ |
| Agent analysis | ❌ | ✅ | ✅ |
| Readiness scoring | ✅ | ❌ | ✅ |
| SQL generation | ✅ | ✅ | ✅ |
| Bulk operations | ✅ | ❌ | ❌ |
| Compatibility check | ❌ | ❌ | ✅ |
| Export options | ✅ | ✅ | ❌ |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Cortex Unified Tool                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────┐ │
│  │ Role Permission  │  │ Agent Permission │  │ Combined  │ │
│  │    Checker       │  │    Generator     │  │ Analysis  │ │
│  └────────┬─────────┘  └────────┬─────────┘  └─────┬─────┘ │
│           │                     │                   │        │
│           └─────────────────────┴───────────────────┘        │
│                              │                               │
│                              ▼                               │
│           ┌──────────────────────────────────┐              │
│           │    Snowflake Snowpark Session    │              │
│           └──────────────────────────────────┘              │
│                              │                               │
│           ┌──────────────────┴──────────────────┐           │
│           │                                      │           │
│           ▼                                      ▼           │
│  ┌─────────────────┐                  ┌─────────────────┐  │
│  │ ACCOUNT_USAGE   │                  │  Agent Objects  │  │
│  │ - ROLES         │                  │  - DESCRIBE     │  │
│  │ - GRANTS        │                  │  - SHOW         │  │
│  └─────────────────┘                  └─────────────────┘  │
│           │                                      │           │
│           ▼                                      ▼           │
│  ┌─────────────────┐                  ┌─────────────────┐  │
│  │ Analysis Engine │                  │ SQL Generator   │  │
│  │ - Readiness     │                  │ - Permissions   │  │
│  │ - Scoring       │                  │ - YAML Parsing  │  │
│  │ - Recommendations│                 │ - Dependencies  │  │
│  └─────────────────┘                  └─────────────────┘  │
│           │                                      │           │
│           └──────────────────┬───────────────────┘           │
│                              ▼                               │
│                   ┌────────────────────┐                     │
│                   │  SQL Script Output │                     │
│                   └────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## Best Practices

### For Role Analysis
1. **Start with Search** - Use the search feature to quickly find roles
2. **Use Bulk Analysis** - Analyze multiple similar roles at once (e.g., `*_ANALYST`)
3. **Review Regularly** - Periodically audit role permissions
4. **Test Changes** - Execute remediation SQL in non-production first
5. **Document Decisions** - Keep track of why certain permissions were granted

### For Agent Permissions
1. **Review Generated SQL** - Always review before executing
2. **Customize Role Names** - Use meaningful names that reflect purpose
3. **Test in Stages** - Grant permissions incrementally and test
4. **Monitor Usage** - Track which roles are actually using agents
5. **Update as Needed** - Re-generate SQL when agent tools change

### Security Considerations
1. **Principle of Least Privilege** - Only grant necessary permissions
2. **Separate Roles** - Create dedicated roles for each agent
3. **Avoid PUBLIC** - Never grant agent access to PUBLIC role
4. **Audit Regularly** - Review permissions quarterly
5. **Revoke Unused** - Remove permissions for inactive users/roles

## Troubleshooting

### Common Issues

#### "Could not query roles from ACCOUNT_USAGE"
**Cause:** App owner lacks access to SNOWFLAKE database

**Solution:**
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <APP_OWNER_ROLE>;
```

#### "Could not retrieve grants for role"
**Cause:** App owner lacks MANAGE GRANTS privilege

**Solution:**
```sql
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE <APP_OWNER_ROLE>;
```

#### "No agents found"
**Cause:** No agents exist or app owner lacks access

**Solution:**
1. Verify agents exist: `SHOW AGENTS IN ACCOUNT;`
2. Grant access: `GRANT USAGE ON AGENT <AGENT_NAME> TO ROLE <APP_OWNER_ROLE>;`

#### "Failed to describe agent"
**Cause:** Agent doesn't exist or insufficient permissions

**Solution:**
1. Check agent name spelling
2. Verify database and schema names
3. Grant USAGE on agent to app owner role

#### "Could not read YAML from semantic view"
**Cause:** Semantic view doesn't exist or lacks permissions

**Solution:**
1. Verify semantic view exists
2. Grant SELECT on semantic view to app owner role

## Advanced Features

### Custom Filters
Use pattern matching for bulk analysis:
- `ANALYST_*` - All roles starting with ANALYST_
- `*_READER` - All roles ending with _READER
- `*PROD*` - All roles containing PROD

### Export Formats
Role grants can be exported as:
- **CSV** - For spreadsheet analysis
- **JSON** - For programmatic processing
- **HTML** - For formatted reports

### Caching
The tool uses Streamlit caching for performance:
- Role lists are cached
- Grant queries are cached per role
- Agent lists are cached
- Use "Refresh Data" button to clear cache

## Integration with Existing Tools

### CortexChecker (Original)
The unified tool **replaces** the original cortexrbac script with enhanced features:
- All original functionality preserved
- Added agent permission generation
- Added combined analysis mode
- Improved UI/UX

### CART (Original)
The unified tool **integrates** CART functionality:
- Agent discovery from CART
- Semantic view analysis from CART
- SQL generation from CART
- Enhanced with role compatibility checking

## Version History

### v1.0.0 (2025-10-31)
- Initial release combining CortexChecker and CART
- Three operational modes: Role Checker, Agent Generator, Combined Analysis
- Comprehensive SQL generation for both roles and agents
- Enhanced UI with better navigation
- Improved error handling and user feedback

## Contributing

To contribute to this tool:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly in Snowflake
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or feature requests:
- Create an issue in the GitHub repository
- Contact the Snowflake Applied Field Engineering team

## Acknowledgments

This tool combines work from:
- **CortexChecker** - Original role analysis tool
- **CART** - Cortex Agent Role Tool by Snowflake AFE
- Built with Streamlit, Snowflake Snowpark, and Pandas

---

**Built for Snowflake Cortex AI** 🚀

