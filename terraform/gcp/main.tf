# ==========================================
# Google Cloud Platform Terraform Configuration
# ==========================================
# Deploys CryptoOrchestrator to GCP Cloud Run
# ==========================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }
  
  backend "gcs" {
    bucket = "cryptoorchestrator-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ==========================================
# Cloud SQL (PostgreSQL) Instance
# ==========================================

resource "google_sql_database_instance" "postgres" {
  name             = "cryptoorchestrator-db"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  
  settings {
    tier              = var.db_tier
    availability_type = var.db_availability_type
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      transaction_log_retention_days  = 7
    }
    
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
    
    database_flags {
      name  = "max_connections"
      value = "100"
    }
    
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }
  
  deletion_protection = var.environment == "production"
}

resource "google_sql_database" "app_db" {
  name     = "cryptoorchestrator"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "app_user" {
  name     = var.db_username
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# ==========================================
# Cloud Memorystore (Redis) Instance
# ==========================================

resource "google_redis_instance" "redis" {
  name           = "cryptoorchestrator-redis"
  tier           = var.redis_tier
  memory_size_gb = var.redis_memory_size
  region         = var.gcp_region
  
  location_id             = "${var.gcp_region}-a"
  alternative_location_id = "${var.gcp_region}-b"
  
  redis_version     = "REDIS_7_0"
  display_name      = "CryptoOrchestrator Redis Cache"
  reserved_ip_range = "10.0.0.0/29"
  
  auth_enabled = true
  
  labels = {
    environment = var.environment
    project     = "cryptoorchestrator"
  }
}

# ==========================================
# VPC Network
# ==========================================

resource "google_compute_network" "vpc" {
  name                    = "cryptoorchestrator-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "cryptoorchestrator-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.gcp_region
  network       = google_compute_network.vpc.id
}

# ==========================================
# VPC Connector for Cloud Run
# ==========================================

resource "google_vpc_access_connector" "connector" {
  name          = "cryptoorchestrator-connector"
  region        = var.gcp_region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.8.0.0/28"
  
  min_instances = 2
  max_instances = 3
}

# ==========================================
# Cloud Run Service
# ==========================================

resource "google_cloud_run_service" "backend" {
  name     = "cryptoorchestrator-backend"
  location = var.gcp_region
  
  template {
    spec {
      containers {
        image = var.container_image
        
        ports {
          container_port = 8000
        }
        
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.database_url.secret_id
              key  = "latest"
            }
          }
        }
        
        env {
          name  = "REDIS_URL"
          value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}"
        }
        
        env {
          name  = "NODE_ENV"
          value = var.environment
        }
        
        env {
          name  = "PORT"
          value = "8000"
        }
        
        # Add other environment variables from secrets
        dynamic "env" {
          for_each = var.additional_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
        
        resources {
          limits = {
            cpu    = var.cloud_run_cpu_limit
            memory = var.cloud_run_memory_limit
          }
        }
        
        startup_probe {
          http_get {
            path = "/healthz"
          }
          initial_delay_seconds = 10
          timeout_seconds       = 5
          period_seconds        = 10
          failure_threshold     = 3
        }
        
        liveness_probe {
          http_get {
            path = "/healthz"
          }
          initial_delay_seconds = 30
          timeout_seconds      = 5
          period_seconds       = 10
          failure_threshold    = 3
        }
      }
      
      service_account_name = google_service_account.cloud_run.email
      
      container_concurrency = var.cloud_run_concurrency
      timeout_seconds      = var.cloud_run_timeout
    }
    
    metadata {
      annotations = {
        "autoscaling.knative.dev/minScale" = var.cloud_run_min_instances
        "autoscaling.knative.dev/maxScale" = var.cloud_run_max_instances
        "run.googleapis.com/vpc-access-connector" = google_vpc_access_connector.connector.name
        "run.googleapis.com/vpc-access-egress"    = "private-ranges-only"
        "run.googleapis.com/cloudsql-instances"   = google_sql_database_instance.postgres.connection_name
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
  
  depends_on = [
    google_vpc_access_connector.connector,
    google_sql_database_instance.postgres,
    google_redis_instance.redis,
  ]
}

# ==========================================
# Cloud Run IAM
# ==========================================



# ==========================================
# Service Account
# ==========================================

resource "google_service_account" "cloud_run" {
  account_id   = "cryptoorchestrator-cloud-run"
  display_name = "CryptoOrchestrator Cloud Run Service Account"
}

resource "google_project_iam_member" "cloud_run_sql" {
  project = var.gcp_project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_project_iam_member" "cloud_run_redis" {
  project = var.gcp_project_id
  role    = "roles/redis.editor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ==========================================
# Secret Manager (for sensitive env vars)
# ==========================================

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret
}

resource "google_secret_manager_secret" "encryption_key" {
  secret_id = "encryption-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "encryption_key" {
  secret      = google_secret_manager_secret.encryption_key.id
  secret_data = var.exchange_key_encryption_key
}

# Grant Cloud Run service account access to secrets
resource "google_secret_manager_secret_iam_member" "jwt_secret_access" {
  secret_id = google_secret_manager_secret.jwt_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

resource "google_secret_manager_secret_iam_member" "encryption_key_access" {
  secret_id = google_secret_manager_secret.encryption_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Database URL Secret
resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = "postgresql+asyncpg://${google_sql_user.app_user.name}:${var.db_password}@/${google_sql_database.app_db.name}?host=/cloudsql/${google_sql_database_instance.postgres.connection_name}"
}

resource "google_secret_manager_secret_iam_member" "database_url_access" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}

# ==========================================
# Cloud Scheduler (for scheduled tasks)
# ==========================================

resource "google_cloud_scheduler_job" "migrate_db" {
  name        = "cryptoorchestrator-migrate-db"
  description = "Run database migrations"
  schedule    = "0 2 * * *"  # Daily at 2 AM
  time_zone   = "UTC"
  region      = var.gcp_region
  
  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.backend.status[0].url}/api/admin/migrate"
    
    oidc_token {
      service_account_email = google_service_account.cloud_run.email
    }
  }
}

# ==========================================
# Outputs
# ==========================================

output "cloud_run_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "database_connection_name" {
  description = "Cloud SQL connection name"
  value       = google_sql_database_instance.postgres.connection_name
}

output "redis_host" {
  description = "Redis instance host"
  value       = google_redis_instance.redis.host
  sensitive   = true
}

output "redis_port" {
  description = "Redis instance port"
  value       = google_redis_instance.redis.port
}
