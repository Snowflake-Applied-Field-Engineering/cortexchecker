# Database Outputs
output "database_names" {
  description = "Names of created databases"
  value       = [for db in snowflake_database.databases : db.name]
}

# Schema Outputs
output "schema_names" {
  description = "Names of created schemas"
  value       = [for schema in snowflake_schema.schemas : schema.name]
}

# Warehouse Outputs
output "warehouse_names" {
  description = "Names of created warehouses"
  value       = [for wh in snowflake_warehouse.warehouses : wh.name]
}

# Role Outputs
output "role_names" {
  description = "Names of created roles"
  value       = [for role in snowflake_role.roles : role.name]
}

# User Outputs
output "user_names" {
  description = "Names of created users"
  value       = [for user in snowflake_user.users : user.name]
}

# Network Policy Outputs
output "network_policy_names" {
  description = "Names of created network policies"
  value       = [for np in snowflake_network_policy.network_policies : np.name]
}

# Summary Output
output "resource_summary" {
  description = "Summary of all created resources"
  value = {
    databases        = length(snowflake_database.databases)
    schemas          = length(snowflake_schema.schemas)
    warehouses       = length(snowflake_warehouse.warehouses)
    roles            = length(snowflake_role.roles)
    users            = length(snowflake_user.users)
    network_policies = length(snowflake_network_policy.network_policies)
  }
}

