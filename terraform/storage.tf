# Storage Buckets for Signed Bootstrap Seeds and Static Taxonomy Mirrors

# 1. Google Cloud Storage Bucket for Seed Directory (Backup & GCS Origin)
resource "google_storage_bucket" "seeds_bucket" {
  name                        = "${var.project_id}-seeds-nexus"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  website {
    main_page_suffix = "peers.json"
    not_found_page   = "peers.json"
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Grant public read access to the seeds bucket
resource "google_storage_bucket_iam_member" "seeds_public_read" {
  bucket = google_storage_bucket.seeds_bucket.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# 2. Google Cloud Storage Bucket for Static Taxonomies & Public Keys
resource "google_storage_bucket" "taxonomies_bucket" {
  name                        = "${var.project_id}-taxonomies-foundation"
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 86400
  }
}

# Grant public read access to the taxonomies bucket
resource "google_storage_bucket_iam_member" "taxonomies_public_read" {
  bucket = google_storage_bucket.taxonomies_bucket.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}
