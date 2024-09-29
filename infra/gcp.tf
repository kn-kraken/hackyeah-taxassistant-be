resource "google_artifact_registry_repository" "tax_assistant_docker_repository" {
  location      = var.google_region
  repository_id = "tax-assistant-docker-repository"
  description   = "Docker repository for TaxAssistant"
  format        = "DOCKER"
}

data "google_artifact_registry_docker_image" "tax_assistant_docker_image" {
  image_name    = "taxassistant-be"
  location      = google_artifact_registry_repository.tax_assistant_docker_repository.location
  repository_id = google_artifact_registry_repository.tax_assistant_docker_repository.repository_id
}

resource "google_cloud_run_v2_service" "tax_assistant_be_service" {
  name     = "tax-assistant-be-service"
  location = var.google_region
  deletion_protection = false
  ingress = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = data.google_artifact_registry_docker_image.tax_assistant_docker_image.self_link
      ports {
        container_port = 8000
      }
      env {
        name = "OPENAI_API_KEY"
        value = var.openai_api_key
      }
      env {
        name = "OPENAI_MODEL_NAME"
        value = var.openai_model_name
      }
      env {
        name = "AZURE_SEARCH_ENDPOINT"
        value = var.azure_search_endpoint
      }
      env {
        name = "AZURE_SEARCH_KEY"
        value = var.azure_search_key
      }
      env {
        name = "AZURE_SEARCH_INDEX_NAME"
        value = var.azure_search_index_name
      }
    }
  }
}

resource "google_cloud_run_service_iam_binding" "tax_assistant_be_service_invoker" {
  location = google_cloud_run_v2_service.tax_assistant_be_service.location
  service  = google_cloud_run_v2_service.tax_assistant_be_service.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}