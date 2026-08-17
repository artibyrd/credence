resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "credence-gemini-api-key"

  replication {
    auto {}
  }
}

resource "google_service_account" "cloud_run_sa" {
  account_id   = "credence-cloud-run-sa"
  display_name = "Credence Cloud Run Service Account"
}

resource "google_secret_manager_secret_iam_member" "sa_secret_access" {
  secret_id = google_secret_manager_secret.gemini_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
