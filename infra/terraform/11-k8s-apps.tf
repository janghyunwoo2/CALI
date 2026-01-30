resource "kubernetes_service_account" "consumer_sa" {
  metadata {
    name      = "consumer-sa"
    namespace = "default"
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.app_role.arn
    }
  }
}

resource "kubernetes_deployment" "consumer" {
  metadata {
    name      = "consumer"
    namespace = "default"
    labels = {
      app = "consumer"
    }
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "consumer"
      }
    }
    template {
      metadata {
        labels = {
          app = "consumer"
        }
      }
      spec {
        service_account_name = kubernetes_service_account.consumer_sa.metadata[0].name
        container {
          name              = "consumer"
          image             = "${aws_ecr_repository.consumer.repository_url}:latest"
          image_pull_policy = "Always"

          env {
            name  = "KINESIS_STREAM_NAME"
            value = "${var.project_name}-logs-stream"
          }
          env {
            name  = "S3_DLQ_BUCKET"
            value = aws_s3_bucket.logs.bucket
          }
          env {
            name  = "AWS_REGION"
            value = var.aws_region
          }
          env {
            name  = "MILVUS_HOST"
            value = "milvus-standalone.milvus.svc.cluster.local" # Full DNS for cross-namespace
          }
          env {
            name  = "MILVUS_PORT"
            value = "19530"
          }

          # Secrets (Assumed to be created manually or via another resource)
          # env {
          #   name = "OPENAI_API_KEY"
          #   value_from {
          #     secret_key_ref {
          #       name = "app-secrets"
          #       key  = "openai-api-key"
          #     }
          #   }
          # }

          resources {
            requests = {
              cpu    = "250m"
              memory = "512Mi"
            }
            limits = {
              cpu    = "500m"
              memory = "1Gi"
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment" "log_generator" {
  metadata {
    name      = "log-generator"
    namespace = "default"
    labels = {
      app = "log-generator"
    }
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "log-generator"
      }
    }
    template {
      metadata {
        labels = {
          app = "log-generator"
        }
      }
      spec {
        container {
          name              = "log-generator"
          image             = "${aws_ecr_repository.log_generator.repository_url}:latest"
          image_pull_policy = "Always"

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }
            limits = {
              cpu    = "200m"
              memory = "256Mi"
            }
          }
        }
      }
    }
  }
}
