# Deployment Guide - Cortex Unified Tool

## Overview

This guide walks you through deploying the Cortex Unified Tool to your Snowflake account and the GitHub repository.

## Prerequisites

- ✅ Snowflake account with Cortex AI enabled
- ✅ ACCOUNTADMIN or equivalent privileges
- ✅ Access to Snowsight
- ✅ GitHub repository access (for code upload)

## Part 1: Snowflake Deployment

### Step 1: Prepare Snowflake Environment

Run this SQL in a Snowflake worksheet as ACCOUNTADMIN:

```sql
-- ============================================================================
-- Cortex Unified Tool - Snowflake Setup
-- ============================================================================

-- Create database and schema for the app
CREATE DATABASE IF NOT EXISTS CORTEX_TOOLS;
CREATE SCHEMA IF NOT EXISTS CORTEX_TOOLS.APPS;

-- Create dedicated role for the app owner
CREATE ROLE IF NOT EXISTS CORTEX_ADMIN;

-- Grant necessary privileges to the app owner role
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE CORTEX_ADMIN;
GRANT ALL ON SCHEMA CORTEX_TOOLS.APPS TO ROLE CORTEX_ADMIN;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CORTEX_ADMIN;

-- Grant CORTEX_ADMIN to users who will manage the app
GRANT ROLE CORTEX_ADMIN TO USER <YOUR_USERNAME>;
GRANT ROLE CORTEX_ADMIN TO ROLE SYSADMIN;

-- Verify setup
USE ROLE CORTEX_ADMIN;
SELECT 'Snowflake environment ready!' as status;

-- Optional: Create test roles for validation
CREATE ROLE IF NOT EXISTS TEST_CORTEX_ROLE;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE TEST_CORTEX_ROLE;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE TEST_CORTEX_ROLE;
```

### Step 2: Deploy Streamlit App

#### Option A: Via Snowsight UI (Recommended)

1. **Navigate to Streamlit**
   - Log into Snowsight
   - Go to **Projects** → **Streamlit**
   - Click **+ Streamlit App**

2. **Configure App**
   - **App name:** `Cortex_Unified_Tool`
   - **Location:** `CORTEX_TOOLS.APPS`
   - **Warehouse:** `COMPUTE_WH`
   - **App role:** `CORTEX_ADMIN`

3. **Upload Code**
   - Delete the default code
   - Copy the entire contents of `CortexRoleTool/cortex_unified_tool.py`
   - Paste into the editor
   - Click **Run**

4. **Verify Deployment**
   - App should load without errors
   - Sidebar should show "Tool Selection"
   - Try selecting a role in Role Permission Checker mode

#### Option B: Via SQL (for automation)

```sql
-- Create Streamlit app via SQL
USE ROLE CORTEX_ADMIN;
USE DATABASE CORTEX_TOOLS;
USE SCHEMA APPS;
USE WAREHOUSE COMPUTE_WH;

-- Note: This requires the Streamlit code to be uploaded via Snowsight first
-- Then you can manage it via SQL
```

### Step 3: Grant Access to Users

```sql
-- Grant access to specific users
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE <USER_ROLE>;
GRANT USAGE ON SCHEMA CORTEX_TOOLS.APPS TO ROLE <USER_ROLE>;
GRANT USAGE ON STREAMLIT CORTEX_TOOLS.APPS.CORTEX_UNIFIED_TOOL TO ROLE <USER_ROLE>;

-- Or grant to all users (use with caution)
GRANT USAGE ON DATABASE CORTEX_TOOLS TO ROLE PUBLIC;
GRANT USAGE ON SCHEMA CORTEX_TOOLS.APPS TO ROLE PUBLIC;
GRANT USAGE ON STREAMLIT CORTEX_TOOLS.APPS.CORTEX_UNIFIED_TOOL TO ROLE PUBLIC;
```

### Step 4: Test Deployment

1. **Test Role Checker**
   - Select "Role Permission Checker"
   - Search for "PUBLIC"
   - Verify role analysis works

2. **Test Agent Generator** (if you have agents)
   - Select "Agent Permission Generator"
   - Try discovering agents
   - Verify SQL generation

3. **Test Combined Analysis**
   - Select "Combined Analysis"
   - Choose a role and agent
   - Verify compatibility check

### Step 5: Optional - Deploy Original Role Checker

If you want to keep both versions:

