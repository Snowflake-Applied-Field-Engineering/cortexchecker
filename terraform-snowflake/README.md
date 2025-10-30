# Snowflake Terraform Provider Upgrade Tool

A comprehensive toolkit to help you upgrade your existing Snowflake Terraform configurations from older provider versions to the latest version (v0.94+). This tool is specifically designed for teams who already have Terraform managing their Snowflake infrastructure and need to migrate to newer provider versions.

## Why This Tool?

The Snowflake Terraform provider has undergone significant breaking changes, especially with:
- **Bundle 2025_04** - Major grant system overhaul
- **v0.90.x+** - Deprecated legacy grant resources
- **v0.80.x+** - Resource attribute changes

If you're using provider versions older than v0.90.0, you'll need to migrate your existing Terraform code. This tool helps you:

1. **Identify** what needs to change in your existing configuration
2. **Understand** the breaking changes and new patterns
3. **Migrate** your code with step-by-step instructions
4. **Validate** that your migration was successful

## Quick Start - Assess Your Current Setup

### Step 1: Run the Migration Checker

Copy the `migration_checker.sh` script to your existing Terraform directory and run it:

```bash
# Copy the script to your Terraform directory
cp migration_checker.sh /path/to/your/terraform/directory/
cd /path/to/your/terraform/directory/

# Run the checker
./migration_checker.sh
```

This will scan your existing Terraform configuration and state files to identify:
- Deprecated grant resources that need migration
- Old warehouse size formats
- Hardcoded passwords
- Other compatibility issues

### Step 2: Review Your Migration Path

Based on your current provider version, follow the appropriate upgrade path:

| Current Version | Recommended Path | Complexity | Notes |
|----------------|------------------|------------|-------|
| v0.70.x or older | v0.70 → v0.80 → v0.90 → v1.0 → v2.0+ | Very High | Multiple breaking changes |
| v0.80.x | v0.80 → v0.90 → v1.0 → v2.0+ | High | Grant system overhaul |
| v0.90.x | v0.90 → v1.0 → v2.0+ | Medium | Major version transitions |
| v1.x (1.0-1.9) | v1.x → v2.0+ | Low | Relatively small configuration changes |
| v2.0-2.2 | v2.0-2.2 → v2.3+ | Low | BCR compatibility fixes |
| v2.3+ | Stay current | Low | Keep updating regularly |

**Important**: 
- The recommended approach is incremental upgrades (0.x → 1.x → 2.x)
- Version 1.0+ introduced significant grant system changes
- Version 2.0+ is the current major version
- Version 2.3+ includes BCR bundle compatibility fixes

**Alternative Migration Path**: 
For teams with existing Snowflake infrastructure, consider importing your entire infrastructure directly to the newest provider version (v2.3+) without intermediate version bumps. This approach:
- Skips the complexity of multiple incremental upgrades
- Allows you to start fresh with current best practices
- Works well if your Terraform state can be rebuilt
- See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md#alternative-direct-import-to-latest-version) for detailed instructions

### Step 3: Follow the Upgrade Guide

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for detailed instructions on:
- Backing up your state
- Updating provider versions
- Migrating deprecated resources
- Testing and validation

## What's Included

### 1. Migration Checker Script (`migration_checker.sh`)
Automated tool that analyzes your existing Terraform configuration and identifies:
- Deprecated `snowflake_database_grant` resources
- Deprecated `snowflake_schema_grant` resources
- Deprecated `snowflake_warehouse_grant` resources
- Old warehouse size formats (XSMALL → X-SMALL)
- Security issues (hardcoded passwords)
- Generates actionable recommendations

### 2. Comprehensive Upgrade Guide (`UPGRADE_GUIDE.md`)
Complete documentation covering:
- Pre-upgrade checklist and backups
- Version-by-version breaking changes
- Step-by-step migration process
- State management (remove/import commands)
- Troubleshooting common issues
- Rollback procedures

### 3. Real-World Migration Examples (`MIGRATION_EXAMPLES.md`)
Practical before/after examples for:
- Database grant migrations
- Schema grant migrations
- Warehouse grant migrations
- Table and view grant migrations
- Complete infrastructure migrations
- Testing and validation procedures

### 4. BCR Bundle Guide (`BCR_BUNDLE_GUIDE.md`)
Comprehensive guide for Snowflake Behavior Change Release (BCR) Bundles:
- What BCR Bundles are and why they matter
- Bundle-by-bundle breakdown (2025_03, 2025_04, 2025_05, 2025_06)
- Specific impacts on Terraform resources
- Migration steps for each breaking change
- Testing procedures before enabling bundles

### 5. Reference Configurations
Modern Terraform configurations showing:
- Current best practices (v0.94+)
- Proper grant resource usage
- Recommended patterns and structures

## Prerequisites

