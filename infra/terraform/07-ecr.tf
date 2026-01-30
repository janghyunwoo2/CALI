# ==============================================================================
# CALI Infrastructure - ECR Repositories
# ==============================================================================
# Consumer, Log Generator Docker 이미지 저장소
# ==============================================================================

# ------------------------------------------------------------------------------
# ECR Repository - Consumer
# ------------------------------------------------------------------------------
resource "aws_ecr_repository" "consumer" {
  name                 = "${var.project_name}/consumer"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-consumer"
  }
}

# ------------------------------------------------------------------------------
# ECR Repository - Log Generator
# ------------------------------------------------------------------------------
resource "aws_ecr_repository" "log_generator" {
  name                 = "${var.project_name}/log-generator"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-log-generator"
  }
}

# ------------------------------------------------------------------------------
# Lifecycle Policy (오래된 이미지 자동 삭제)
# ------------------------------------------------------------------------------
resource "aws_ecr_lifecycle_policy" "consumer" {
  repository = aws_ecr_repository.consumer.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

resource "aws_ecr_lifecycle_policy" "log_generator" {
  repository = aws_ecr_repository.log_generator.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}

# ------------------------------------------------------------------------------
# ECR Repository - Airflow Custom Image
# ------------------------------------------------------------------------------
resource "aws_ecr_repository" "airflow_custom" {
  name                 = "${var.project_name}/airflow-custom"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-airflow-custom"
  }
}

# Image Build & Push Automation
resource "null_resource" "airflow_custom_build" {
  triggers = {
    dockerfile_hash   = filemd5("${path.module}/../../apps/airflow/Dockerfile")
    requirements_hash = filemd5("${path.module}/../../apps/airflow/requirements.txt")
    ecr_url           = aws_ecr_repository.airflow_custom.repository_url
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]
    command     = <<EOT
      $ErrorActionPreference = "Stop"
      $EcrUrl = "${aws_ecr_repository.airflow_custom.repository_url}"
      $Region = "ap-northeast-2"
      
      # Login
      aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $EcrUrl.Split('/')[0]
      
      # Build
      docker build -t $EcrUrl":latest" ../../apps/airflow
      
      # Push
      docker push $EcrUrl":latest"
    EOT
  }

  depends_on = [
    aws_ecr_repository.airflow_custom
  ]
}

resource "aws_ecr_lifecycle_policy" "airflow_custom" {
  repository = aws_ecr_repository.airflow_custom.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}
