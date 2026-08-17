variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID to deploy Credence into."
}

variable "region" {
  type        = string
  description = "The GCP region for Cloud Run and Secret Manager resources."
  default     = "us-central1"
}

variable "service_name" {
  type        = string
  description = "The name of the Cloud Run service."
  default     = "credence-server"
}

variable "container_image" {
  type        = string
  description = "The full container image URI in Artifact Registry or GCR."
  default     = "us-central1-docker.pkg.dev/sample-project/credence/credence-server:latest"
}

variable "credence_profile" {
  type        = string
  description = "Operational cost profile: 'free', 'balanced', or 'ultra'."
  default     = "balanced"

  validation {
    condition     = contains(["free", "balanced", "ultra"], var.credence_profile)
    error_message = "credence_profile must be one of: 'free', 'balanced', 'ultra'."
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
