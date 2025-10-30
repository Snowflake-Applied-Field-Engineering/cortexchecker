# Snowflake Terraform Provider Upgrade Guide

This guide helps you upgrade your existing Snowflake Terraform configurations from older provider versions to the latest version. This is especially important if you're using provider versions older than v0.90.0.

## Table of Contents

- [Overview](#overview)
- [Before You Begin](#before-you-begin)
- [Version Compatibility](#version-compatibility)
- [Breaking Changes by Version](#breaking-changes-by-version)
- [Step-by-Step Upgrade Process](#step-by-step-upgrade-process)
- [Alternative: Direct Import to Latest Version](#alternative-direct-import-to-latest-version)
- [Common Migration Scenarios](#common-migration-scenarios)
- [Troubleshooting](#troubleshooting)
- [Additional Resources](#additional-resources)

## Overview

The Snowflake Terraform provider has undergone significant changes to align with Snowflake's best practices and improve resource management. The most significant changes are documented in the [Snowflake BCR Migration Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md#bundle-2025_04).

### Key Changes in Recent Versions

- **Bundle 2025_04**: Major breaking changes to resource schemas and behavior
- **v0.90.0+**: Introduction of new grant resources and deprecation of legacy grant patterns
- **v0.80.0+**: Changes to warehouse, database, and schema resource attributes
- **v0.70.0+**: Updates to role and user management

## Before You Begin

### Prerequisites

1. **Backup Your State File**
   ```bash
   # Local state
   cp terraform.tfstate terraform.tfstate.backup
   
   # Remote state (S3 example)
   aws s3 cp s3://your-bucket/path/terraform.tfstate ./terraform.tfstate.backup
   ```

2. **Review Current Configuration**
   ```bash
   terraform state list
   terraform show
   ```

3. **Check Current Provider Version**
   ```bash
   terraform version
   grep -A 5 "required_providers" *.tf
   ```

4. **Create a Test Environment**
   - Test the upgrade in a non-production environment first
   - Use a separate workspace or state file

### Important Warnings

- **Recommended: Incremental upgrades** - Upgrade incrementally (e.g., 0.70 → 0.80 → 0.90 → 1.0 → 2.3+)
- **Alternative: Direct import** - Consider importing infrastructure directly to v2.3+ (see below)
- **Review deprecation warnings** - Run `terraform plan` after each version upgrade
- **Test thoroughly** - Validate changes in dev/staging before production
- **Communicate with your team** - Coordinate upgrades to avoid conflicts

## Version Compatibility

| Provider Version | Terraform Version | Snowflake Compatibility | Status | Notes |
|-----------------|-------------------|------------------------|---------|-------|
| v2.3.x+ | >= 1.5.0 | All current versions | Current | BCR bundle fixes |
| v2.0.x - v2.2.x | >= 1.5.0 | All current versions | Supported | Update to 2.3+ for BCR |
| v1.0.x - v1.9.x | >= 1.4.0 | All current versions | Supported | Upgrade to 2.x |
| v0.94.x | >= 1.5.0 | All current versions | Deprecated | Legacy 0.x series |
| v0.90.x | >= 1.4.0 | All current versions | Deprecated | Legacy 0.x series |
| v0.80.x | >= 1.3.0 | All current versions | Deprecated | Legacy 0.x series |
| v0.70.x | >= 1.2.0 | All current versions | Deprecated | Legacy 0.x series |
| < v0.70.0 | >= 1.0.0 | All current versions | End of Life | Not supported |

**Key Version Milestones:**
- **v2.3.0+**: BCR bundle compatibility fixes (especially for SHOW FUNCTIONS/PROCEDURES)
- **v2.0.0**: Major version with breaking changes, new resource patterns
- **v1.0.0**: Grant system overhaul, deprecation of legacy grant resources
- **v0.90.0**: Introduction of `snowflake_grant_privileges_to_role`

## Breaking Changes by Version

### v2.3.x+ (Current)

**BCR Bundle Compatibility**
- Fixed parsing for SHOW FUNCTIONS/PROCEDURES with new argument format
- Resolves issues with function and procedure resources being removed from state
- Critical for BCR bundle compatibility

**Improvements**
- Better error messages
- Enhanced state management

### v2.0.x - v2.2.x

**Major Version 2.0 Changes**
- Refactoring of resource schemas (relatively small configuration changes)
- New resource patterns and naming conventions
- Enhanced validation and error handling
- Improved state management
- Removal of some sensitive fields

**Grant System Refinements**
- Further improvements to `snowflake_grant_privileges_to_role`
- Better handling of grant dependencies
- Enhanced privilege validation

**Migration Complexity**: Low - The changes between v1.x and v2.x are relatively small configuration adjustments, much simpler than the v0.90 → v1.0 migration

### v1.0.x - v1.9.x

**Major Grant System Overhaul (v1.0)**
- Introduction of `snowflake_grant_privileges_to_role` (unified grant resource)
- Deprecation of legacy grant resources:
  - `snowflake_database_grant`
  - `snowflake_schema_grant`
  - `snowflake_warehouse_grant`
  - `snowflake_table_grant`
  - `snowflake_view_grant`
- New grant ownership model

**Resource Improvements**
- More strict validation on resource names
- Case sensitivity enforced
- Better dependency handling

### v0.94.x (Legacy)

**Grant Resources Refactored**
- `snowflake_database_grant` → Use specific grant resources
- `snowflake_schema_grant` → Use specific grant resources
- `snowflake_warehouse_grant` → Use specific grant resources

**Resource Attribute Changes**
- Warehouse: `warehouse_size` validation stricter
- Database: `data_retention_time_in_days` range updated
- Schema: `is_managed` behavior clarified

### v0.90.x (Legacy)

**Early Grant System Changes**
- Initial work on new grant patterns
- Preparation for v1.0 grant overhaul

### v0.80.x (Legacy)

**Schema Changes**
- `snowflake_user`: Password management changes
- `snowflake_role`: Comment field now required for tracking
- `snowflake_warehouse`: Auto-suspend/resume defaults changed

## Step-by-Step Upgrade Process

### Step 1: Assess Current State

```bash
# List all resources
terraform state list > current_resources.txt

# Check for deprecated resources
grep -E "(database_grant|schema_grant|warehouse_grant)" current_resources.txt
```

### Step 2: Update Provider Version (Incremental)

Edit your `versions.tf` or `main.tf`:

**If upgrading from 0.x to 1.x:**
```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 1.0"  # First upgrade to 1.x
    }
  }
}
```

**If upgrading from 1.x to 2.x:**
```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 2.0"  # Then upgrade to 2.x
    }
  }
}
```

**Current recommended version:**
```hcl
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 2.3"  # Latest with BCR fixes
    }
  }
}
```

**Important**: The recommended approach is to upgrade incrementally through major versions (0.x → 1.x → 2.x). However, you may also consider importing your infrastructure directly to the latest version - see [Alternative: Direct Import to Latest Version](#alternative-direct-import-to-latest-version) below.

### Step 3: Initialize and Plan

```bash
# Reinitialize with new provider version
terraform init -upgrade

# Review the plan
terraform plan -out=upgrade.tfplan

# Save the plan output for review
terraform show upgrade.tfplan > upgrade_plan.txt
```

### Step 4: Address Deprecation Warnings

Review the plan output for warnings like:

```
Warning: Deprecated Resource
The resource type "snowflake_database_grant" is deprecated.
```

### Step 5: Migrate Deprecated Resources

See [Common Migration Scenarios](#common-migration-scenarios) below for specific examples.

### Step 6: Apply Changes

```bash
# Apply the upgrade
terraform apply upgrade.tfplan

# Verify the state
terraform state list
terraform show
```

### Step 7: Validate in Snowflake

```sql
-- Check databases
SHOW DATABASES;

-- Check warehouses
SHOW WAREHOUSES;

-- Check roles and grants
SHOW ROLES;
SHOW GRANTS TO ROLE your_role_name;

-- Check users
SHOW USERS;
```

## Alternative: Direct Import to Latest Version

For teams with existing Snowflake infrastructure, you may consider importing your entire infrastructure directly to the newest provider version (v2.3+) without going through intermediate version bumps. This approach can be more efficient than multiple incremental upgrades.

### When to Use Direct Import

**Good candidates for direct import:**
- You have well-documented Snowflake infrastructure
- Your Terraform state can be rebuilt from scratch
- You want to adopt current best practices immediately
- You're willing to rewrite configurations using modern patterns
- You have a clear inventory of all Snowflake objects

**Not recommended if:**
- You have complex, undocumented infrastructure
- You cannot afford downtime or state inconsistencies
- You have many custom or legacy configurations
- You lack a complete inventory of resources

### Direct Import Process

#### Step 1: Prepare for Import

```bash
# 1. Document your current infrastructure
terraform state list > current_resources.txt
terraform show > current_state.txt

# 2. Export Snowflake objects
# Run these in Snowflake to get current state
snowsql -q "SHOW DATABASES;" -o output_format=csv > databases.csv
snowsql -q "SHOW WAREHOUSES;" -o output_format=csv > warehouses.csv
snowsql -q "SHOW ROLES;" -o output_format=csv > roles.csv
snowsql -q "SHOW GRANTS TO ROLE <role_name>;" -o output_format=csv > grants_<role>.csv

# 3. Backup your current state
cp terraform.tfstate terraform.tfstate.pre-import-backup
```

#### Step 2: Create New Configuration with Latest Provider

Create a new Terraform configuration using v2.3+ patterns:

```hcl
# versions.tf
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 2.3"  # Latest version
    }
  }
}

# main.tf - Use modern resource patterns
resource "snowflake_database" "example" {
  name    = "MY_DATABASE"
  comment = "Imported database"
}

resource "snowflake_warehouse" "example" {
  name           = "MY_WAREHOUSE"
  warehouse_size = "X-SMALL"  # Note: hyphenated format
}

resource "snowflake_role" "example" {
  name    = "MY_ROLE"
  comment = "Imported role"
}

# Use the modern grant resource
resource "snowflake_grant_privileges_to_role" "database_usage" {
  role_name   = snowflake_role.example.name
  privileges  = ["USAGE"]
  on_database = snowflake_database.example.name
}
```

#### Step 3: Initialize with New Provider

```bash
# Initialize with the latest provider
terraform init

# Verify provider version
terraform version
```

#### Step 4: Import Resources

Import each resource using the latest provider's import format:

```bash
# Import databases
terraform import snowflake_database.example "MY_DATABASE"

# Import warehouses
terraform import snowflake_warehouse.example "MY_WAREHOUSE"

# Import roles
terraform import snowflake_role.example "MY_ROLE"

# Import grants (use v2.x import format)
terraform import snowflake_grant_privileges_to_role.database_usage "MY_ROLE|false|USAGE|OnDatabase|MY_DATABASE"
```

#### Step 5: Validate and Reconcile

```bash
# Run plan to see if configuration matches imported state
terraform plan

# If there are differences, adjust your configuration
# Repeat until terraform plan shows no changes
```

#### Step 6: Verify in Snowflake

```sql
-- Verify databases
SHOW DATABASES;

-- Verify warehouses
SHOW WAREHOUSES;

-- Verify roles
SHOW ROLES;

-- Verify grants
SHOW GRANTS TO ROLE MY_ROLE;
```

### Benefits of Direct Import

1. **Skip complex migrations** - Avoid dealing with deprecated resources and intermediate versions
2. **Modern patterns from day one** - Start with current best practices
3. **Cleaner state** - No legacy resource types in your state
4. **Faster overall** - One import process vs. multiple upgrade cycles
5. **Better understanding** - Forces you to understand your current infrastructure

### Considerations

1. **Time investment** - Initial setup takes time to document and import all resources
2. **Risk of missing resources** - Must have complete inventory
3. **Testing required** - Thoroughly test that all resources are correctly imported
4. **Downtime planning** - May need maintenance window for state transition
5. **Team coordination** - Ensure all team members are aware of the change

### Hybrid Approach

You can also use a hybrid approach:
1. Import critical resources directly to v2.3+
2. Use incremental upgrades for complex or risky resources
3. Gradually migrate remaining resources

### Import Helper Script

```bash
#!/bin/bash
# import_to_latest.sh - Helper script for importing to v2.3+

echo "=== Snowflake Terraform Import Helper ==="
echo "This script helps import resources to provider v2.3+"
echo ""

# Function to import database
import_database() {
  local db_name=$1
  echo "Importing database: $db_name"
  terraform import "snowflake_database.${db_name,,}" "$db_name"
}

# Function to import warehouse
import_warehouse() {
  local wh_name=$1
  echo "Importing warehouse: $wh_name"
  terraform import "snowflake_warehouse.${wh_name,,}" "$wh_name"
}

# Function to import role
import_role() {
  local role_name=$1
  echo "Importing role: $role_name"
  terraform import "snowflake_role.${role_name,,}" "$role_name"
}

# Function to import grant
import_grant() {
  local role=$1
  local privilege=$2
  local object_type=$3
  local object_name=$4
  
  echo "Importing grant: $privilege on $object_type $object_name to $role"
  terraform import "snowflake_grant_privileges_to_role.${role,,}_${object_name,,}" \
    "${role}|false|${privilege}|${object_type}|${object_name}"
}

# Example usage
# import_database "MY_DATABASE"
# import_warehouse "MY_WAREHOUSE"
# import_role "MY_ROLE"
# import_grant "MY_ROLE" "USAGE" "OnDatabase" "MY_DATABASE"

echo "Customize this script with your specific resources"
```

## Common Migration Scenarios

### Scenario 1: Migrating Database Grants

**Old Configuration (v0.80.x and earlier):**
```hcl
resource "snowflake_database_grant" "grant" {
  database_name = "MY_DATABASE"
  privilege     = "USAGE"
  roles         = ["MY_ROLE"]
}
```

**New Configuration (v0.90.x+):**
```hcl
resource "snowflake_grant_privileges_to_role" "database_usage" {
  role_name  = "MY_ROLE"
  privileges = ["USAGE"]
  
  on_database = "MY_DATABASE"
}
```

**Migration Steps:**
```bash
# 1. Remove old resource from state
terraform state rm snowflake_database_grant.grant

# 2. Update configuration to new format

# 3. Import the existing grant
terraform import snowflake_grant_privileges_to_role.database_usage "MY_ROLE|false|USAGE|OnDatabase|MY_DATABASE"

# 4. Verify
terraform plan
```

### Scenario 2: Migrating Schema Grants

**Old Configuration:**
```hcl
resource "snowflake_schema_grant" "grant" {
  database_name = "MY_DATABASE"
  schema_name   = "MY_SCHEMA"
  privilege     = "USAGE"
  roles         = ["MY_ROLE"]
}
```

**New Configuration:**
```hcl
resource "snowflake_grant_privileges_to_role" "schema_usage" {
  role_name  = "MY_ROLE"
  privileges = ["USAGE"]
  
  on_schema {
    schema_name = "MY_DATABASE.MY_SCHEMA"
  }
}
```

### Scenario 3: Migrating Warehouse Grants

**Old Configuration:**
```hcl
resource "snowflake_warehouse_grant" "grant" {
  warehouse_name = "MY_WAREHOUSE"
  privilege      = "USAGE"
  roles          = ["MY_ROLE"]
}
```

**New Configuration:**
```hcl
resource "snowflake_grant_privileges_to_role" "warehouse_usage" {
  role_name  = "MY_ROLE"
  privileges = ["USAGE"]
  
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = "MY_WAREHOUSE"
  }
}
```

### Scenario 4: Updating Warehouse Configuration

**Old Configuration:**
```hcl
resource "snowflake_warehouse" "warehouse" {
  name           = "MY_WAREHOUSE"
  warehouse_size = "XSMALL"  # Old format
}
```

**New Configuration:**
```hcl
resource "snowflake_warehouse" "warehouse" {
  name           = "MY_WAREHOUSE"
  warehouse_size = "X-SMALL"  # New format with hyphen
}
```

### Scenario 5: User Password Management

**Old Configuration:**
```hcl
resource "snowflake_user" "user" {
  name     = "MY_USER"
  password = "hardcoded_password"  # Deprecated
}
```

**New Configuration:**
```hcl
resource "snowflake_user" "user" {
  name     = "MY_USER"
  # Password should be managed outside Terraform or use must_change_password
  must_change_password = true
}
```

## Automated Migration Script

Use this helper script to identify resources that need migration:

```bash
#!/bin/bash
# migration_checker.sh

echo "Checking for deprecated resources..."

# Check for old grant resources
echo -e "\n=== Deprecated Grant Resources ==="
terraform state list | grep -E "(database_grant|schema_grant|warehouse_grant|table_grant)" || echo "None found"

# Check for old warehouse size format
echo -e "\n=== Checking Warehouse Sizes ==="
terraform show | grep -i "warehouse_size.*XSMALL\|warehouse_size.*XXSMALL" || echo "No issues found"

# Check for hardcoded passwords
echo -e "\n=== Checking for Hardcoded Passwords ==="
grep -r "password.*=" *.tf | grep -v "must_change_password" | grep -v "#" || echo "No issues found"

# Generate migration report
echo -e "\n=== Migration Report ==="
echo "Total resources: $(terraform state list | wc -l)"
echo "Deprecated grants: $(terraform state list | grep -E '(database_grant|schema_grant|warehouse_grant)' | wc -l)"

echo -e "\nReview complete. Check output above for items requiring migration."
```

Save as `migration_checker.sh` and run:
```bash
chmod +x migration_checker.sh
./migration_checker.sh
```

## Troubleshooting

### Issue: "Error: Invalid provider version"

**Solution:**
```bash
# Clear provider cache
rm -rf .terraform
rm .terraform.lock.hcl

# Reinitialize
terraform init -upgrade
```

### Issue: "Resource not found" after upgrade

**Solution:**
The resource may have been renamed. Check the state:
```bash
terraform state list
terraform state show <resource_name>

# If needed, rename in state
terraform state mv old_resource_name new_resource_name
```

### Issue: "Cycle error" in dependencies

**Solution:**
This often happens with grant resources. Break the cycle:
```bash
# Remove problematic resource from state
terraform state rm problematic_resource

# Reimport after fixing dependencies
terraform import resource_type.name "import_id"
```

### Issue: "Provider configuration has changed"

**Solution:**
```bash
# Reconfigure provider
terraform init -reconfigure

# If using workspaces
terraform workspace select default
terraform init -reconfigure
```

### Issue: Grants not applying correctly

**Solution:**
Ensure proper role hierarchy and dependencies:
```hcl
resource "snowflake_role" "role" {
  name = "MY_ROLE"
}

resource "snowflake_grant_privileges_to_role" "grant" {
  role_name = snowflake_role.role.name  # Use reference
  # ... rest of configuration
  
  depends_on = [snowflake_role.role]
}
```

## Best Practices for Future Upgrades

1. **Pin Provider Versions**: Use `~>` for minor version flexibility
   ```hcl
   version = "~> 0.94.0"  # Allows 0.94.x but not 0.95.0
   ```

2. **Monitor Deprecation Warnings**: Review `terraform plan` output regularly

3. **Use Modules**: Encapsulate common patterns to simplify updates

4. **Document Custom Configurations**: Comment non-standard setups

5. **Automate Testing**: Use Terratest or similar for validation

6. **Subscribe to Updates**: Watch the [provider repository](https://github.com/snowflakedb/terraform-provider-snowflake) for changes

## Additional Resources

- [Snowflake BCR Migration Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md#bundle-2025_04) - Official migration guide for Bundle 2025_04
- [Terraform Snowflake Provider Documentation](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs)
- [Snowflake Terraform Provider GitHub](https://github.com/snowflakedb/terraform-provider-snowflake)
- [Snowflake Terraform Provider Discussions](https://github.com/snowflakedb/terraform-provider-snowflake/discussions)
- [Terraform Upgrade Guide](https://www.terraform.io/upgrade-guides)
- [Snowflake Documentation](https://docs.snowflake.com/)

## Getting Help

If you encounter issues during the upgrade:

1. **Check GitHub Issues**: Search for similar problems in the [provider issues](https://github.com/snowflakedb/terraform-provider-snowflake/issues)
2. **Review Discussions**: Check [GitHub Discussions](https://github.com/snowflakedb/terraform-provider-snowflake/discussions)
3. **Consult Documentation**: Review the latest provider documentation
4. **Contact Support**: Reach out to Snowflake support if needed

## Version History

- **2025-04**: Bundle 2025_04 breaking changes
- **2024-Q4**: v0.94.x release with grant refactoring
- **2024-Q3**: v0.90.x major grant system overhaul
- **2024-Q2**: v0.80.x schema and attribute updates

---

**Note**: Always test upgrades in a non-production environment first. This guide is maintained as a reference and should be used in conjunction with the official Snowflake Terraform provider documentation.

