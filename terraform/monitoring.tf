resource "google_monitoring_dashboard" "credence_dashboard" {
  dashboard_json = jsonencode({
    displayName = "Credence FastMCP & Epistemic Audit Metrics"
    gridLayout = {
      columns = "2"
      widgets = [
        {
          title = "Cloud Run Request Count"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/request_count\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
              }
            ]
          }
        },
        {
          title = "Cloud Run Container Memory Utilization"
          xyChart = {
            dataSets = [
              {
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"run.googleapis.com/container/memory/utilizations\" AND resource.type=\"cloud_run_revision\" AND resource.label.service_name=\"${var.service_name}\""
                    aggregation = {
                      perSeriesAligner   = "ALIGN_PERCENTILE_99"
                      crossSeriesReducer = "REDUCE_MEAN"
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
