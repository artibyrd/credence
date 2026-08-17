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
