# Provider Configuration Variables
variable "snowflake_account" {
  description = "Snowflake account identifier"
  type        = string
}

variable "snowflake_user" {
  description = "Snowflake user for authentication"
  type        = string
}

variable "snowflake_password" {
  description = "Snowflake password for authentication"
  type        = string
  sensitive   = true
}

variable "snowflake_role" {
  description = "Snowflake role to use for operations"
  type        = string
  default     = "ACCOUNTADMIN"
}

variable "snowflake_region" {
  description = "Snowflake region"
  type        = string
  default     = "us-east-1"
}

# Database Variables
variable "databases" {
  description = "Map of databases to create"
  type = map(object({
    comment              = string
    data_retention_days  = number
  }))
  default = {}
}

# Schema Variables
variable "schemas" {
  description = "Map of schemas to create"
  type = map(object({
    database            = string
    comment             = string
    is_transient        = bool
    is_managed          = bool
    data_retention_days = number
  }))
  default = {}
}

# Warehouse Variables
variable "warehouses" {
  description = "Map of warehouses to create"
  type = map(object({
    comment             = string
    size                = string
    auto_suspend        = number
    auto_resume         = bool
    initially_suspended = bool
    max_cluster_count   = number
    min_cluster_count   = number
    scaling_policy      = string
  }))
  default = {}
}

# Role Variables
variable "roles" {
  description = "Map of roles to create"
  type = map(object({
    comment = string
  }))
  default = {}
}

# User Variables
variable "users" {
  description = "Map of users to create"
  type = map(object({
    comment           = string
    login_name        = string
    display_name      = string
    email             = string
    disabled          = bool
    default_warehouse = string
    default_role      = string
    default_namespace = string
  }))
  default = {}
}

# Role Grant Variables
variable "role_grants" {
  description = "Map of role grants to users"
  type = map(object({
    role_name = string
    users     = list(string)
  }))
  default = {}
}

# Database Grant Variables
variable "database_grants" {
  description = "Map of database grants"
  type = map(object({
    database_name     = string
    privilege         = string
    roles             = list(string)
    with_grant_option = bool
  }))
  default = {}
}

# Schema Grant Variables
variable "schema_grants" {
  description = "Map of schema grants"
  type = map(object({
    database_name     = string
    schema_name       = string
    privilege         = string
    roles             = list(string)
    with_grant_option = bool
  }))
  default = {}
}

# Warehouse Grant Variables
variable "warehouse_grants" {
  description = "Map of warehouse grants"
  type = map(object({
    warehouse_name    = string
    privilege         = string
    roles             = list(string)
    with_grant_option = bool
  }))
  default = {}
}

# Network Policy Variables
variable "network_policies" {
  description = "Map of network policies"
  type = map(object({
    comment         = string
    allowed_ip_list = list(string)
    blocked_ip_list = list(string)
  }))
  default = {}
}

