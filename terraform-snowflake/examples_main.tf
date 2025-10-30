terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.94"
    }
  }

  # Uncomment and configure for remote state management
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "snowflake/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "snowflake" {
  account  = var.snowflake_account
  user     = var.snowflake_user
  password = var.snowflake_password
  role     = var.snowflake_role
  region   = var.snowflake_region
}

# Database Resources
resource "snowflake_database" "databases" {
  for_each = var.databases

  name                        = each.key
  comment                     = each.value.comment
  data_retention_time_in_days = each.value.data_retention_days
}

# Schema Resources
resource "snowflake_schema" "schemas" {
  for_each = var.schemas

  database            = each.value.database
  name                = each.key
  comment             = each.value.comment
  is_transient        = each.value.is_transient
  is_managed          = each.value.is_managed
  data_retention_days = each.value.data_retention_days

  depends_on = [snowflake_database.databases]
}

# Warehouse Resources
resource "snowflake_warehouse" "warehouses" {
  for_each = var.warehouses

  name           = each.key
  comment        = each.value.comment
  warehouse_size = each.value.size
  auto_suspend   = each.value.auto_suspend
  auto_resume    = each.value.auto_resume
  initially_suspended = each.value.initially_suspended
  max_cluster_count   = each.value.max_cluster_count
  min_cluster_count   = each.value.min_cluster_count
  scaling_policy      = each.value.scaling_policy
}

# Role Resources
resource "snowflake_role" "roles" {
  for_each = var.roles

  name    = each.key
  comment = each.value.comment
}

# User Resources
resource "snowflake_user" "users" {
  for_each = var.users

  name         = each.key
  comment      = each.value.comment
  login_name   = each.value.login_name
  display_name = each.value.display_name
  email        = each.value.email
  disabled     = each.value.disabled
  default_warehouse = each.value.default_warehouse
  default_role      = each.value.default_role
  default_namespace = each.value.default_namespace

  depends_on = [
    snowflake_warehouse.warehouses,
    snowflake_role.roles,
    snowflake_database.databases
  ]
}

# Role Grants to Users
resource "snowflake_role_grants" "role_grants" {
  for_each = var.role_grants

  role_name = each.value.role_name
  users     = each.value.users

  depends_on = [
    snowflake_role.roles,
    snowflake_user.users
  ]
}

# Database Grants
resource "snowflake_database_grant" "database_grants" {
  for_each = var.database_grants

  database_name = each.value.database_name
  privilege     = each.value.privilege
  roles         = each.value.roles
  with_grant_option = each.value.with_grant_option

  depends_on = [
    snowflake_database.databases,
    snowflake_role.roles
  ]
}

# Schema Grants
resource "snowflake_schema_grant" "schema_grants" {
  for_each = var.schema_grants

  database_name = each.value.database_name
  schema_name   = each.value.schema_name
  privilege     = each.value.privilege
  roles         = each.value.roles
  with_grant_option = each.value.with_grant_option

  depends_on = [
    snowflake_schema.schemas,
    snowflake_role.roles
  ]
}

# Warehouse Grants
resource "snowflake_warehouse_grant" "warehouse_grants" {
  for_each = var.warehouse_grants

  warehouse_name = each.value.warehouse_name
  privilege      = each.value.privilege
  roles          = each.value.roles
  with_grant_option = each.value.with_grant_option

  depends_on = [
    snowflake_warehouse.warehouses,
    snowflake_role.roles
  ]
}

# Network Policy (Optional)
resource "snowflake_network_policy" "network_policies" {
  for_each = var.network_policies

  name            = each.key
  comment         = each.value.comment
  allowed_ip_list = each.value.allowed_ip_list
  blocked_ip_list = each.value.blocked_ip_list
}

