# =====================================================
# CALI 프로젝트 - Terraform 변수 정의
# =====================================================
# 설명: 프로젝트 전체에서 사용하는 공통 변수를 정의합니다.
# =====================================================

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
  default     = "cali"
}

variable "environment" {
  description = "환경 (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "AWS 리전"
  type        = string
  default     = "ap-northeast-2"
}

variable "tags" {
  description = "모든 리소스에 적용할 공통 태그"
  type        = map(string)
  default = {
    Project   = "CALI"
    ManagedBy = "Terraform"
  }
}

# TODO: 추가 변수 정의
