# Cloud Scheduler Periodic Job for Automated Seed Ranking & Publishing

resource "google_service_account" "seed_publisher_sa" {
  account_id   = "credence-seed-publisher-sa"
  display_name = "Credence Seed Publisher Service Account"
}

# Grant Storage Object Admin on the seeds bucket
resource "google_storage_bucket_iam_member" "publisher_gcs_admin" {
  bucket = google_storage_bucket.seeds_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.seed_publisher_sa.email}"
}

# Grant Secret Manager Secret Accessor to read MESH_ROOT_ED25519_KEY
resource "google_secret_manager_secret_iam_member" "publisher_root_key_reader" {
  secret_id = "MESH_ROOT_ED25519_KEY"
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.seed_publisher_sa.email}"
}

# Cloud Scheduler Trigger: Runs every 12 hours (0 */12 * * *)
resource "google_cloud_scheduler_job" "seed_refresh_cron" {
  name             = "credence-seed-refresh-cron"
  description      = "Periodically recalculates mesh node quality and publishes signed peers.json"
  schedule         = "0 */12 * * *"
  time_zone        = "Etc/UTC"
  attempt_deadline = "300s"

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_v2_service.credence.uri}/cron/publish-seeds"

    oidc_token {
      service_account_email = google_service_account.seed_publisher_sa.email
    }
  }
}
