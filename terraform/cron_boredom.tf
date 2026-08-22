# Cloud Scheduler Periodic Heartbeat for Adaptive Epistemic Curiosity (Scale-to-Zero)

resource "google_service_account" "boredom_cron_sa" {
  account_id   = "credence-boredom-cron-sa"
  display_name = "Credence Boredom Cron Service Account"
}

# Grant Cloud Run Invoker role on the target service
resource "google_cloud_run_v2_service_iam_member" "boredom_cron_invoker" {
  location = google_cloud_run_v2_service.credence.location
  name     = google_cloud_run_v2_service.credence.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.boredom_cron_sa.email}"
}

# Cloud Scheduler Trigger: Variable Epistemic Heartbeat every 10 minutes (*/10 * * * *)
resource "google_cloud_scheduler_job" "boredom_tick_cron" {
  name             = "credence-boredom-tick-cron"
  description      = "Executes adaptive epistemic curiosity bursts when the node is idle"
  schedule         = "*/10 * * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "300s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.credence.uri}/cron/boredom"

    oidc_token {
      service_account_email = google_service_account.boredom_cron_sa.email
    }
  }
}
