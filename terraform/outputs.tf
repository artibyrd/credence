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
