output "azurerm_ai_search_key" {
  value     = azurerm_search_service.tax_assistant_ai_search.primary_key
  sensitive = true
}

output "google_cloud_run_be_service_uri" {
  value = google_cloud_run_v2_service.tax_assistant_be_service.uri
}

output "google_cloud_run_mock_fe_service_uri" {
  value = google_cloud_run_v2_service.tax_assistant_mock_fe_service.uri
}
