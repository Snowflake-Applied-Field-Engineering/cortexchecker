# Quick Reference

## Common SQL Commands

### Grant Cortex Access
```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <ROLE_NAME>;
```

### Grant Warehouse
```sql
GRANT USAGE ON WAREHOUSE <WAREHOUSE_NAME> TO ROLE <ROLE_NAME>;
```

### Grant Database/Schema
```sql
GRANT USAGE ON DATABASE <DB_NAME> TO ROLE <ROLE_NAME>;
GRANT USAGE ON SCHEMA <DB_NAME>.<SCHEMA_NAME> TO ROLE <ROLE_NAME>;
```

### Grant Table Access
```sql
GRANT SELECT ON TABLE <DB>.<SCHEMA>.<TABLE> TO ROLE <ROLE_NAME>;
-- Or all tables:
GRANT SELECT ON ALL TABLES IN SCHEMA <DB>.<SCHEMA> TO ROLE <ROLE_NAME>;
```

### Grant Agent Access
```sql
GRANT USAGE ON AGENT <DB>.<SCHEMA>.<AGENT> TO ROLE <ROLE_NAME>;
```

### Grant Stage Access
```sql
GRANT READ ON STAGE <DB>.<SCHEMA>.<STAGE> TO ROLE <ROLE_NAME>;
```

## App Modes

### 1. Role Permission Checker
- Analyze role permissions
- Check Cortex readiness
- Generate remediation SQL
- Execute SQL directly

### 2. Agent Permission Generator
- Discover agents
- Parse tools and dependencies
- Generate least-privilege SQL
- Execute SQL directly

### 3. Combined Analysis
- Verify role-agent compatibility
- Identify missing permissions
- Generate fix SQL

## Keyboard Shortcuts

- **Search roles:** Start typing in role search box
- **Clear search:** Click X in search box
- **Expand/Collapse:** Click section headers

## Tips

### Role Analysis
- Use wildcards in search: `*ANALYST*`
- Check readiness score (0-4 points)
- Download SQL before executing
- Review grants in CSV export

### Agent Permissions
- Let tool discover agents automatically
- Review semantic views and tables
- Customize role names in SQL
- Use Execute SQL for quick setup

### Execute SQL
- Requires SECURITYADMIN or higher
- Review variables before executing
- Check execution results
- Download SQL as backup

## Troubleshooting Quick Fixes

```sql
-- Can't query roles
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;

-- Can't execute SQL
GRANT CREATE ROLE ON ACCOUNT TO ROLE CORTEX_ADMIN;
GRANT MANAGE GRANTS ON ACCOUNT TO ROLE CORTEX_ADMIN;

-- Can't see agents
GRANT USAGE ON DATABASE <AGENT_DB> TO ROLE CORTEX_ADMIN;
GRANT USAGE ON SCHEMA <AGENT_DB>.<AGENT_SCHEMA> TO ROLE CORTEX_ADMIN;
```

## Links

- [README.md](README.md) - Overview
- [QUICKSTART.md](QUICKSTART.md) - Quick start
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Detailed setup
- [PERMISSIONS_SETUP.md](PERMISSIONS_SETUP.md) - Permissions guide
