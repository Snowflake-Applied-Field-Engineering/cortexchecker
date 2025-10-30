#!/bin/bash

# Snowflake Terraform Provider Migration Checker
# This script helps identify resources that need migration when upgrading
# the Snowflake Terraform provider to newer versions

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Snowflake Terraform Migration Checker${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}Error: Terraform is not installed${NC}"
    exit 1
fi

# Check if we're in a terraform directory
if [ ! -f "main.tf" ] && [ ! -f "*.tf" ]; then
    echo -e "${RED}Error: No Terraform files found in current directory${NC}"
    exit 1
fi

# Initialize counters
deprecated_grants=0
deprecated_resources=0
warnings=0

# Check current provider version
echo -e "${BLUE}=== Current Provider Configuration ===${NC}"
if grep -q "Snowflake-Labs/snowflake" *.tf 2>/dev/null; then
    current_version=$(grep -A 2 "Snowflake-Labs/snowflake" *.tf | grep "version" | head -1 | awk -F'"' '{print $2}')
    echo -e "Current version constraint: ${GREEN}${current_version}${NC}"
else
    echo -e "${YELLOW}Warning: Could not find Snowflake provider configuration${NC}"
fi

# Check if state file exists
if [ ! -f "terraform.tfstate" ] && [ -z "$TF_WORKSPACE" ]; then
    echo -e "\n${YELLOW}Warning: No terraform.tfstate file found. Run 'terraform init' first.${NC}"
    echo -e "${YELLOW}Checking configuration files only...${NC}\n"
    STATE_EXISTS=false
else
    STATE_EXISTS=true
fi

