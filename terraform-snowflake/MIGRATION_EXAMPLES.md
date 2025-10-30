# Terraform Snowflake Provider Migration Examples

This document provides real-world examples of migrating from older Snowflake Terraform provider versions to the latest version (v0.94+). These examples are based on common patterns and the [official BCR Migration Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md#bundle-2025_04).

## Table of Contents

- [Complete Migration Example](#complete-migration-example)
- [Grant Migrations](#grant-migrations)
- [Resource Attribute Updates](#resource-attribute-updates)
- [State Management](#state-management)
- [Testing Your Migration](#testing-your-migration)

## Complete Migration Example

This example shows a complete migration from v0.70.x to v0.94.x.

### Before Migration (v0.70.x)

```hcl
# main.tf (OLD)
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.70"
    }
  }
}

provider "snowflake" {
  account  = var.snowflake_account
  username = var.snowflake_user
  password = var.snowflake_password
  role     = "ACCOUNTADMIN"
}

# Database
resource "snowflake_database" "analytics" {
  name                        = "ANALYTICS_DB"
  comment                     = "Analytics database"
  data_retention_time_in_days = 7
}

# Schema
resource "snowflake_schema" "raw" {
  database = snowflake_database.analytics.name
  name     = "RAW"
  comment  = "Raw data schema"
}

# Warehouse
resource "snowflake_warehouse" "etl" {
  name           = "ETL_WH"
  warehouse_size = "XSMALL"  # OLD FORMAT
  auto_suspend   = 60
  auto_resume    = true
}

# Role
resource "snowflake_role" "analyst" {
  name    = "ANALYST_ROLE"
  comment = "Analyst role"
}

# OLD GRANT STYLE - DEPRECATED
resource "snowflake_database_grant" "analyst_db_usage" {
  database_name = snowflake_database.analytics.name
  privilege     = "USAGE"
  roles         = [snowflake_role.analyst.name]
}

resource "snowflake_schema_grant" "analyst_schema_usage" {
  database_name = snowflake_database.analytics.name
  schema_name   = snowflake_schema.raw.name
  privilege     = "USAGE"
  roles         = [snowflake_role.analyst.name]
}

resource "snowflake_warehouse_grant" "analyst_wh_usage" {
  warehouse_name = snowflake_warehouse.etl.name
  privilege      = "USAGE"
  roles          = [snowflake_role.analyst.name]
}
```

### After Migration (v0.94.x)

```hcl
# main.tf (NEW)
terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.94"
    }
  }
}

provider "snowflake" {
  account  = var.snowflake_account
  user     = var.snowflake_user  # Changed from 'username'
  password = var.snowflake_password
  role     = "ACCOUNTADMIN"
}

# Database (unchanged)
resource "snowflake_database" "analytics" {
  name                        = "ANALYTICS_DB"
  comment                     = "Analytics database"
  data_retention_time_in_days = 7
}

# Schema (unchanged)
resource "snowflake_schema" "raw" {
  database = snowflake_database.analytics.name
  name     = "RAW"
  comment  = "Raw data schema"
}

# Warehouse (updated size format)
resource "snowflake_warehouse" "etl" {
  name           = "ETL_WH"
  warehouse_size = "X-SMALL"  # NEW FORMAT with hyphen
  auto_suspend   = 60
  auto_resume    = true
}

# Role (unchanged)
resource "snowflake_role" "analyst" {
  name    = "ANALYST_ROLE"
  comment = "Analyst role"
}

# NEW GRANT STYLE
resource "snowflake_grant_privileges_to_role" "analyst_db_usage" {
  role_name  = snowflake_role.analyst.name
  privileges = ["USAGE"]
  
  on_database = snowflake_database.analytics.name
}

resource "snowflake_grant_privileges_to_role" "analyst_schema_usage" {
  role_name  = snowflake_role.analyst.name
  privileges = ["USAGE"]
  
  on_schema {
    schema_name = "${snowflake_database.analytics.name}.${snowflake_schema.raw.name}"
  }
}

resource "snowflake_grant_privileges_to_role" "analyst_wh_usage" {
  role_name  = snowflake_role.analyst.name
  privileges = ["USAGE"]
  
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.etl.name
  }
}
```

### Migration Commands

```bash
# Step 1: Backup state
cp terraform.tfstate terraform.tfstate.backup

# Step 2: Update provider version in main.tf to 0.94

# Step 3: Reinitialize
terraform init -upgrade

# Step 4: Remove old grant resources from state
terraform state rm snowflake_database_grant.analyst_db_usage
terraform state rm snowflake_schema_grant.analyst_schema_usage
terraform state rm snowflake_warehouse_grant.analyst_wh_usage

# Step 5: Update configuration files with new grant syntax

# Step 6: Import new grant resources
terraform import snowflake_grant_privileges_to_role.analyst_db_usage "ANALYST_ROLE|false|false|USAGE|OnDatabase|ANALYTICS_DB"
terraform import snowflake_grant_privileges_to_role.analyst_schema_usage "ANALYST_ROLE|false|false|USAGE|OnSchema|ANALYTICS_DB.RAW"
terraform import snowflake_grant_privileges_to_role.analyst_wh_usage "ANALYST_ROLE|false|false|USAGE|OnAccountObject|WAREHOUSE|ETL_WH"

# Step 7: Plan and verify
terraform plan

# Step 8: Apply if plan looks good
terraform apply
```

## Grant Migrations

### Database Grants

#### Multiple Privileges

**Before:**
```hcl
resource "snowflake_database_grant" "usage" {
  database_name = "MY_DB"
  privilege     = "USAGE"
  roles         = ["ROLE1"]
}

resource "snowflake_database_grant" "create_schema" {
  database_name = "MY_DB"
  privilege     = "CREATE SCHEMA"
  roles         = ["ROLE1"]
}
```

**After:**
```hcl
resource "snowflake_grant_privileges_to_role" "db_grants" {
  role_name  = "ROLE1"
  privileges = ["USAGE", "CREATE SCHEMA"]
  
  on_database = "MY_DB"
}
```

#### Multiple Roles

**Before:**
```hcl
resource "snowflake_database_grant" "usage_role1" {
  database_name = "MY_DB"
  privilege     = "USAGE"
  roles         = ["ROLE1"]
}

resource "snowflake_database_grant" "usage_role2" {
  database_name = "MY_DB"
  privilege     = "USAGE"
  roles         = ["ROLE2"]
}
```

**After:**
```hcl
resource "snowflake_grant_privileges_to_role" "db_usage_role1" {
  role_name  = "ROLE1"
  privileges = ["USAGE"]
  
  on_database = "MY_DB"
}

resource "snowflake_grant_privileges_to_role" "db_usage_role2" {
  role_name  = "ROLE2"
  privileges = ["USAGE"]
  
  on_database = "MY_DB"
}
```

### Schema Grants

#### All Schemas in Database

**Before:**
```hcl
resource "snowflake_schema_grant" "all_schemas" {
  database_name = "MY_DB"
  privilege     = "USAGE"
  roles         = ["ANALYST"]
  on_future     = false
  on_all        = true
}
```

**After:**
```hcl
resource "snowflake_grant_privileges_to_role" "all_schemas" {
  role_name  = "ANALYST"
  privileges = ["USAGE"]
  
  on_schema {
    all_schemas_in_database = "MY_DB"
  }
}
```

#### Future Schemas

**Before:**
```hcl
resource "snowflake_schema_grant" "future_schemas" {
  database_name = "MY_DB"
  privilege     = "USAGE"
  roles         = ["ANALYST"]
  on_future     = true
}
```

**After:**
```hcl
resource "snowflake_grant_privileges_to_role" "future_schemas" {
  role_name  = "ANALYST"
  privileges = ["USAGE"]
  
  on_schema {
    future_schemas_in_database = "MY_DB"
  }
}
```

### Table Grants

**Before:**
```hcl
resource "snowflake_table_grant" "select" {
  database_name = "MY_DB"
  schema_name   = "MY_SCHEMA"
  table_name    = "MY_TABLE"
  privilege     = "SELECT"
  roles         = ["ANALYST"]
}
```

**After:**
```hcl
resource "snowflake_grant_privileges_to_role" "table_select" {
  role_name  = "ANALYST"
  privileges = ["SELECT"]
  
  on_schema_object {
    object_type = "TABLE"
    object_name = "MY_DB.MY_SCHEMA.MY_TABLE"
  }
}
```

### View Grants

**Before:**
```hcl
resource "snowflake_view_grant" "select" {
  database_name = "MY_DB"
  schema_name   = "MY_SCHEMA"
  view_name     = "MY_VIEW"
  privilege     = "SELECT"
  roles         = ["ANALYST"]
}
```

**After:**
```hcl
resource "snowflake_grant_privileges_to_role" "view_select" {
  role_name  = "ANALYST"
  privileges = ["SELECT"]
  
  on_schema_object {
    object_type = "VIEW"
    object_name = "MY_DB.MY_SCHEMA.MY_VIEW"
  }
}
```

## Resource Attribute Updates

### Warehouse Size Format

**Before:**
```hcl
resource "snowflake_warehouse" "compute" {
  name           = "COMPUTE_WH"
  warehouse_size = "XSMALL"   # Old format
  # or
  warehouse_size = "XXSMALL"  # Old format
}
```

**After:**
```hcl
resource "snowflake_warehouse" "compute" {
  name           = "COMPUTE_WH"
  warehouse_size = "X-SMALL"   # New format
  # or
  warehouse_size = "XX-SMALL"  # New format
}
```

**All Valid Sizes:**
- `X-SMALL`
- `SMALL`
- `MEDIUM`
- `LARGE`
- `X-LARGE`
- `2X-LARGE`
- `3X-LARGE`
- `4X-LARGE`
- `5X-LARGE`
- `6X-LARGE`

### User Password Management

**Before:**
```hcl
resource "snowflake_user" "analyst" {
  name     = "ANALYST_USER"
  password = "HardcodedPassword123!"  # Not recommended
}
```

**After (Option 1 - Force password change):**
```hcl
resource "snowflake_user" "analyst" {
  name                 = "ANALYST_USER"
  must_change_password = true
}
```

**After (Option 2 - Use variable):**
```hcl
resource "snowflake_user" "analyst" {
  name     = "ANALYST_USER"
  password = var.analyst_password  # From environment variable
}
```

### Schema Attributes

**Before:**
```hcl
resource "snowflake_schema" "data" {
  database = "MY_DB"
  name     = "DATA"
  # Old attribute names
  is_transient = "false"
  is_managed   = "false"
}
```

**After:**
```hcl
resource "snowflake_schema" "data" {
  database = "MY_DB"
  name     = "DATA"
  # New boolean values
  is_transient = false
  is_managed   = false
}
```

## State Management

### Removing Resources from State

```bash
# Remove a single resource
terraform state rm snowflake_database_grant.old_grant

# Remove multiple resources matching a pattern
terraform state list | grep "database_grant" | xargs -I {} terraform state rm {}

# Remove all old grant types
terraform state list | grep -E "(database_grant|schema_grant|warehouse_grant)" | xargs -I {} terraform state rm {}
```

### Importing New Resources

```bash
# Database grant import
terraform import snowflake_grant_privileges_to_role.db_usage \
  "ROLE_NAME|false|false|USAGE|OnDatabase|DATABASE_NAME"

# Schema grant import
terraform import snowflake_grant_privileges_to_role.schema_usage \
  "ROLE_NAME|false|false|USAGE|OnSchema|DATABASE.SCHEMA"

# Warehouse grant import
terraform import snowflake_grant_privileges_to_role.wh_usage \
  "ROLE_NAME|false|false|USAGE|OnAccountObject|WAREHOUSE|WAREHOUSE_NAME"

# Table grant import
terraform import snowflake_grant_privileges_to_role.table_select \
  "ROLE_NAME|false|false|SELECT|OnSchemaObject|TABLE|DATABASE.SCHEMA.TABLE"
```

### Import ID Format

The import ID format for `snowflake_grant_privileges_to_role` is:
```
ROLE_NAME|ALWAYS_APPLY|ALWAYS_APPLY_TRIGGER|PRIVILEGE|ON_TYPE|OBJECT_NAME
```

Where:
- `ROLE_NAME`: The role receiving the grant
- `ALWAYS_APPLY`: Boolean (true/false)
- `ALWAYS_APPLY_TRIGGER`: Boolean (true/false)
- `PRIVILEGE`: The privilege being granted (e.g., USAGE, SELECT)
- `ON_TYPE`: One of: OnDatabase, OnSchema, OnSchemaObject, OnAccountObject
- `OBJECT_NAME`: The fully qualified object name

## Testing Your Migration

### Pre-Migration Checklist

```bash
# 1. Backup state
cp terraform.tfstate terraform.tfstate.pre-migration

# 2. Export current grants from Snowflake
snowsql -q "SHOW GRANTS TO ROLE ANALYST_ROLE;" -o output_format=csv > grants_before.csv

# 3. List all current resources
terraform state list > resources_before.txt

# 4. Create a plan
terraform plan -out=pre-migration.tfplan
terraform show pre-migration.tfplan > pre-migration-plan.txt
```

### Post-Migration Validation

```bash
# 1. Verify state
terraform state list > resources_after.txt
diff resources_before.txt resources_after.txt

# 2. Verify grants in Snowflake
snowsql -q "SHOW GRANTS TO ROLE ANALYST_ROLE;" -o output_format=csv > grants_after.csv
diff grants_before.csv grants_after.csv

# 3. Run plan to ensure no changes
terraform plan

# 4. Test functionality
# Connect as the role and verify access
snowsql -r ANALYST_ROLE -q "USE DATABASE ANALYTICS_DB;"
snowsql -r ANALYST_ROLE -q "USE SCHEMA RAW;"
snowsql -r ANALYST_ROLE -q "USE WAREHOUSE ETL_WH;"
```

### Rollback Procedure

If migration fails:

```bash
# 1. Restore state file
cp terraform.tfstate.pre-migration terraform.tfstate

# 2. Downgrade provider version in configuration

# 3. Reinitialize
terraform init -upgrade

# 4. Verify state
terraform plan
```

## Common Patterns

### Pattern: Role Hierarchy with Grants

**Before:**
```hcl
resource "snowflake_role" "junior_analyst" {
  name = "JUNIOR_ANALYST"
}

resource "snowflake_role" "senior_analyst" {
  name = "SENIOR_ANALYST"
}

resource "snowflake_role_grants" "senior_to_junior" {
  role_name = snowflake_role.junior_analyst.name
  roles     = [snowflake_role.senior_analyst.name]
}

resource "snowflake_database_grant" "junior_usage" {
  database_name = "ANALYTICS_DB"
  privilege     = "USAGE"
  roles         = [snowflake_role.junior_analyst.name]
}
```

**After:**
```hcl
resource "snowflake_role" "junior_analyst" {
  name = "JUNIOR_ANALYST"
}

resource "snowflake_role" "senior_analyst" {
  name = "SENIOR_ANALYST"
}

resource "snowflake_grant_privileges_to_role" "senior_inherits_junior" {
  role_name  = snowflake_role.senior_analyst.name
  privileges = ["USAGE"]  # Inherits junior role
  
  on_account_object {
    object_type = "ROLE"
    object_name = snowflake_role.junior_analyst.name
  }
}

resource "snowflake_grant_privileges_to_role" "junior_db_access" {
  role_name  = snowflake_role.junior_analyst.name
  privileges = ["USAGE"]
  
  on_database = "ANALYTICS_DB"
}
```

### Pattern: Complete Data Pipeline Setup

This example shows a complete ETL pipeline setup with proper grants:

```hcl
# Database
resource "snowflake_database" "etl" {
  name    = "ETL_DB"
  comment = "ETL database"
}

# Schemas
resource "snowflake_schema" "raw" {
  database = snowflake_database.etl.name
  name     = "RAW"
}

resource "snowflake_schema" "staging" {
  database = snowflake_database.etl.name
  name     = "STAGING"
}

# Warehouse
resource "snowflake_warehouse" "etl" {
  name           = "ETL_WH"
  warehouse_size = "MEDIUM"
  auto_suspend   = 300
}

# Role
resource "snowflake_role" "etl_engineer" {
  name = "ETL_ENGINEER"
}

# Database grants
resource "snowflake_grant_privileges_to_role" "etl_db_usage" {
  role_name  = snowflake_role.etl_engineer.name
  privileges = ["USAGE", "CREATE SCHEMA", "MONITOR"]
  on_database = snowflake_database.etl.name
}

# Schema grants - RAW
resource "snowflake_grant_privileges_to_role" "etl_raw_all" {
  role_name  = snowflake_role.etl_engineer.name
  privileges = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE STAGE"]
  
  on_schema {
    schema_name = "${snowflake_database.etl.name}.${snowflake_schema.raw.name}"
  }
}

# Schema grants - STAGING
resource "snowflake_grant_privileges_to_role" "etl_staging_all" {
  role_name  = snowflake_role.etl_engineer.name
  privileges = ["USAGE", "CREATE TABLE", "CREATE VIEW"]
  
  on_schema {
    schema_name = "${snowflake_database.etl.name}.${snowflake_schema.staging.name}"
  }
}

# Warehouse grant
resource "snowflake_grant_privileges_to_role" "etl_wh_operate" {
  role_name  = snowflake_role.etl_engineer.name
  privileges = ["USAGE", "OPERATE"]
  
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = snowflake_warehouse.etl.name
  }
}
```

## Additional Resources

- [Official BCR Migration Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md#bundle-2025_04)
- [Terraform Snowflake Provider Documentation](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs)
- [UPGRADE_GUIDE.md](./UPGRADE_GUIDE.md) - Detailed upgrade instructions
- [Snowflake Access Control Documentation](https://docs.snowflake.com/en/user-guide/security-access-control)

---

**Note**: Always test migrations in a non-production environment first and maintain backups of your state files.

