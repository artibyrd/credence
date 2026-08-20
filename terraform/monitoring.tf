# Cloud Monitoring Dashboard, Uptime Probes & Dual-Tier Alert Policies

locals {
  enable_simple_alerts   = var.monitoring_tier != "disabled"
  enable_advanced_alerts = var.monitoring_tier == "advanced"
}

# ==============================================================================
# 1. Essential HTTP Uptime Health Check Probe
# ==============================================================================

resource "google_monitoring_uptime_check_config" "credence_http_uptime" {
  count        = (var.enable_uptime_check && var.monitoring_tier != "disabled") ? 1 : 0
  display_name = "${var.service_name}-http-uptime-probe"
  timeout      = "10s"
  period       = "60s"

  http_check {
    path           = "/health"
    port           = 443
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(replace(google_cloud_run_v2_service.credence.uri, "https://", ""), "http://", "")
    }
  }

  content_matchers {
    content = "healthy"
    matcher = "CONTAINS_STRING"
  }
}

# ==============================================================================
# 2. Core Alert Policies (Active in both 'simple' and 'advanced' tiers)
# ==============================================================================

# 2.1 Critical Service Outage Alert (Uptime Check Failed)
resource "google_monitoring_alert_policy" "uptime_check_failure" {
  count                 = (var.enable_uptime_check && local.enable_simple_alerts) ? 1 : 0
  display_name          = "${var.service_name} - Critical Service Outage (Uptime Probe Failed)"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Run /health Uptime Check Failing"
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"${google_monitoring_uptime_check_config.credence_http_uptime[0].uptime_check_id}\" AND resource.type=\"uptime_url\""
      duration        = "120s"
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_FRACTION_TRUE"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "🚨 **CRITICAL**: The Credence service `${var.service_name}` is failing global HTTP `/health` uptime checks. Investigate container status via `just gcp status` or review logs with `just gcp logs`."
    mime_type = "text/markdown"
  }
}

# 2.2 Server 5xx Error Spike Alert
resource "google_monitoring_alert_policy" "cloud_run_5xx_errors" {
  count                 = local.enable_simple_alerts ? 1 : 0
  display_name          = "${var.service_name} - High 5xx Server Error Spike"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Run 5xx Server Errors > Threshold"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\" AND metric.label.response_code_class=\"5xx\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.alert_5xx_count_threshold
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "🔥 **WARNING**: Elevated 5xx server errors detected on `${var.service_name}`. Inspect recent container exceptions with `just gcp logs` or rollback if necessary with `just gcp rollback`."
    mime_type = "text/markdown"
  }
}

# 2.3 Container Memory Pressure Alert (>85% limit)
resource "google_monitoring_alert_policy" "cloud_run_memory_utilization" {
  count                 = local.enable_simple_alerts ? 1 : 0
  display_name          = "${var.service_name} - Container Memory Pressure Warning (>85%)"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Run Memory Utilization > Threshold"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/container/memory/utilizations\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
      duration        = "180s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.alert_memory_threshold
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MAX"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "⚠️ **WARNING**: Container memory utilization has exceeded ${var.alert_memory_threshold * 100}% on `${var.service_name}`. This may cause Playwright/feed sifter container OOM exit (code 137). Consider increasing memory baseline in `cloud_run.tf` or scaling."
    mime_type = "text/markdown"
  }
}

# ==============================================================================
# 3. Advanced Alert Policies & Metrics (Active only when monitoring_tier = 'advanced')
# ==============================================================================

# 3.1 P95 Request Latency Alert
resource "google_monitoring_alert_policy" "cloud_run_latency_high" {
  count                 = local.enable_advanced_alerts ? 1 : 0
  display_name          = "${var.service_name} - Elevated Request Latency (P95 > ${var.alert_latency_p95_ms}ms)"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Run P95 Latency > Threshold"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.alert_latency_p95_ms
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_95"
        cross_series_reducer = "REDUCE_MAX"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "⏱️ **PERFORMANCE**: High request latency detected on `${var.service_name}`. Epistemic LLM reasoning or network scraping operations may be stalling."
    mime_type = "text/markdown"
  }
}

