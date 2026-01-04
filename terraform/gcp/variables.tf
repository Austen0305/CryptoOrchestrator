# ==========================================
# GCP Terraform Variables
# ==========================================

variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP Region (e.g., us-central1)"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

# ==========================================
# Database Configuration
# ==========================================

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"  # Free tier: db-f1-micro
  
  # Production tiers: db-n1-standard-1, db-n1-standard-2, etc.
}

variable "db_availability_type" {
  description = "Database availability type"
  type        = string
  default     = "ZONAL"  # Use REGIONAL for high availability
  
  validation {
    condition     = contains(["ZONAL", "REGIONAL"], var.db_availability_type)
    error_message = "Availability type must be ZONAL or REGIONAL."
  }
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = "crypto_user"
  sensitive   = true
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

# ==========================================
# Redis Configuration
# ==========================================

variable "redis_tier" {
  description = "Redis instance tier"
  type        = string
  default     = "BASIC"  # Use STANDARD_HA for high availability
  
  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be BASIC or STANDARD_HA."
  }
}

variable "redis_memory_size" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1  # Free tier: 1GB
}

# ==========================================
# Cloud Run Configuration
# ==========================================

variable "container_image" {
  description = "Container image URL (e.g., gcr.io/project-id/cryptoorchestrator:latest)"
  type        = string
}

variable "cloud_run_cpu_limit" {
  description = "Cloud Run CPU limit"
  type        = string
  default     = "2"
}

variable "cloud_run_memory_limit" {
  description = "Cloud Run memory limit"
  type        = string
  default     = "2Gi"
}

variable "cloud_run_concurrency" {
  description = "Cloud Run container concurrency"
  type        = number
  default     = 80
}

variable "cloud_run_timeout" {
  description = "Cloud Run request timeout in seconds"
  type        = number
  default     = 300
}

variable "cloud_run_min_instances" {
  description = "Minimum Cloud Run instances (0 for scale-to-zero)"
  type        = string
  default     = "0"
}

variable "cloud_run_max_instances" {
  description = "Maximum Cloud Run instances"
  type        = string
  default     = "10"
}

# ==========================================
# Security
# ==========================================

variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "exchange_key_encryption_key" {
  description = "Exchange key encryption key"
  type        = string
  sensitive   = true
}

# ==========================================
# Additional Environment Variables
# ==========================================

variable "additional_env_vars" {
  description = "Additional environment variables for Cloud Run"
  type        = map(string)
  default     = {}
}
