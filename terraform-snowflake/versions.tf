# Terraform version constraints
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 2.3"  # Current recommended version with BCR bundle fixes
      
      # Version history:
      # - 2.3.x+: BCR bundle compatibility (SHOW FUNCTIONS/PROCEDURES fixes)
      # - 2.0.x: Major version with breaking changes
      # - 1.0.x: Grant system overhaul
      # - 0.94.x and older: Legacy versions (deprecated)
    }
  }
}

