output "azurerm_ai_search_key" {
  value = azurerm_search_service.tax_assistant_ai_search.primary_key
  sensitive = true
}