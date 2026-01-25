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