```sql
-- Deploy the original cortexrbac as a separate app
-- Follow same steps as above but use cortexrbac code
-- Name it: Cortex_Role_Checker
```

## Part 2: GitHub Repository Upload

### Step 1: Prepare Repository

```bash
# Navigate to your local repository
cd /Users/phorrigan/cortexdemocode

# Check current status
git status

# Verify you're on the correct branch
git branch
```

### Step 2: Add New Files

```bash
# Add the unified tool and documentation
git add CortexRoleTool/cortex_unified_tool.py
git add CortexRoleTool/UNIFIED_TOOL_README.md
git add CortexRoleTool/UNIFIED_QUICKSTART.md
git add CortexRoleTool/TEST_PLAN.md
git add CortexRoleTool/requirements_unified.txt

# Add updated main files
git add README.md
git add INTEGRATION_SUMMARY.md
git add DEPLOYMENT_GUIDE.md

# Check what will be committed
git status
```

### Step 3: Commit Changes

```bash
# Commit with descriptive message
git commit -m "v3.0.0: Integrate CART with CortexChecker

- Add unified tool combining role checker and agent permission generator
- Implement three operational modes: Role Checker, Agent Generator, Combined Analysis
- Add comprehensive documentation (README, QuickStart, Test Plan)
- Preserve original cortexrbac for backward compatibility
- Update main README with new features and architecture
- Add deployment guide and integration summary

Features:
- Role permission analysis with Cortex readiness scoring
- Agent discovery and semantic view processing
- Comprehensive SQL generation for both roles and agents
- Role-to-agent compatibility checking
- Search, filter, bulk analysis, and comparison
- Multi-format export (CSV, JSON, HTML)

Closes #[issue_number] (if applicable)"
```

### Step 4: Push to GitHub

```bash
# Push to your fork first (if working on a fork)
git push origin main

# Or push directly to main repository (if you have access)
git push upstream main
```

### Step 5: Create Release (Optional)

1. **Via GitHub UI:**
   - Go to repository on GitHub
   - Click **Releases** → **Create a new release**
   - Tag: `v3.0.0`
   - Title: `v3.0.0 - Unified Tool Release`
   - Description: Copy from INTEGRATION_SUMMARY.md

2. **Via Command Line:**
```bash
# Create and push tag
git tag -a v3.0.0 -m "v3.0.0: Unified Tool Release - Combines CortexChecker and CART"
git push origin v3.0.0
```

### Step 6: Update Repository README

Ensure the main repository README reflects:
- ✅ New unified tool
- ✅ Three operational modes
- ✅ Updated installation instructions
- ✅ Links to new documentation
- ✅ Version history

### Step 7: Create Pull Request (if using fork)

1. Go to your fork on GitHub
2. Click **Pull Request**
3. Title: `v3.0.0: Integrate CART with CortexChecker`
4. Description: Include summary from INTEGRATION_SUMMARY.md
5. Add reviewers
6. Submit PR

## Part 3: Documentation Updates

### Files to Update on GitHub

1. **README.md** (main) ✅ - Already updated
2. **CortexRoleTool/UNIFIED_TOOL_README.md** ✅ - Created
3. **CortexRoleTool/UNIFIED_QUICKSTART.md** ✅ - Created
4. **INTEGRATION_SUMMARY.md** ✅ - Created
5. **DEPLOYMENT_GUIDE.md** ✅ - This file

### GitHub Pages (Optional)

If your repository has GitHub Pages enabled:

1. Create `docs/` directory
2. Copy documentation files
3. Create index.html or use Jekyll
4. Enable GitHub Pages in repository settings

## Part 4: Post-Deployment

### Verification Checklist

- [ ] App loads without errors in Snowflake
- [ ] All three modes are accessible
- [ ] Role analysis works
- [ ] Agent analysis works (if agents exist)
- [ ] SQL generation works
- [ ] Downloads work
- [ ] Search and filter work
- [ ] Export functions work
- [ ] Documentation is accessible
- [ ] GitHub repository is updated

### User Communication

**Email Template:**

