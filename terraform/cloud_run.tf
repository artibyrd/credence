locals {
  profile_resources = {
    offline = {
      cpu           = "1.0"
      memory        = "512Mi"
      max_instances = 1
    }
    free = {
      cpu           = "1.0"
      memory        = "512Mi"
      max_instances = 1
    }
    economy = {
      cpu           = "1.0"
      memory        = "512Mi"
      max_instances = 2
    }
    balanced = {
      cpu           = "1.0"
      memory        = "1024Mi"
      max_instances = 2
    }
    ultra = {
      cpu           = "2.0"
      memory        = "2048Mi"
      max_instances = 5
    }
  }

  active_resources = local.profile_resources[var.credence_profile]
}

resource "google_cloud_run_v2_service" "credence" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account       = google_service_account.cloud_run_sa.email
    execution_environment = "EXECUTION_ENVIRONMENT_GEN2"

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = coalesce(var.max_instance_count, local.active_resources.max_instances)
    }

    containers {
      image = var.container_image

      command = ["credence", "serve", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = local.active_resources.cpu
          memory = local.active_resources.memory
        }
        cpu_idle          = true # Scale-to-zero compute savings when idle
        startup_cpu_boost = true # Dynamic CPU boost during cold boot
      }

      env {
        name  = "ENV"
        value = var.environment == "dev" ? "development" : "production"
      }
      env {
        name  = "CREDENCE_PROFILE"
        value = var.credence_profile
      }
      env {
        name  = "MCP_HOST"
        value = "0.0.0.0"
      }
      env {
        name  = "MCP_PORT"
        value = "8000"
      }

      env {
        name = "CREDENCE_GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "CREDENCE_ADMIN_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.admin_api_key.secret_id
            version = "latest"
          }
        }
      }
      env {
        name  = "CREDENCE_ADMIN_EMAILS"
        value = var.admin_emails
      }
      env {
        name  = "CREDENCE_OAUTH_GOOGLE_CLIENT_ID"
        value = var.oauth_google_client_id
      }

      startup_probe {
        initial_delay_seconds = 0
        period_seconds        = 2
        timeout_seconds       = 2
        failure_threshold     = 30
        http_get {
          path = "/health"
          port = 8000
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Public access policy (or customize for IAM authentication)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.credence.location
  service  = google_cloud_run_v2_service.credence.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
