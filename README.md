# Cortex Checker - Snowflake Cortex Analyst Access Checker

A comprehensive Streamlit application for analyzing Snowflake role permissions and assessing readiness for **Snowflake Cortex Analyst**.

## Overview

Cortex Checker helps Snowflake administrators quickly evaluate whether roles have the necessary permissions to use Cortex Analyst features. It provides detailed analysis, smart recommendations, and auto-generated remediation SQL scripts.
<img width="2147" height="1061" alt="image" src="https://github.com/user-attachments/assets/543c0a3f-cf49-4096-ae33-b72ae59fde2e" />
<img width="2181" height="1260" alt="image" src="https://github.com/user-attachments/assets/79a87557-dbe2-400c-addb-c43285239b09" />
<img width="2151" height="1217" alt="image" src="https://github.com/user-attachments/assets/dd95bffc-7872-49e3-a083-6ff2877adb7f" />


## Key Features

- **Role Permission Analysis** - Comprehensive grant analysis for any role
- **Cortex Readiness Scoring** - 4-point assessment of Cortex Analyst readiness
- **Smart Recommendations** - Context-aware suggestions based on role patterns
- **Auto-Generated SQL** - Ready-to-run scripts to fix missing permissions
- **Search & Filter** - Find roles quickly with real-time search
- **Bulk Analysis** - Analyze multiple roles matching patterns (e.g., `ANALYST_*`)
- **Role Comparison** - Side-by-side comparison of multiple roles
- **Multi-Format Export** - Export grants as CSV, JSON, or HTML
- **Metrics Dashboard** - Visual summary of key permissions

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
   - Upload `CortexRoleTool/cortexrbac` file
   - Set app role to `CORTEX_ADMIN`
   - Run the app

## Usage

### Basic Workflow

1. **Select Role(s)** - Use search or bulk analysis to find roles
2. **View Analysis** - Review Cortex readiness and detailed grants
3. **Get Recommendations** - See smart suggestions for improvements
4. **Fix Issues** - Download auto-generated SQL scripts
5. **Export Results** - Save analysis as CSV, JSON, or HTML

### Example Use Cases

**Check Single Role:**
```
1. Search for "DATA_ANALYST"
2. View readiness score (e.g., 3/4)
3. Expand "View Remediation SQL Script"
4. Download and run SQL to fix issues
```

**Bulk Analysis:**
```
1. Click "Bulk Analysis"
2. Enter pattern: "ANALYST_*"
3. Analyze all matching roles
4. Download comparison report
```

**Compare Roles:**
```
1. Select multiple roles
2. View comparison table
3. Identify best-configured role
4. Use as template for others
```

## Documentation

- **[CortexRoleTool/README.md](CortexRoleTool/README.md)** - Complete application guide
- **[CortexRoleTool/QUICKSTART.md](CortexRoleTool/QUICKSTART.md)** - 5-minute setup guide
- **[CortexRoleTool/PERMISSIONS_SETUP.md](CortexRoleTool/PERMISSIONS_SETUP.md)** - Detailed permissions guide
- **[CortexRoleTool/ENHANCEMENTS_ADDED.md](CortexRoleTool/ENHANCEMENTS_ADDED.md)** - Feature documentation

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Streamlit UI                       │
├─────────────────────────────────────────────────────┤
│  Search & Filter → Role Selection → Analysis        │
│                                                      │
│  ┌────────────────┐    ┌──────────────────┐        │
│  │ ACCOUNT_USAGE  │───▶│ Pandas DataFrame │        │
│  │    (Primary)   │    └──────────────────┘        │
│  └────────────────┘              │                  │
│         │ Fallback               ▼                  │
│         ▼                  ┌──────────┐             │
│  ┌────────────────┐        │ Analysis │             │
│  │ INFORMATION_   │───────▶│ Engine   │             │
│  │    SCHEMA      │        └──────────┘             │
│  └────────────────┘              │                  │
│                                  ▼                  │
│                        ┌──────────────────┐         │
│                        │ • Readiness Score│         │
│                        │ • Recommendations│         │
│                        │ • SQL Generation │         │
│                        │ • Export Options │         │
│                        └──────────────────┘         │
└─────────────────────────────────────────────────────┘
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

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

## Support

For issues or questions:
1. Check the [documentation](CortexRoleTool/README.md)
2. Review [troubleshooting guide](CortexRoleTool/PERMISSIONS_SETUP.md)
3. Open an issue on GitHub

## Acknowledgments

Built with:
- **Streamlit** - Web framework
- **Snowflake Snowpark** - Database connectivity
- **Pandas** - Data manipulation

## Version History

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

---

**Maintained by:** Snowflake Applied Field Engineering  
**Repository:** https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker
