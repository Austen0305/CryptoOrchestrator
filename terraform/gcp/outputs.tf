# ==========================================
# GCP Terraform Outputs
# ==========================================

output "cloud_run_service_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_service.backend.status[0].url
}

output "cloud_run_service_name" {
  description = "Name of the Cloud Run service"
  value       = google_cloud_run_service.backend.name
}

output "database_connection_name" {
  description = "Cloud SQL connection name (for Cloud Run connection)"
  value       = google_sql_database_instance.postgres.connection_name
}

output "database_instance_name" {
  description = "Cloud SQL instance name"
  value       = google_sql_database_instance.postgres.name
}

output "redis_instance_name" {
  description = "Redis instance name"
  value       = google_redis_instance.redis.name
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

output "vpc_connector_name" {
  description = "VPC connector name"
  value       = google_vpc_access_connector.connector.name
}

output "service_account_email" {
  description = "Cloud Run service account email"
  value       = google_service_account.cloud_run.email
}
