# Secret Manager Resources & IAM Access Policies

resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "credence-gemini-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gemini_api_key_version" {
  count       = var.gemini_api_key != "" ? 1 : 0
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key
}

resource "google_secret_manager_secret" "root_ed25519_key" {
  secret_id = "MESH_ROOT_ED25519_KEY"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "admin_api_key" {
  secret_id = "credence-admin-api-key"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "admin_api_key_version" {
  count       = var.admin_api_key != "" ? 1 : 0
  secret      = google_secret_manager_secret.admin_api_key.id
  secret_data = var.admin_api_key
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

resource "google_secret_manager_secret_iam_member" "sa_admin_key_access" {
  secret_id = google_secret_manager_secret.admin_api_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

