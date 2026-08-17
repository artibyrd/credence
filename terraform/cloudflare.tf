# Cloudflare DNS, Edge Caching, and Security Configuration for Credence Multi-Domain Stack

locals {
  has_cloudflare = var.cloudflare_api_token != ""
}

# 1. Cloudflare DNS Zones (Conditional on Cloudflare Token being set)
resource "cloudflare_zone" "zone_run" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  zone       = var.domain_credence_run
  plan       = "free"
}

resource "cloudflare_zone" "zone_nexus" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  zone       = var.domain_credence_nexus
  plan       = "free"
}

resource "cloudflare_zone" "zone_foundation" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  zone       = var.domain_credence_foundation
  plan       = "free"
}

resource "cloudflare_zone" "zone_report" {
  count      = local.has_cloudflare ? 1 : 0
  account_id = var.cloudflare_account_id
  zone       = var.domain_credence_report
  plan       = "free"
}

# 2. SSL/TLS Strict Mode Configuration across all zones
resource "cloudflare_zone_settings_override" "ssl_run" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_run[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    automatic_https_rewrites = "on"
  }
}

resource "cloudflare_zone_settings_override" "ssl_nexus" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_nexus[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    automatic_https_rewrites = "on"
  }
}

resource "cloudflare_zone_settings_override" "ssl_foundation" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_foundation[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    automatic_https_rewrites = "on"
  }
}

resource "cloudflare_zone_settings_override" "ssl_report" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_report[0].id

  settings {
    ssl                      = "strict"
    always_use_https         = "on"
    min_tls_version          = "1.2"
    brotli                   = "on"
    http3                    = "on"
    automatic_https_rewrites = "on"
  }
}

# 3. DNS Records for credence.run (Website + FastMCP SSE Origin)
resource "cloudflare_record" "mcp_cname" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_run[0].id
  name    = "mcp"
  content = replace(replace(google_cloud_run_v2_service.credence.uri, "https://", ""), "/", "")
  type    = "CNAME"
  proxied = true
  ttl     = 1 # Auto when proxied
  comment = "FastMCP Cloud Run SSE service"
}

# 4. DNS Records for seeds.credence.nexus & SRV Record
resource "cloudflare_record" "seeds_cname" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_nexus[0].id
  name    = "seeds"
  content = "cname.r2.cloudflarestorage.com"
  type    = "CNAME"
  proxied = true
  ttl     = 1
  comment = "Bootstrap seed directory (peers.json)"
}

resource "cloudflare_record" "mesh_srv" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_nexus[0].id
  name    = "_credence-seed._tcp"
  type    = "SRV"

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

# 5. DNS Records for taxonomies.credence.foundation
resource "cloudflare_record" "taxonomies_cname" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_foundation[0].id
  name    = "taxonomies"
  content = "cname.r2.cloudflarestorage.com"
  type    = "CNAME"
  proxied = true
  ttl     = 1
  comment = "Static JSON taxonomy catalogs"
}

resource "cloudflare_record" "keys_cname" {
  count   = local.has_cloudflare ? 1 : 0
  zone_id = cloudflare_zone.zone_foundation[0].id
  name    = "keys"
  content = "cname.r2.cloudflarestorage.com"
  type    = "CNAME"
  proxied = true
  ttl     = 1
  comment = "Network root Ed25519 public key (root.pub)"
}

# 6. Page Rules & Cache Rules (Disable SSE Buffering, Enable Seed Caching)
resource "cloudflare_page_rule" "sse_bypass" {
  count    = local.has_cloudflare ? 1 : 0
  zone_id  = cloudflare_zone.zone_run[0].id
  target   = "mcp.${var.domain_credence_run}/sse*"
  priority = 1

  actions {
    cache_level         = "bypass"
    disable_performance = true # Disables response buffering for real-time SSE streaming
  }
}

resource "cloudflare_page_rule" "seeds_cache" {
  count    = local.has_cloudflare ? 1 : 0
  zone_id  = cloudflare_zone.zone_nexus[0].id
  target   = "seeds.${var.domain_credence_nexus}/peers.json"
  priority = 1

  actions {
    cache_level    = "cache_everything"
    edge_cache_ttl = 300
  }
}
