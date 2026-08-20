variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID to deploy Credence into."
}

variable "region" {
  type        = string
  description = "The GCP region for Cloud Run and Secret Manager resources."
  default     = "us-central1"
}

variable "environment" {
  type        = string
  description = "Target deployment environment: 'dev' or 'prod'."
  default     = "prod"

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be either 'dev' or 'prod'."
  }
}

variable "enable_dev_subdomains" {
  type        = bool
  description = "Enable provisioning and DNS routing for dev.* subdomains in Cloudflare."
  default     = false
}

variable "service_name" {
  type        = string
  description = "The name of the Cloud Run service."
  default     = "credence-server"
}

variable "container_image" {
  type        = string
  description = "The full container image URI in GCR or Artifact Registry."
  default     = "gcr.io/sample-project/credence-server:latest"
}

variable "credence_profile" {
  type        = string
  description = "Operational cost profile: 'offline', 'free', 'economy', 'balanced', or 'ultra'."
  default     = "economy"

  validation {
    condition     = contains(["offline", "free", "economy", "balanced", "ultra"], var.credence_profile)
    error_message = "credence_profile must be one of: 'offline', 'free', 'economy', 'balanced', 'ultra'."
  }
}

variable "monthly_budget_limit_usd" {
  type        = number
  description = "Hard monthly budget ceiling for the project in USD."
  default     = 15.0
}

variable "billing_account_id" {
  type        = string
  description = "The GCP Billing Account ID (e.g. 012345-567890-ABCDEF) for budget alerts."
  default     = ""
}

variable "alert_email_addresses" {
  type        = list(string)
  description = "Email addresses to notify when budget alert thresholds (50%, 80%, 100%) are reached."
  default     = []
}

variable "min_instance_count" {
  type        = number
  description = "Minimum instance count for Cloud Run (0 for scale-to-zero)."
  default     = 0
}

variable "max_instance_count" {
  type        = number
  description = "Maximum instance count for Cloud Run to prevent runaway scaling."
  default     = 2
}

variable "cloudflare_api_token" {
  type        = string
  description = "Cloudflare scoped API token for managing DNS, WAF, and R2."
  sensitive   = true
  default     = ""
}

variable "cloudflare_account_id" {
  type        = string
  description = "The Cloudflare Account ID for R2 storage and zones."
  default     = ""
}

variable "domain_credence_run" {
  type        = string
  description = "Primary canonical domain for website and FastMCP service."
  default     = "credence.run"
}

variable "domain_credence_nexus" {
  type        = string
  description = "Domain for P2P mesh network, seed directory, and relay."
  default     = "credence.nexus"
}

variable "domain_credence_foundation" {
  type        = string
  description = "Domain for taxonomy governance and root public key directory."
  default     = "credence.foundation"
}

variable "domain_credence_report" {
  type        = string
  description = "Domain for public audit permalinks and report viewer."
  default     = "credence.report"
}

variable "gemini_api_key" {
  type        = string
  description = "Google Gemini API key for Cloud Run reasoning engine."
  sensitive   = true
  default     = ""
}

# ==============================================================================
# Monitoring & Alerting Configuration (Dual-Tier: Simple / Advanced)
# ==============================================================================

variable "monitoring_tier" {
  type        = string
  description = "Monitoring and alerting tier: 'simple' (Guy in his basement easy mode: 3 essential failure alerts + Discord/Email), 'advanced' (extended SRE metrics, log error tracking, P95 latency alerts), or 'disabled'."
  default     = "simple"

  validation {
    condition     = contains(["simple", "advanced", "disabled"], var.monitoring_tier)
    error_message = "monitoring_tier must be one of: 'simple', 'advanced', 'disabled'."
  }
}

variable "discord_webhook_url" {
  type        = string
  description = "Discord or Powercord incoming webhook URL for incident alerts and monthly budget thresholds."
  sensitive   = true
  default     = ""
}

variable "enable_uptime_check" {
  type        = bool
  description = "Enable global 60-second HTTP uptime check against /health endpoint."
  default     = true
}

variable "alert_memory_threshold" {
  type        = number
  description = "Memory utilization threshold (0.0 - 1.0) triggering early OOM warning (default: 0.85 = 85%)."
  default     = 0.85
}

variable "alert_cpu_threshold" {
  type        = number
  description = "CPU utilization threshold (0.0 - 1.0) triggering CPU saturation warning in advanced tier (default: 0.90 = 90%)."
  default     = 0.90
}

variable "alert_latency_p95_ms" {
  type        = number
  description = "P95 request latency threshold in milliseconds triggering performance degradation alert in advanced tier (default: 5000ms)."
  default     = 5000
}

variable "alert_5xx_count_threshold" {
  type        = number
  description = "Number of 5xx HTTP server errors over a 5-minute window triggering server crash alert (default: 5)."
  default     = 5
}