- Existing Snowflake Terraform configuration (any version)
- [Terraform](https://www.terraform.io/downloads.html) >= 1.5.0
- Snowflake account with appropriate permissions (ACCOUNTADMIN or SECURITYADMIN role)
- Access to your Terraform state files
- Backup capabilities for your state files

## Common Migration Scenarios

### Scenario 1: You have old grant resources

**Problem**: Your configuration uses deprecated grant resources like:
```hcl
resource "snowflake_database_grant" "grant" {
  database_name = "MY_DATABASE"
  privilege     = "USAGE"
  roles         = ["MY_ROLE"]
}
```

**Solution**: See [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md#grant-migrations) for step-by-step migration to:
```hcl
resource "snowflake_grant_privileges_to_role" "database_usage" {
  role_name  = "MY_ROLE"
  privileges = ["USAGE"]
  on_database = "MY_DATABASE"
}
```

### Scenario 2: Warehouse size format errors

**Problem**: Terraform plan shows errors about warehouse sizes:
```
Error: Invalid warehouse size "XSMALL"
```

**Solution**: Update to hyphenated format:
```hcl
warehouse_size = "X-SMALL"  # Changed from "XSMALL"
```

### Scenario 3: Provider version conflicts

**Problem**: Getting errors after updating provider version

**Solution**: Follow the incremental upgrade path in [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md#step-by-step-upgrade-process)

## Understanding BCR Bundles

Snowflake releases **Behavior Change Release (BCR) Bundles** that contain breaking changes. These changes are eventually enabled by default and cannot be disabled. Our [BCR_BUNDLE_GUIDE.md](BCR_BUNDLE_GUIDE.md) helps you:

- Understand what each bundle changes
- Test bundles before they're enforced
- Migrate your Terraform code to be compatible
- Handle authentication policies, privileges, and resource changes

**Key BCR Bundles:**
- **2025_06**: Authentication policy changes (MFA methods deprecated)
- **2025_05**: Key-pair auth changes, dependency enforcement
- **2025_04**: MFA defaults, stage access requirements
- **2025_03**: Privilege renames, Python package changes

See [BCR_BUNDLE_GUIDE.md](BCR_BUNDLE_GUIDE.md) for detailed migration instructions.

## For Official Documentation

This tool complements the official Snowflake documentation:
- [Snowflake BCR Migration Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md) - Official BCR migration guide
- [Terraform Snowflake Provider Docs](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs) - Latest provider documentation
- [Provider GitHub Repository](https://github.com/snowflakedb/terraform-provider-snowflake) - Issues and discussions
- [Snowflake BCR Bundles](https://docs.snowflake.com/en/release-notes/behavior-changes) - Official BCR bundle documentation

## Step-by-Step Migration Process

### Phase 1: Assessment (5-10 minutes)

1. **Clone this repository**
   ```bash
   git clone https://github.com/Snowflake-Applied-Field-Engineering/terraformupdate.git
   cd terraformupdate
   ```

2. **Copy migration checker to your Terraform directory**
   ```bash
   cp migration_checker.sh /path/to/your/terraform/
   cd /path/to/your/terraform/
   ```

3. **Run the assessment**
   ```bash
   ./migration_checker.sh
   ```

4. **Review the output** - The script will tell you:
   - How many deprecated resources you have
   - What configuration changes are needed
   - Recommended next steps

### Phase 2: Preparation (10-15 minutes)

1. **Backup your state file**
   ```bash
   # Local state
   cp terraform.tfstate terraform.tfstate.backup
   
   # Remote state (example for S3)
   aws s3 cp s3://your-bucket/path/terraform.tfstate ./terraform.tfstate.backup
   ```

2. **Document current state**
   ```bash
   terraform state list > resources_before_migration.txt
   terraform show > state_before_migration.txt
   ```

3. **Export current grants from Snowflake**
   ```bash
   # For each role you manage
   snowsql -q "SHOW GRANTS TO ROLE YOUR_ROLE;" -o output_format=csv > grants_before.csv
   ```

4. **Review the upgrade guide**
   - Read [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md) for your version
   - Check [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md) for similar patterns

### Phase 3: Migration (30-60 minutes)

Follow the detailed instructions in [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md#step-by-step-upgrade-process) which covers:

1. **Update provider version** (incrementally)
2. **Remove deprecated resources from state**
3. **Update configuration files** with new resource types
4. **Import new resources** into state
5. **Validate with terraform plan**
6. **Apply changes**

### Phase 4: Validation (10-15 minutes)

1. **Verify no unexpected changes**
   ```bash
   terraform plan  # Should show no changes
   ```

2. **Compare grants in Snowflake**
   ```bash
   snowsql -q "SHOW GRANTS TO ROLE YOUR_ROLE;" -o output_format=csv > grants_after.csv
   diff grants_before.csv grants_after.csv
   ```

3. **Test functionality**
   - Connect with affected roles
   - Verify database/schema/warehouse access
   - Run sample queries

## Detailed Documentation

## Reference Configurations

The following files provide reference examples of modern Terraform configurations using the latest provider version (v2.3+):

- `examples_main.tf` - Example resource definitions using current best practices
- `examples_variables.tf` - Variable patterns for v2.3+
- `examples_outputs.tf` - Useful outputs for Snowflake resources
- `examples_terraform.tfvars` - Configuration example
- `versions.tf` - Provider version constraints (shows v2.3+ recommended)

These are provided as **reference only** to show you what your migrated code should look like. **Do not replace your existing configuration with these files.** Use them as a guide when updating your own Terraform code.

## Key Breaking Changes to Know

### Grant System Overhaul (v0.90+)

The biggest change is how grants are managed. The old pattern used separate resources for each object type:

**Old (Deprecated):**
- `snowflake_database_grant`
- `snowflake_schema_grant`
- `snowflake_warehouse_grant`
- `snowflake_table_grant`
- `snowflake_view_grant`

**New (Current):**
- `snowflake_grant_privileges_to_role` - Unified grant resource

See [MIGRATION_EXAMPLES.md](MIGRATION_EXAMPLES.md) for detailed before/after examples.

### Warehouse Size Format (v0.80+)

Warehouse sizes now require hyphens:
- Old: `XSMALL`, `XXSMALL`
- New: `X-SMALL`, `XX-SMALL`

### Provider Configuration (v0.90+)

Provider authentication parameter changed:
- Old: `username`
- New: `user`

## Migration Best Practices

1. **Never Skip Versions**: Upgrade incrementally through each major version
2. **Always Backup State**: Before any migration, backup your state file
3. **Test in Non-Production**: Run migration in dev/staging first
4. **Validate Grants**: Compare grants before and after migration
5. **Use the Checker Script**: Run `migration_checker.sh` before starting
6. **Document Your Changes**: Keep notes on what you migrated
7. **Plan Multiple Times**: Run `terraform plan` after each step
8. **One Resource Type at a Time**: Migrate database grants, then schema grants, etc.

## Useful Migration Commands

```bash
# Check what needs migration
./migration_checker.sh

# Backup state
cp terraform.tfstate terraform.tfstate.backup

# List all current resources
terraform state list

# Remove deprecated resource from state
terraform state rm snowflake_database_grant.old_grant

# Import new grant resource
terraform import snowflake_grant_privileges_to_role.new_grant "ROLE|false|false|USAGE|OnDatabase|DB_NAME"

# Validate migration
terraform plan

# Show specific resource
terraform state show snowflake_grant_privileges_to_role.new_grant
```

## Common Migration Errors and Solutions

### Error: "Resource not found"
**Cause**: Resource was removed from state but still exists in Snowflake  
**Solution**: Import the resource back into state with correct format

### Error: "Cycle in dependency graph"
**Cause**: Circular dependencies in grant resources  
**Solution**: Use explicit `depends_on` or break into separate apply steps

### Error: "Invalid provider version"
**Cause**: Trying to skip major versions  
**Solution**: Upgrade incrementally (v0.70 → v0.80 → v0.90 → v0.94)

### Error: "Invalid warehouse size"
**Cause**: Using old format without hyphens  
**Solution**: Change `XSMALL` to `X-SMALL`

See [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md#troubleshooting) for more solutions.

## Getting Help

### If You Get Stuck

1. **Check the migration checker output** - It provides specific recommendations
2. **Review UPGRADE_GUIDE.md** - Detailed troubleshooting section
3. **Look at MIGRATION_EXAMPLES.md** - Find similar scenarios
4. **Search GitHub Issues** - [Provider Issues](https://github.com/snowflakedb/terraform-provider-snowflake/issues)
5. **Join Discussions** - [Provider Discussions](https://github.com/snowflakedb/terraform-provider-snowflake/discussions)

### Support Resources

- **Official BCR Migration Guide**: [Bundle 2025_04 Guide](https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md#bundle-2025_04)
- **Provider Documentation**: [Terraform Registry](https://registry.terraform.io/providers/Snowflake-Labs/snowflake/latest/docs)
- **Snowflake Community**: [community.snowflake.com](https://community.snowflake.com/)

### Migration Support Checklist

Before asking for help, have ready:
- [ ] Output from `migration_checker.sh`
- [ ] Current provider version
- [ ] Target provider version
- [ ] Terraform version (`terraform version`)
- [ ] Specific error messages
- [ ] Relevant configuration snippets (sanitized)

## Success Stories

After successful migration, you should see:
- ✅ `terraform plan` shows no changes
- ✅ All grants verified in Snowflake match expectations
- ✅ No deprecated resource warnings
- ✅ All roles can access their resources
- ✅ Queries run successfully with migrated configuration

## Contributing

Found an issue or have a suggestion? Please open an issue or PR on the [GitHub repository](https://github.com/Snowflake-Applied-Field-Engineering/terraformupdate).

## License

This migration tool is provided as-is to help teams upgrade their Snowflake Terraform configurations.

