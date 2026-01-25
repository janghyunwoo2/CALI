# ==============================================================================
# CALI Infrastructure - Terraform Provider Configuration
# ==============================================================================
# AWS Provider 설정 및 공통 변수 정의
# ==============================================================================

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ------------------------------------------------------------------------------
# AWS Provider
# ------------------------------------------------------------------------------
provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key

  default_tags {
    tags = {
      Project     = "CALI"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# ------------------------------------------------------------------------------
# Variables
# ------------------------------------------------------------------------------
variable "aws_region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "aws_access_key" {
  description = "AWS Access Key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "cali"
}
