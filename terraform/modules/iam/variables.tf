# =====================================================
# IAM 모듈 - 변수 정의
# =====================================================

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경"
  type        = string
}

variable "oidc_provider_arn" {
  description = "EKS OIDC Provider ARN (IRSA용)"
  type        = string
}

# TODO: 추가 변수 정의
