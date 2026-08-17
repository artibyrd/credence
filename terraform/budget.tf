resource "google_billing_budget" "budget" {
  count = var.billing_account_id != "" ? 1 : 0

  billing_account = var.billing_account_id
  display_name    = "Credence Project Hard Budget Ceiling ($${var.monthly_budget_limit_usd}/mo)"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "USD"
      units         = tostring(floor(var.monthly_budget_limit_usd))
      nanos         = floor((var.monthly_budget_limit_usd - floor(var.monthly_budget_limit_usd)) * 1000000000)
    }
  }

  threshold_rules {
    threshold_percent = 0.50
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.80
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.00
    spend_basis       = "CURRENT_SPEND"
  }

  dynamic "all_updates_rule" {
    for_each = length(var.alert_email_addresses) > 0 ? [1] : []
    content {
      monitoring_notification_channels = []
      disable_default_iam_recipients   = false
    }
  }
}
