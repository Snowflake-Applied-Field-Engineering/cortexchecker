# Snowflake BCR Bundle Migration Guide

This document helps you understand and migrate your Terraform configuration to maintain compatibility with [Snowflake BCR Bundles](https://docs.snowflake.com/en/release-notes/behavior-changes) (Behavior Change Release).

## What are BCR Bundles?

Snowflake BCR Bundles are collections of breaking changes that are eventually enabled by default. According to the [Bundle Lifecycle](https://docs.snowflake.com/en/release-notes/intro-bcr-releases#bundle-lifecycle), these changes will be enabled without the possibility to disable them, so it's important to prepare beforehand.

## Testing BCR Bundles

You can test new behavior before it's enabled by default:

```sql
-- Enable a bundle for testing
SELECT SYSTEM$ENABLE_BEHAVIOR_CHANGE_BUNDLE('2025_04');

-- Disable a bundle after testing
SELECT SYSTEM$DISABLE_BEHAVIOR_CHANGE_BUNDLE('2025_04');
```

## Important Notes

- Always use the latest version of the provider ([new features and fixes policy](https://docs.snowflake.com/en/user-guide/terraform#new-features-and-fixes))
- Follow the [provider migration guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/MIGRATION_GUIDE.md) when upgrading
- Only changes affecting the Terraform provider are listed here
- For the full list of changes, see [Snowflake BCR Bundle documentation](https://docs.snowflake.com/en/release-notes/behavior-changes)
- The `snowflake_execute` resource is not covered here - you must check SQL commands yourself

---

## [Unbundled Changes](https://docs.snowflake.com/en/release-notes/bcr-bundles/un-bundled/unbundled-behavior-changes)

### Argument Output Changes for SHOW FUNCTIONS and SHOW PROCEDURES

> **IMPORTANT**: This change has been rolled back from BCR 2025_03.

**Impact**: Changed format in `Arguments` column from `SHOW FUNCTIONS/PROCEDURES` output breaks provider parsing:
- [`snowflake_functions`](https://registry.terraform.io/providers/snowflakedb/snowflake/2.2.0/docs/data-sources/functions) and [`snowflake_procedures`](https://registry.terraform.io/providers/snowflakedb/snowflake/2.2.0/docs/data-sources/procedures) data sources become inoperable
- Function and procedure resources fail to read state, causing removal from Terraform state

**Issues**: [#3822](https://github.com/snowflakedb/terraform-provider-snowflake/issues/3822), [#3823](https://github.com/snowflakedb/terraform-provider-snowflake/issues/3823)

**Solution**:
1. Upgrade to provider version **2.3.0** (or **1.2.3** for backport)
2. Data sources work automatically after upgrade
3. If resources were removed from state:
   - Check with `terraform state list`
   - Reimport them following the [resource migration guide](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs/guides/resource_migration)
4. If resources still in state, they work automatically after upgrade

**Reference**: [BCR-1944](https://docs.snowflake.com/release-notes/bcr-bundles/un-bundled/bcr-1944)

---

## [Bundle 2025_06](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_06_bundle)

### Changes in Authentication Policies

> **IMPORTANT**: [BCR-2086](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_06/bcr-2086) was rolled back from 2025_04 and moved to 2025_06.

> **IMPORTANT**: Not yet addressed in the provider. Use the [execute](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs/resources/execute) resource as a workaround.

**Changes**:
1. `MFA_AUTHENTICATION_METHODS` property is **deprecated** - setting it returns an error
2. New property: `ENFORCE_MFA_ON_EXTERNAL_AUTHENTICATION` (coming in future provider versions)
3. `MFA_ENROLLMENT` allowed values changed:
   - Removed: `OPTIONAL`
   - Added: `REQUIRED_PASSWORD_ONLY`, `REQUIRED_SNOWFLAKE_UI_PASSWORD_ONLY`

**Impact**: `authentication_policy` resource with `mfa_authentication_methods` field will error

**Workaround**:
```bash
# 1. Disable the 2025_06 bundle
SELECT SYSTEM$DISABLE_BEHAVIOR_CHANGE_BUNDLE('2025_06');

# 2. Remove mfa_authentication_methods from your Terraform config

# 3. Enable the 2025_06 bundle
SELECT SYSTEM$ENABLE_BEHAVIOR_CHANGE_BUNDLE('2025_06');

# 4. If you get non-empty plan, use ignore_changes
```

```hcl
resource "snowflake_authentication_policy" "example" {
  # ... other config ...
  
  lifecycle {
    ignore_changes = [mfa_authentication_methods]
  }
}
```

**References**: [BCR-2086](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_06/bcr-2086), [BCR-2097](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_06/bcr-2097)

### Snowflake OAuth Authentication: Network Policy Changes

**Impact**: Modifies authentication behavior with active network policies

**Action Required**: Verify your network policy configuration allows provider connections after enabling this change

**New Feature**: Network policies can now be assigned to External OAuth integrations

**Note**: Setting `network_policy` field in `external_oauth_integration` resource not yet supported. Use the [execute](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs/resources/execute) resource as a workaround.

**Reference**: [BCR-2094](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_06/bcr-2094)

### Snowpark Container Services: Job Service Retention Time Increase

**Change**: Job service retention increased from 7 days to 14 days after completion

**Impact**: Minimal - the `job_service` resource forces `ASYNC` option

**Action**: Optionally manually drop completed jobs if needed

**Reference**: [BCR-2093](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_06/bcr-2093)

---

## [Bundle 2025_05](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_05_bundle)

### Key-Pair Authentication for Google Cloud (us-central1 Region)

**Change**: Key-pair authentication now requires using only the account locator without additional segments

**Before**: Account locator with additional segments was supported in us-central1
**After**: Must use only account locator (applies to all cloud platforms and regions)

**Action**: Review your [Authentication methods](https://registry.terraform.io/providers/snowflakedb/snowflake/latest/docs/guides/authentication_methods) configuration

**Reference**: [BCR-2055](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_05/bcr-2055)

### File Formats and Stages: Enforce Dependency Checks

**Change**: Cannot drop/recreate file formats or stages with dependent external tables

**Restrictions**:
- Can't drop file format with dependent external tables
- Can't drop stage with dependent external tables
- Can't alter stage location with dependent external tables

**Action**: Drop dependent external tables first before modifying file formats or stages

**Reference**: [BCR-1989](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_05/bcr-1989)

---

## [Bundle 2025_04](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_04_bundle)

### MFA_AUTHENTICATION_METHODS Default Value Change

**Change**: Default value changed from `[PASSWORD, SAML]` to `[PASSWORD]` only

**Impact**: May cause permadiff on optional `mfa_authentication_methods` field in `authentication_policy` resource

**Solution** (choose one):

**Option 1 - Specify explicitly:**
```hcl
resource "snowflake_authentication_policy" "example" {
  name                      = "MY_POLICY"
  mfa_authentication_methods = ["PASSWORD"]  # Explicitly set
  # ... other config ...
}
```

**Option 2 - Ignore changes:**
```hcl
resource "snowflake_authentication_policy" "example" {
  name = "MY_POLICY"
  # ... other config ...
  
  lifecycle {
    ignore_changes = [mfa_authentication_methods]
  }
}
```

**Note**: This resource is in preview and will be reworked with improved default value handling

**Reference**: [BCR-1971](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_04/bcr-1971)

### Primary Role Requires Stage Access for External Tables

**Change**: Creating external tables now requires primary role to have `USAGE` privilege on referenced stage

**Action Required**: Grant `USAGE` privilege on relevant stages to your connection role

```sql
-- Example grant
GRANT USAGE ON STAGE my_stage TO ROLE my_terraform_role;
```

**Impact**: `snowflake_external_table` resource creation will fail without proper stage access

**Reference**: [BCR-1993](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_04/bcr-1993)

---

## [Bundle 2025_03](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03_bundle)

### CREATE DATA EXCHANGE LISTING Privilege Rename

**Change**: `CREATE DATA EXCHANGE LISTING` privilege renamed to `CREATE LISTING`

**Impact**: Affects privilege-granting resources like `snowflake_grant_privileges_to_account_role`

**Migration Steps**:

```bash
# 1. Remove the resource from state
terraform state rm snowflake_grant_privileges_to_account_role.old_listing_grant

# 2. Update your Terraform config
```

```hcl
# OLD
resource "snowflake_grant_privileges_to_account_role" "listing" {
  privileges        = ["CREATE DATA EXCHANGE LISTING"]
  account_role_name = "MY_ROLE"
  on_account        = true
}

# NEW
resource "snowflake_grant_privileges_to_account_role" "listing" {
  privileges        = ["CREATE LISTING"]  # Updated privilege name
  account_role_name = "MY_ROLE"
  on_account        = true
}
```

```bash
# 3. Re-import with new privilege name
terraform import snowflake_grant_privileges_to_account_role.listing \
  "MY_ROLE|false|false|CREATE LISTING|OnAccount"
```

**Reference**: [BCR-1926](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03/bcr-1926)

### New Maximum Size Limits for Database Objects

**Change**: Max sizes for `VARCHAR` and `BINARY` data types increased

**Impact**: Provider continues using old defaults (16MB for VARCHAR, 8MB for BINARY) when size not specified

**Action**: If you want to use larger sizes after enabling the bundle, specify them explicitly

```hcl
# Example: Using new larger size
resource "snowflake_table" "example" {
  # ...
  column {
    name = "large_text"
    type = "VARCHAR(32000000)"  # Explicitly specify larger size
  }
}
```

**Note**: Default values may change in future provider versions

**Reference**: [BCR-1942](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03/bcr-1942)

### Python UDFs: Stop Implicit psutil Package Injection

**Change**: `psutil` package no longer automatically injected into Python UDFs and stored procedures

**Action Required**: Explicitly add `psutil` to your package list

**Before** (implicit):
```hcl
resource "snowflake_procedure_python" "test" {
  # psutil was automatically available
  # ... other config ...
}
```

**After** (explicit):
```hcl
resource "snowflake_procedure_python" "test" {
  packages = ["psutil==5.9.0"]  # Must explicitly include
  # ... other config ...
}
```

**Also applies to**:
- `snowflake_function_python`
- Any Python UDFs

**Reference**: [BCR-1948](https://docs.snowflake.com/en/release-notes/bcr-bundles/2025_03/bcr-1948)

---

## Migration Workflow

### Before Enabling a Bundle

1. **Review this guide** for changes affecting your resources
2. **Test in non-production** using `SYSTEM$ENABLE_BEHAVIOR_CHANGE_BUNDLE`
3. **Update provider** to latest version
4. **Run migration checker** from our upgrade tool
5. **Update configurations** as needed
6. **Test thoroughly** with `terraform plan`

### Testing a Bundle

```sql
-- Enable for testing
SELECT SYSTEM$ENABLE_BEHAVIOR_CHANGE_BUNDLE('2025_04');

-- Run your Terraform operations
-- terraform plan
-- terraform apply

-- Verify everything works

-- Disable if issues found
SELECT SYSTEM$DISABLE_BEHAVIOR_CHANGE_BUNDLE('2025_04');
```

### After Enabling a Bundle

1. **Monitor for errors** in Terraform operations
2. **Check state consistency** with `terraform state list`
3. **Validate grants** in Snowflake match expectations
4. **Document changes** made to your configuration

## Getting Help

- **Official BCR Guide**: [Snowflake BCR Migration Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md)
- **Provider Issues**: [GitHub Issues](https://github.com/snowflakedb/terraform-provider-snowflake/issues)
- **Provider Discussions**: [GitHub Discussions](https://github.com/snowflakedb/terraform-provider-snowflake/discussions)
- **Snowflake Docs**: [BCR Bundle Documentation](https://docs.snowflake.com/en/release-notes/behavior-changes)

## Quick Reference

| Bundle | Key Changes | Action Required |
|--------|-------------|-----------------|
| 2025_06 | Auth policy changes | Use workaround or wait for provider update |
| 2025_05 | Key-pair auth, dependency checks | Update auth config, manage dependencies |
| 2025_04 | MFA defaults, stage access | Set explicit values, grant stage access |
| 2025_03 | Privilege rename, psutil | Update privilege names, add explicit packages |

---

**Last Updated**: Based on official Snowflake BCR Migration Guide  
**Source**: [GitHub - Snowflake Terraform Provider](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md)

