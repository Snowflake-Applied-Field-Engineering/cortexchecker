# Cortex Tool - Quick Reference Card

## 🚀 Quick Start

```sql
-- 1. Setup (run as ACCOUNTADMIN)
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- 2. Deploy app in Snowsight → Streamlit
-- 3. Upload: cortex_tool.py
-- 4. Run!
```

## 🎯 Three Modes

### Mode 1: Role Permission Checker
**Use when:** Checking if roles are ready for Cortex Analyst

```
1. Select "Role Permission Checker"
2. Search for role
3. View readiness score (0-4)
4. Download remediation SQL if needed
```

**Checks:**
- ✅ Cortex database role
- ✅ Warehouse access
- ✅ Database/schema access
- ✅ Table SELECT privileges

### Mode 2: Agent Permission Generator
**Use when:** Creating least-privilege role for an agent

```
1. Select "Agent Permission Generator"
2. Choose agent (list or manual)
3. Click "Analyze Agent"
4. Download generated SQL
5. Execute in Snowflake
```

**Generates grants for:**
- Agent USAGE
- Semantic views
- Base tables
- Search services
- Procedures
- Warehouses

### Mode 3: Combined Analysis
**Use when:** Checking if a role can use a specific agent

```
1. Select "Combined Analysis"
2. Choose role + agent
3. Click "Analyze Compatibility"
4. Download fix SQL if needed
```

**Verifies:**
- ✅ Agent access
- ✅ Cortex role
- ✅ Warehouse access

## 📊 Readiness Scoring

| Score | Status | Meaning |
|-------|--------|---------|
| 4/4 | ✅ FULLY READY | All permissions present |
| 3/4 | ⚠️ MOSTLY READY | One permission missing |
| 2/4 | ⚠️ PARTIALLY READY | Two permissions missing |
| 0-1/4 | ❌ NOT READY | Multiple permissions missing |

## 🔧 Common SQL Fixes

### Grant Cortex Access
```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE <ROLE_NAME>;
```

### Grant Warehouse
```sql
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE <ROLE_NAME>;
```

### Grant Database/Schema
```sql
GRANT USAGE ON DATABASE <DB_NAME> TO ROLE <ROLE_NAME>;
GRANT USAGE ON SCHEMA <DB_NAME>.<SCHEMA_NAME> TO ROLE <ROLE_NAME>;
```

### Grant Table Access
```sql
GRANT SELECT ON TABLE <DB>.<SCHEMA>.<TABLE> TO ROLE <ROLE_NAME>;
-- Or all tables in schema:
GRANT SELECT ON ALL TABLES IN SCHEMA <DB>.<SCHEMA> TO ROLE <ROLE_NAME>;
```

### Grant Agent Access
```sql
GRANT USAGE ON AGENT <DB>.<SCHEMA>.<AGENT> TO ROLE <ROLE_NAME>;
```

## 🔍 Search Patterns

| Pattern | Matches |
|---------|---------|
| `ANALYST_*` | All roles starting with ANALYST_ |
| `*_READER` | All roles ending with _READER |
| `*PROD*` | All roles containing PROD |
| `DATA_*` | All roles starting with DATA_ |

## 📥 Export Formats

- **CSV** - For spreadsheet analysis
- **JSON** - For programmatic processing
- **HTML** - For formatted reports
- **SQL** - For execution in Snowflake

## ⚡ Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Search roles | Click search box, start typing |
| Refresh data | Click "Refresh Data" button |
| Download | Click download button |
| Expand section | Click expander |

## 🐛 Troubleshooting

### "Could not query roles"
```sql
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

### "No agents found"
- Verify agents exist: `SHOW AGENTS IN ACCOUNT;`
- Use manual entry mode
- Check app owner role permissions

### "App won't load"
- Check warehouse is running
- Verify role has privileges
- Check for syntax errors

### "Download not working"
- Try different browser
- Check browser download settings
- Ensure pop-ups allowed

## 📚 Documentation Links

- **Full Guide:** TOOL_README.md
- **Quick Start:** UNIFIED_QUICKSTART.md
- **Test Plan:** TEST_PLAN.md
- **Deployment:** DEPLOYMENT_GUIDE.md

## 🎓 Example Workflows

### Workflow 1: Onboard New Analyst
```
1. Create role: CREATE ROLE DATA_ANALYST;
2. Check readiness (Mode 1)
3. Download remediation SQL
4. Execute SQL
5. Grant role to user
```

### Workflow 2: Setup Agent Access
```
1. Create agent in Snowflake
2. Generate permissions (Mode 2)
3. Download SQL
4. Execute SQL
5. Test with user
```

### Workflow 3: Audit All Roles
```
1. Bulk analysis with pattern: *ANALYST*
2. View comparison table
3. Export to CSV
4. Review and fix issues
```

## 💡 Pro Tips

1. **Use Patterns** - Bulk analyze with wildcards
2. **Compare Roles** - Find best-configured roles
3. **Export Everything** - Keep records
4. **Test First** - Use test roles/agents
5. **Review SQL** - Always review before executing

## 🔐 Security Best Practices

- ✅ Use least-privilege principles
- ✅ Create dedicated roles per agent
- ✅ Avoid granting to PUBLIC
- ✅ Audit regularly
- ✅ Document all grants

## 📞 Support

- **GitHub:** https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker
- **Issues:** Create GitHub issue
- **Docs:** Check TOOL_README.md

## 🎯 Quick Checklist

### For Role Analysis
- [ ] Search for role
- [ ] View readiness score
- [ ] Check issues
- [ ] Download remediation SQL
- [ ] Execute SQL
- [ ] Re-check

### For Agent Permissions
- [ ] Select agent
- [ ] Analyze tools
- [ ] Review dependencies
- [ ] Customize role name
- [ ] Download SQL
- [ ] Execute and test

### For Compatibility
- [ ] Select role
- [ ] Select agent
- [ ] Analyze compatibility
- [ ] Review gaps
- [ ] Download fix SQL
- [ ] Execute and verify

---

**Version:** 3.0.0  
**Last Updated:** October 31, 2025

**Need more details?** See [TOOL_README.md](TOOL_README.md)

