# Snowflake Provider Configuration
snowflake_account  = "your-account-identifier"
snowflake_user     = "your-username"
snowflake_password = "your-password"  # Consider using environment variables instead
snowflake_role     = "ACCOUNTADMIN"
snowflake_region   = "us-east-1"

# Databases
databases = {
  "DEV_DB" = {
    comment             = "Development database"
    data_retention_days = 1
  }
  "PROD_DB" = {
    comment             = "Production database"
    data_retention_days = 7
  }
}

# Schemas
schemas = {
  "DEV_SCHEMA" = {
    database            = "DEV_DB"
    comment             = "Development schema"
    is_transient        = false
    is_managed          = false
    data_retention_days = 1
  }
  "PROD_SCHEMA" = {
    database            = "PROD_DB"
    comment             = "Production schema"
    is_transient        = false
    is_managed          = false
    data_retention_days = 7
  }
}

# Warehouses
warehouses = {
  "DEV_WH" = {
    comment             = "Development warehouse"
    size                = "X-SMALL"
    auto_suspend        = 60
    auto_resume         = true
    initially_suspended = true
    max_cluster_count   = 1
    min_cluster_count   = 1
    scaling_policy      = "STANDARD"
  }
  "PROD_WH" = {
    comment             = "Production warehouse"
    size                = "MEDIUM"
    auto_suspend        = 300
    auto_resume         = true
    initially_suspended = false
    max_cluster_count   = 3
    min_cluster_count   = 1
    scaling_policy      = "STANDARD"
  }
}

# Roles
roles = {
  "DEV_ROLE" = {
    comment = "Developer role with access to dev resources"
  }
  "ANALYST_ROLE" = {
    comment = "Analyst role with read access"
  }
  "DATA_ENGINEER_ROLE" = {
    comment = "Data engineer role with write access"
  }
}

# Users
users = {
  "DEV_USER" = {
    comment           = "Development user"
    login_name        = "dev_user"
    display_name      = "Developer User"
    email             = "dev@example.com"
    disabled          = false
    default_warehouse = "DEV_WH"
    default_role      = "DEV_ROLE"
    default_namespace = "DEV_DB.DEV_SCHEMA"
  }
}

# Role Grants
role_grants = {
  "grant_dev_role" = {
    role_name = "DEV_ROLE"
    users     = ["DEV_USER"]
  }
}

# Database Grants
database_grants = {
  "dev_db_usage" = {
    database_name     = "DEV_DB"
    privilege         = "USAGE"
    roles             = ["DEV_ROLE"]
    with_grant_option = false
  }
  "dev_db_create_schema" = {
    database_name     = "DEV_DB"
    privilege         = "CREATE SCHEMA"
    roles             = ["DATA_ENGINEER_ROLE"]
    with_grant_option = false
  }
}

# Schema Grants
schema_grants = {
  "dev_schema_usage" = {
    database_name     = "DEV_DB"
    schema_name       = "DEV_SCHEMA"
    privilege         = "USAGE"
    roles             = ["DEV_ROLE", "ANALYST_ROLE"]
    with_grant_option = false
  }
  "dev_schema_create_table" = {
    database_name     = "DEV_DB"
    schema_name       = "DEV_SCHEMA"
    privilege         = "CREATE TABLE"
    roles             = ["DATA_ENGINEER_ROLE"]
    with_grant_option = false
  }
}

# Warehouse Grants
warehouse_grants = {
  "dev_wh_usage" = {
    warehouse_name    = "DEV_WH"
    privilege         = "USAGE"
    roles             = ["DEV_ROLE"]
    with_grant_option = false
  }
  "prod_wh_usage" = {
    warehouse_name    = "PROD_WH"
    privilege         = "USAGE"
    roles             = ["DATA_ENGINEER_ROLE"]
    with_grant_option = false
  }
}

# Network Policies (Optional)
network_policies = {
  # "office_policy" = {
  #   comment         = "Allow access from office IPs only"
  #   allowed_ip_list = ["203.0.113.0/24", "198.51.100.0/24"]
  #   blocked_ip_list = []
  # }
}