```
Subject: New Unified Cortex Permission Management Tool Available

Hi Team,

We're excited to announce the release of the Cortex Unified Tool v3.0.0!

What's New:
- Combines role permission checking and agent permission generation
- Three operational modes for different use cases
- Enhanced SQL generation for both roles and agents
- Role-to-agent compatibility checking

Access:
- Snowflake: [Link to Streamlit app]
- Documentation: [Link to GitHub]
- Quick Start: [Link to UNIFIED_QUICKSTART.md]

Getting Started:
1. Open the app in Snowsight
2. Choose your mode (Role Checker, Agent Generator, or Combined)
3. Follow the on-screen instructions

Questions? Check the documentation or contact [support contact].

Happy permission managing!
```

### Training Materials

Consider creating:
1. **Video Walkthrough** - Screen recording of each mode
2. **Presentation** - PowerPoint/Google Slides overview
3. **Workshop** - Hands-on training session
4. **FAQ Document** - Common questions and answers

## Part 5: Maintenance

### Regular Tasks

**Weekly:**
- Monitor app usage
- Check for errors in logs
- Review user feedback

**Monthly:**
- Review permissions on app owner role
- Check for Snowflake updates
- Update documentation if needed

**Quarterly:**
- Full test plan execution
- Performance review
- Feature enhancement planning

### Update Process

When making updates:

1. **Test in Development**
   - Deploy to test environment
   - Run test plan
   - Get user feedback

2. **Update Documentation**
   - Update README
   - Update version history
   - Update relevant guides

3. **Deploy to Production**
   - Update Streamlit app
   - Test in production
   - Notify users

4. **Update GitHub**
   - Commit changes
   - Create new release
   - Update changelog

## Troubleshooting

### Common Deployment Issues

**Issue: "Could not query roles from ACCOUNT_USAGE"**
```sql
-- Fix: Grant imported privileges
GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE CORTEX_ADMIN;
```

**Issue: "App won't load"**
- Check warehouse is running
- Verify role has necessary privileges
- Check for syntax errors in code

**Issue: "No agents found"**
- Verify agents exist: `SHOW AGENTS IN ACCOUNT;`
- Check app owner role has access to agents
- Try manual entry mode

**Issue: "GitHub push rejected"**
```bash
# Pull latest changes first
git pull origin main

# Resolve conflicts if any
# Then push again
git push origin main
```

## Rollback Plan

If deployment fails:

### Snowflake Rollback

1. **Keep Original App**
   - Original `cortexrbac` remains unchanged
   - Users can continue using it

2. **Delete New App**
```sql
DROP STREAMLIT CORTEX_TOOLS.APPS.CORTEX_UNIFIED_TOOL;
```

3. **Restore from Backup**
   - If you backed up the original, restore it

### GitHub Rollback

```bash
# Revert to previous commit
git revert HEAD

# Or reset to specific commit
git reset --hard <commit-hash>

# Force push (use with caution)
git push origin main --force
```

## Support

### Getting Help

- **Documentation:** Check UNIFIED_TOOL_README.md
- **Issues:** Create GitHub issue
- **Questions:** Contact Snowflake AFE team
- **Bugs:** Report via GitHub issues

### Contact Information

- **Repository:** https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker
- **Issues:** https://github.com/Snowflake-Applied-Field-Engineering/cortexchecker/issues

## Appendix

### A. Required Snowflake Privileges

**For App Owner Role (CORTEX_ADMIN):**
- IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE
- USAGE ON DATABASE CORTEX_TOOLS
- ALL ON SCHEMA CORTEX_TOOLS.APPS
- USAGE ON WAREHOUSE COMPUTE_WH

**For App Users:**
- USAGE ON DATABASE CORTEX_TOOLS
- USAGE ON SCHEMA CORTEX_TOOLS.APPS
- USAGE ON STREAMLIT CORTEX_TOOLS.APPS.CORTEX_UNIFIED_TOOL

### B. File Checklist

Files to deploy:
- [x] cortex_unified_tool.py
- [x] UNIFIED_TOOL_README.md
- [x] UNIFIED_QUICKSTART.md
- [x] TEST_PLAN.md
- [x] requirements_unified.txt
- [x] INTEGRATION_SUMMARY.md
- [x] DEPLOYMENT_GUIDE.md
- [x] Updated README.md

### C. Version Information

- **Version:** 3.0.0
- **Release Date:** October 31, 2025
- **Python Version:** 3.8+
- **Streamlit Version:** 1.28.0+
- **Snowpark Version:** 1.11.0+

---

**Deployment Complete!** 🎉

Your Cortex Unified Tool is now ready for use. Don't forget to communicate the release to your users and gather feedback for future improvements.