# 3.2 Container CPU Saturation Alert
resource "google_monitoring_alert_policy" "cloud_run_cpu_saturation" {
  count                 = local.enable_advanced_alerts ? 1 : 0
  display_name          = "${var.service_name} - Container CPU Saturation (>90%)"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Run CPU Utilization > Threshold"
    condition_threshold {
      filter          = "metric.type=\"run.googleapis.com/container/cpu/utilizations\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = var.alert_cpu_threshold
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MAX"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "⚙️ **PERFORMANCE**: CPU utilization has exceeded ${var.alert_cpu_threshold * 100}% on `${var.service_name}`."
    mime_type = "text/markdown"
  }
}

# 3.3 Cloud Scheduler Job Failure Alert
resource "google_logging_metric" "scheduler_job_failures" {
  count       = local.enable_advanced_alerts ? 1 : 0
  name        = "${var.service_name}-scheduler-failures"
  description = "Log-based metric for failed Cloud Scheduler seed refresh executions."
  filter      = "resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"${google_cloud_scheduler_job.seed_refresh_cron.name}\" AND (severity>=ERROR OR jsonPayload.status!=\"SUCCESS\")"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_monitoring_alert_policy" "cloud_scheduler_cron_failure" {
  count                 = local.enable_advanced_alerts ? 1 : 0
  display_name          = "${var.service_name} - Seed Publisher Cron Job Failure"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Scheduler Job Attempt Failed"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.scheduler_job_failures[0].name}\" AND resource.type=\"cloud_scheduler_job\""
      duration        = "0s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "📅 **WARNING**: Cloud Scheduler job `${google_cloud_scheduler_job.seed_refresh_cron.name}` failed to execute seed ranking and GCS publication."
    mime_type = "text/markdown"
  }
}

# 3.4 Custom Log-Based Error Metric & Surge Alert
resource "google_logging_metric" "credence_error_logs" {
  count       = local.enable_advanced_alerts ? 1 : 0
  name        = "${var.service_name}-error-logs"
  description = "Log-based metric for Cloud Run ERROR and CRITICAL severity log entries."
  filter      = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.service_name}\" AND severity>=ERROR"

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

resource "google_monitoring_alert_policy" "error_log_surge" {
  count                 = local.enable_advanced_alerts ? 1 : 0
  display_name          = "${var.service_name} - Application Error Log Surge"
  combiner              = "OR"
  enabled               = true
  notification_channels = local.all_notification_channels

  conditions {
    display_name = "Cloud Run Error Log Entries > 10 in 5m"
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.credence_error_logs[0].name}\" AND resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_DELTA"
        cross_series_reducer = "REDUCE_SUM"
      }
      trigger {
        count = 1
      }
    }
  }

  documentation {
    content   = "📜 **WARNING**: Surge in application error logs on `${var.service_name}`. Run `just gcp logs` to inspect tracebacks."
    mime_type = "text/markdown"
  }
}

# ==============================================================================
# 4. Production SRE Telemetry Dashboard
# ==============================================================================

resource "google_monitoring_dashboard" "credence_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Credence FastMCP & Epistemic Node SRE Telemetry"
    gridLayout = {
      columns = "2"
      widgets = [
        {
          title = "HTTP Request Rate by Response Code Class"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields      = ["metric.label.response_code_class"]
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Request Latencies (P50, P95, P99 Distribution)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_latencies\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_95"
                      crossSeriesReducer = "REDUCE_MAX"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Container Memory Utilization (vs 85% Warning Limit)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/memory/utilizations\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_99"
                      crossSeriesReducer = "REDUCE_MAX"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Container CPU Utilization (vs 90% Limit)"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/cpu/utilizations\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_99"
                      crossSeriesReducer = "REDUCE_MAX"
                    }
                  }
                }
              }
            ]
          }
        }
      ]
    }
  })
}
