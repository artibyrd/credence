# Cloudflare DNS, Edge Caching, and Security Configuration for Credence Multi-Domain Stack

locals {
  has_cloudflare = var.cloudflare_api_token != ""
}

# 1. Cloudflare DNS Zones (Data source lookup for active zones)
data "cloudflare_zone" "zone_run" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = var.domain_credence_run
}

data "cloudflare_zone" "zone_nexus" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = var.domain_credence_nexus
}

data "cloudflare_zone" "zone_foundation" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = var.domain_credence_foundation
}

data "cloudflare_zone" "zone_report" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  name       = var.domain_credence_report
}

# 2. SSL/TLS Strict Mode & Performance Configuration across all zones
resource "cloudflare_zone_settings_override" "ssl_run" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = data.cloudflare_zone.zone_run[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    early_hints              = "on"
    zero_rtt                 = "on"
    automatic_https_rewrites = "on"
  }
}

resource "cloudflare_zone_settings_override" "ssl_nexus" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = data.cloudflare_zone.zone_nexus[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    early_hints              = "on"
    zero_rtt                 = "on"
    automatic_https_rewrites = "on"
  }
}

resource "cloudflare_zone_settings_override" "ssl_foundation" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = data.cloudflare_zone.zone_foundation[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    early_hints              = "on"
    zero_rtt                 = "on"
    automatic_https_rewrites = "on"
  }
}

resource "cloudflare_zone_settings_override" "ssl_report" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = data.cloudflare_zone.zone_report[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    early_hints              = "on"
    zero_rtt                 = "on"
    automatic_https_rewrites = "on"
  }
}

# 3. DNS Records for P2P Mesh Discovery (SRV Record)
resource "cloudflare_record" "mesh_srv" {
  count           = local.has_cloudflare ? 1 : 0
  zone_id         = data.cloudflare_zone.zone_nexus[0].id
  name            = "_credence-seed._tcp"
  type            = "SRV"
  allow_overwrite = true

  data {
    service  = "_credence-seed"
    proto    = "_tcp"
    name     = var.domain_credence_nexus
    priority = 10
    weight   = 10
    port     = 8765
    target   = "relay.${var.domain_credence_nexus}"
  }
  comment = "DNS SRV record for mesh seed node discovery"
}
