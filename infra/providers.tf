terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "4.3.0"
    }

    google = {
      source  = "hashicorp/google"
      version = "6.4.0"
    }
  }
}

provider "azurerm" {
    subscription_id = var.azure_subscription_id
    features {}
}

provider "google" {
  project     = var.google_project_id
  region      = var.google_region
}
