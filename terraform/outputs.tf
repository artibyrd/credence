output "service_url" {
  description = "The main HTTP URL of the deployed Credence Cloud Run service."
  value       = google_cloud_run_v2_service.credence.uri
}

output "sse_endpoint" {
  description = "The Server-Sent Events (SSE) MCP endpoint URL for connecting remote AI agents."
  value       = "${google_cloud_run_v2_service.credence.uri}/sse"
}

output "service_account_email" {
  description = "Service Account email for IAM permissions."
  value       = google_service_account.cloud_run_sa.email
}

output "active_profile" {
  description = "The active cost profile deployed."
  value       = var.credence_profile
}

output "canonical_domains" {
  description = "Configured canonical domains for the Credence network."
  value = {
    website    = "https://${var.domain_credence_run}"
    mcp_sse    = "https://mcp.${var.domain_credence_run}/sse"
    seeds      = "https://seeds.${var.domain_credence_nexus}/peers.json"
    taxonomies = "https://taxonomies.${var.domain_credence_foundation}"
    reports    = "https://${var.domain_credence_report}"
  }
}

output "seeds_bucket_name" {
  description = "Google Cloud Storage bucket for bootstrap seed manifests."
  value       = google_storage_bucket.seeds_bucket.name
}

output "taxonomies_bucket_name" {
  description = "Google Cloud Storage bucket for static taxonomy catalogs and root keys."
  value       = google_storage_bucket.taxonomies_bucket.name
}

output "monitoring_dashboard_id" {
  description = "Resource ID of the deployed Google Cloud Monitoring dashboard."
  value       = google_monitoring_dashboard.credence_dashboard.id
}

output "monitoring_tier" {
  description = "Active monitoring and alerting tier ('simple', 'advanced', or 'disabled')."
  value       = var.monitoring_tier
}

output "uptime_check_id" {
  description = "Resource ID of the global HTTP uptime probe (if enabled)."
  value       = length(google_monitoring_uptime_check_config.credence_http_uptime) > 0 ? google_monitoring_uptime_check_config.credence_http_uptime[0].id : "disabled"
}

output "active_notification_channels" {
  description = "List of configured Google Cloud Monitoring notification channel names."
  value       = local.all_notification_channels
}

