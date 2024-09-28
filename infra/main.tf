resource "azurerm_resource_group" "tax_assistant_rg" {
  name     = "tax-assistant-rg"
  location = "West Europe"
}

resource "azurerm_search_service" "tax_assistant_ai_search" {
  name                = "tax-assistant-ai-search"
  resource_group_name = azurerm_resource_group.tax_assistant_rg.name
  location            = azurerm_resource_group.tax_assistant_rg.location
  sku                 = "basic"
}
