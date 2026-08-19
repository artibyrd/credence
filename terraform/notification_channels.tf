# Cloud Monitoring Notification Channels for Incident & Budget Alerting

# 1. Discord / Powercord Webhook Channel
resource "google_monitoring_notification_channel" "discord" {
  count        = var.discord_webhook_url != "" ? 1 : 0
  display_name = "Discord Webhook (${var.service_name})"
  type         = "webhook_tokenauth"
  description  = "Direct incoming webhook for Discord or Powercord bot relay."

  labels = {
    url = var.discord_webhook_url
  }
}

# 2. Direct Email Notification Channels
resource "google_monitoring_notification_channel" "email" {
  for_each     = toset(var.alert_email_addresses)
  display_name = "Email Alert (${each.value})"
  type         = "email"
  description  = "Direct email notifications for operational incidents and budget thresholds."

  labels = {
    email_address = each.value
  }
}

# 3. Consolidated Notification Channels
locals {
  all_notification_channels = concat(
    [for ch in google_monitoring_notification_channel.discord : ch.name],
    [for ch in google_monitoring_notification_channel.email : ch.name]
  )
  has_notification_channels = length(local.all_notification_channels) > 0
}
