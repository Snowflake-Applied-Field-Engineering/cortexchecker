# Cortex Tool - Complete Snowflake Cortex AI Permission Management

A comprehensive Streamlit application that combines role permission analysis and agent permission generation for **Snowflake Cortex AI**.

## Overview

**Cortex Tool** integrates the best features from two powerful utilities:
- **CortexChecker** - Role permission analysis and Cortex Analyst readiness assessment
- **CART (Cortex Agent Role Tool)** - Automated least-privilege SQL generation for Cortex Agents

This solution helps Snowflake administrators manage permissions for both roles and agents, providing detailed analysis, smart recommendations, and auto-generated SQL scripts.
<img width="2147" height="1061" alt="image" src="https://github.com/user-attachments/assets/543c0a3f-cf49-4096-ae33-b72ae59fde2e" />
<img width="2181" height="1260" alt="image" src="https://github.com/user-attachments/assets/79a87557-dbe2-400c-addb-c43285239b09" />
<img width="2151" height="1217" alt="image" src="https://github.com/user-attachments/assets/dd95bffc-7872-49e3-a083-6ff2877adb7f" />


## Key Features

### 🎯 Three Operational Modes

1. **Role Permission Checker**
   - Comprehensive grant analysis for any role
   - Cortex Analyst readiness scoring (4-point assessment)
   - Smart recommendations based on role patterns
   - Auto-generated remediation SQL
   - Search, filter, and bulk analysis
   - Role comparison and multi-format export

2. **Agent Permission Generator**
   - Automated agent discovery
   - Semantic view and YAML analysis
   - Tool dependency extraction (Analyst, Search, Generic)
   - Comprehensive least-privilege SQL generation
   - Support for manual or automatic agent selection

3. **Combined Analysis**
   - Role-to-agent compatibility checking
   - Gap analysis and quick fixes
   - Verify if specific roles can use specific agents

## Quick Start

### Prerequisites

- Snowflake account with Cortex AI enabled
- Streamlit in Snowflake (SiS) environment
- App owner role with appropriate privileges:
  - `IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE` (recommended)
  - OR `MANAGE GRANTS` privilege

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git
cd cortexchecker
```

2. **Deploy to Snowflake:**
```sql
-- Create database and schema
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- Create a dedicated role for the app
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- Grant necessary privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Grant role to your user
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;
```

3. **Upload the Streamlit app:**
   - Navigate to Snowsight → Streamlit
   - Create new Streamlit app
   - Upload `CortexRoleTool/cortex_tool.py` file (or use `cortexrbac` for role-only analysis)
   - Set app role to `CORTEX_ADMIN`
   - Run the app

## Usage

### Mode 1: Role Permission Checker

**Check if roles are ready for Cortex Analyst**

1. Select "Role Permission Checker" from sidebar
2. Search or use bulk analysis to find roles
3. Select one or more roles to analyze
4. Review readiness score (0-4 points)
5. Download remediation SQL if needed

**Example:**
```
1. Search for "DATA_ANALYST"
2. View score: 3/4 (missing table access)
3. Click "View Remediation SQL"
4. Download and execute SQL
5. Re-analyze to confirm
```

### Mode 2: Agent Permission Generator

**Create least-privilege roles for Cortex Agents**

1. Select "Agent Permission Generator" from sidebar
2. Choose agent (from list or enter manually)
3. Click "Analyze Agent"
4. Review tools and dependencies
5. Customize role name
6. Download generated SQL

**Example:**
```
1. Select agent: MYDB.MYSCHEMA.SALES_AGENT
2. Review: 2 Analyst tools, 1 Search tool
3. See semantic views and base tables
4. Download SQL with all required grants
5. Execute in Snowflake worksheet
```

### Mode 3: Combined Analysis

**Check role-to-agent compatibility**

1. Select "Combined Analysis" from sidebar
2. Choose a role and an agent
3. Click "Analyze Compatibility"
4. Review compatibility checks
5. Download fix SQL if needed

**Example:**
```
1. Role: DATA_ANALYST
2. Agent: SALES_AGENT
3. Result: Missing agent USAGE permission
4. Download and execute fix SQL
```

## Documentation

- **[CortexRoleTool/TOOL_README.md](CortexRoleTool/TOOL_README.md)** - Complete tool guide
- **[CortexRoleTool/README.md](CortexRoleTool/README.md)** - Original role checker documentation
- **[CortexRoleTool/QUICKSTART.md](CortexRoleTool/QUICKSTART.md)** - 5-minute setup guide
- **[CortexRoleTool/PERMISSIONS_SETUP.md](CortexRoleTool/PERMISSIONS_SETUP.md)** - Detailed permissions guide

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       Cortex Tool                            │
├─────────────────────────────────────────────────────────────┤
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
│  └─────────────────┘                  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Cortex Analyst Requirements

For a role to use Cortex Analyst, it needs:

1. **Cortex Database Role** (Required)
   - `SNOWFLAKE.CORTEX_USER` OR
   - `SNOWFLAKE.CORTEX_ANALYST_USER`

2. **Compute Resources** (Required)
   - `USAGE` on at least one warehouse

3. **Data Access** (Required)
   - `USAGE` on database(s)
   - `USAGE` on schema(s)
   - `SELECT` on table(s)/view(s)

## Troubleshooting

### Common Issues

**"Could not query roles from ACCOUNT_USAGE"**
```sql
-- Grant access to SNOWFLAKE database
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE <APP_OWNER_ROLE>;
```

**"Could not retrieve grants for role"**
```sql
-- Grant MANAGE GRANTS privilege
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE <APP_OWNER_ROLE>;
```

See [PERMISSIONS_SETUP.md](CortexRoleTool/PERMISSIONS_SETUP.md) for detailed troubleshooting.



### Development Setup

```bash
# Clone the repository
git clone https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker.git
cd cortexchecker

# Install dependencies
pip install -r requirements.txt

# Run locally (limited functionality without Snowflake session)
streamlit run CortexRoleTool/cortexrbac
```

## License

MIT License - See LICENSE file for details


## Acknowledgments

Built with:
- **Streamlit** - Web framework
- **Snowflake Snowpark** - Database connectivity
- **Pandas** - Data manipulation

## Version History

- **v3.0.0** (2025-10-31) - Combined Tool Release
  - Integrated CART (Cortex Agent Role Tool) functionality
  - Added Agent Permission Generator mode
  - Added Combined Analysis mode (role-to-agent compatibility)
  - Enhanced SQL generation for both roles and agents
  - Improved navigation with three operational modes
  - Comprehensive documentation updates

- **v2.1.0** (2025-10-28) - Major feature release
  - Added search and bulk analysis
  - Auto-generated remediation SQL
  - Smart recommendations
  - Multi-format export
  - Role comparison
  - Metrics dashboard

- **v2.0.0** (2025-10-27) - Complete overhaul
  - Fixed critical bugs
  - Enhanced UI/UX
  - Comprehensive documentation