# Check for deprecated grant resources in state
if [ "$STATE_EXISTS" = true ]; then
    echo -e "\n${BLUE}=== Checking State for Deprecated Resources ===${NC}"
    
    deprecated_db_grants=$(terraform state list 2>/dev/null | grep "snowflake_database_grant" | wc -l | tr -d ' ')
    deprecated_schema_grants=$(terraform state list 2>/dev/null | grep "snowflake_schema_grant" | wc -l | tr -d ' ')
    deprecated_wh_grants=$(terraform state list 2>/dev/null | grep "snowflake_warehouse_grant" | wc -l | tr -d ' ')
    deprecated_table_grants=$(terraform state list 2>/dev/null | grep "snowflake_table_grant" | wc -l | tr -d ' ')
    deprecated_role_grants=$(terraform state list 2>/dev/null | grep "snowflake_role_grants\." | wc -l | tr -d ' ')
    
    deprecated_grants=$((deprecated_db_grants + deprecated_schema_grants + deprecated_wh_grants + deprecated_table_grants + deprecated_role_grants))
    
    if [ $deprecated_db_grants -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $deprecated_db_grants database_grant resources (deprecated)${NC}"
        terraform state list 2>/dev/null | grep "snowflake_database_grant" | sed 's/^/  - /'
    fi
    
    if [ $deprecated_schema_grants -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $deprecated_schema_grants schema_grant resources (deprecated)${NC}"
        terraform state list 2>/dev/null | grep "snowflake_schema_grant" | sed 's/^/  - /'
    fi
    
    if [ $deprecated_wh_grants -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $deprecated_wh_grants warehouse_grant resources (deprecated)${NC}"
        terraform state list 2>/dev/null | grep "snowflake_warehouse_grant" | sed 's/^/  - /'
    fi
    
    if [ $deprecated_table_grants -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $deprecated_table_grants table_grant resources (deprecated)${NC}"
        terraform state list 2>/dev/null | grep "snowflake_table_grant" | sed 's/^/  - /'
    fi
    
    if [ $deprecated_role_grants -gt 0 ]; then
        echo -e "${YELLOW}⚠ Found $deprecated_role_grants role_grants resources (may need review)${NC}"
        terraform state list 2>/dev/null | grep "snowflake_role_grants\." | sed 's/^/  - /'
    fi
    
    if [ $deprecated_grants -eq 0 ]; then
        echo -e "${GREEN}✓ No deprecated grant resources found in state${NC}"
    fi
fi

# Check configuration files for deprecated patterns
echo -e "\n${BLUE}=== Checking Configuration Files ===${NC}"

# Check for old grant resources in .tf files
if grep -r "resource.*snowflake_database_grant" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found snowflake_database_grant in configuration files${NC}"
    grep -n "resource.*snowflake_database_grant" *.tf 2>/dev/null | grep -v "^#" | sed 's/^/  /'
    ((warnings++))
fi

if grep -r "resource.*snowflake_schema_grant" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found snowflake_schema_grant in configuration files${NC}"
    grep -n "resource.*snowflake_schema_grant" *.tf 2>/dev/null | grep -v "^#" | sed 's/^/  /'
    ((warnings++))
fi

if grep -r "resource.*snowflake_warehouse_grant" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found snowflake_warehouse_grant in configuration files${NC}"
    grep -n "resource.*snowflake_warehouse_grant" *.tf 2>/dev/null | grep -v "^#" | sed 's/^/  /'
    ((warnings++))
fi

# Check for old warehouse size format
echo -e "\n${BLUE}=== Checking Warehouse Configurations ===${NC}"
if grep -r "warehouse_size.*=.*\"XSMALL\"" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found old warehouse size format 'XSMALL' (should be 'X-SMALL')${NC}"
    grep -n "warehouse_size.*=.*\"XSMALL\"" *.tf 2>/dev/null | grep -v "^#" | sed 's/^/  /'
    ((warnings++))
fi

if grep -r "warehouse_size.*=.*\"XXSMALL\"" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found old warehouse size format 'XXSMALL' (should be 'XX-SMALL')${NC}"
    grep -n "warehouse_size.*=.*\"XXSMALL\"" *.tf 2>/dev/null | grep -v "^#" | sed 's/^/  /'
    ((warnings++))
fi

if [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ Warehouse configurations look good${NC}"
fi

# Check for hardcoded passwords
echo -e "\n${BLUE}=== Checking Security Configurations ===${NC}"
if grep -r "password.*=.*\".*\"" *.tf 2>/dev/null | grep -v "must_change_password" | grep -v "^#" | grep -v "snowflake_password" > /dev/null; then
    echo -e "${YELLOW}⚠ Found potential hardcoded passwords${NC}"
    echo -e "${YELLOW}  Consider using environment variables or must_change_password${NC}"
    ((warnings++))
else
    echo -e "${GREEN}✓ No hardcoded passwords detected${NC}"
fi

# Check for BCR Bundle related issues
echo -e "\n${BLUE}=== Checking for BCR Bundle Compatibility Issues ===${NC}"

# Check for authentication_policy with mfa_authentication_methods (BCR 2025_06)
if grep -r "resource.*snowflake_authentication_policy" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    if grep -r "mfa_authentication_methods" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
        echo -e "${YELLOW}⚠ Found authentication_policy with mfa_authentication_methods${NC}"
        echo -e "${YELLOW}  This field is deprecated in BCR Bundle 2025_06${NC}"
        echo -e "${YELLOW}  See BCR_BUNDLE_GUIDE.md for migration steps${NC}"
        ((warnings++))
    fi
fi

# Check for CREATE DATA EXCHANGE LISTING privilege (BCR 2025_03)
if grep -r "CREATE DATA EXCHANGE LISTING" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found 'CREATE DATA EXCHANGE LISTING' privilege${NC}"
    echo -e "${YELLOW}  This was renamed to 'CREATE LISTING' in BCR Bundle 2025_03${NC}"
    grep -n "CREATE DATA EXCHANGE LISTING" *.tf 2>/dev/null | grep -v "^#" | sed 's/^/  /'
    ((warnings++))
fi

# Check for Python procedures/functions without explicit psutil (BCR 2025_03)
if grep -r "resource.*snowflake_procedure_python\|resource.*snowflake_function_python" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found Python UDF/procedures${NC}"
    echo -e "${YELLOW}  BCR Bundle 2025_03 removes implicit psutil injection${NC}"
    echo -e "${YELLOW}  Ensure psutil is explicitly listed in packages if needed${NC}"
    ((warnings++))
fi

# Check for external_table resources (BCR 2025_04)
if grep -r "resource.*snowflake_external_table" *.tf 2>/dev/null | grep -v "^#" > /dev/null; then
    echo -e "${YELLOW}⚠ Found external_table resources${NC}"
    echo -e "${YELLOW}  BCR Bundle 2025_04 requires USAGE privilege on stages${NC}"
    echo -e "${YELLOW}  Ensure your role has USAGE on referenced stages${NC}"
    ((warnings++))
fi

if [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ No BCR Bundle compatibility issues detected${NC}"
fi

# Check for new grant resources
echo -e "\n${BLUE}=== Checking for New Grant Resources ===${NC}"
new_grants=$(grep -r "snowflake_grant_privileges_to_role" *.tf 2>/dev/null | grep -v "^#" | wc -l | tr -d ' ')
if [ $new_grants -gt 0 ]; then
    echo -e "${GREEN}✓ Found $new_grants new-style grant resources${NC}"
else
    if [ $deprecated_grants -gt 0 ] || [ $warnings -gt 0 ]; then
        echo -e "${YELLOW}⚠ No new-style grant resources found. Consider migrating.${NC}"
    fi
fi

# Generate summary report
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Migration Summary${NC}"
echo -e "${BLUE}========================================${NC}"

if [ "$STATE_EXISTS" = true ]; then
    total_resources=$(terraform state list 2>/dev/null | wc -l | tr -d ' ')
    echo -e "Total resources in state: ${total_resources}"
    echo -e "Deprecated grant resources: ${deprecated_grants}"
fi

echo -e "Configuration warnings: ${warnings}"

# Provide recommendations
echo -e "\n${BLUE}=== Recommendations ===${NC}"

if [ $deprecated_grants -gt 0 ] || [ $warnings -gt 0 ]; then
    echo -e "${YELLOW}Action Required:${NC}"
    echo -e "1. Review the UPGRADE_GUIDE.md for detailed migration instructions"
    echo -e "2. Backup your state file before making changes"
    echo -e "3. Test migrations in a non-production environment first"
    echo -e "4. Use 'terraform state rm' and 'terraform import' for grant migrations"
    echo -e "\n${YELLOW}Suggested next steps:${NC}"
    echo -e "  terraform plan -out=migration.tfplan"
    echo -e "  # Review the plan carefully"
    echo -e "  terraform show migration.tfplan > migration_plan.txt"
else
    echo -e "${GREEN}✓ Your configuration appears to be up-to-date!${NC}"
    echo -e "  No immediate migration actions required."
fi

# Check for upgrade guide
echo -e "\n${BLUE}=== Documentation ===${NC}"
docs_found=0
if [ -f "UPGRADE_GUIDE.md" ]; then
    echo -e "${GREEN}✓ UPGRADE_GUIDE.md found${NC}"
    ((docs_found++))
fi
if [ -f "BCR_BUNDLE_GUIDE.md" ]; then
    echo -e "${GREEN}✓ BCR_BUNDLE_GUIDE.md found${NC}"
    ((docs_found++))
fi
if [ -f "MIGRATION_EXAMPLES.md" ]; then
    echo -e "${GREEN}✓ MIGRATION_EXAMPLES.md found${NC}"
    ((docs_found++))
fi

if [ $docs_found -eq 0 ]; then
    echo -e "${YELLOW}⚠ No migration guides found in current directory${NC}"
    echo -e "${YELLOW}  Consider downloading from: https://github.com/Snowflake-Applied-Field-Engineering/terraformupdate${NC}"
fi

echo -e "\n${BLUE}For detailed migration instructions, see:${NC}"
echo -e "  - Provider Version Upgrade: ./UPGRADE_GUIDE.md"
echo -e "  - BCR Bundle Changes: ./BCR_BUNDLE_GUIDE.md"
echo -e "  - Migration Examples: ./MIGRATION_EXAMPLES.md"
echo -e "  - Official BCR Guide: https://github.com/snowflakedb/terraform-provider-snowflake/blob/main/SNOWFLAKE_BCR_MIGRATION_GUIDE.md"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}Migration check complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Exit with appropriate code
if [ $deprecated_grants -gt 0 ] || [ $warnings -gt 0 ]; then
    exit 1
else
    exit 0
fi

