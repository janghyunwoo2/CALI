# =====================================================
# CALI 프로젝트 - Terraform 및 Provider 버전 관리
# =====================================================
# 설명: Terraform 버전과 AWS Provider 버전을 고정합니다.
# 목적: 재현 가능한 인프라 배포 보장
# =====================================================

terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.80"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = var.tags
  }
}
