# =====================================================
# ECR 모듈 - 변수 정의
# =====================================================

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경"
  type        = string
}

variable "repository_names" {
  description = "생성할 ECR 리포지토리 이름 목록"
  type        = list(string)
  default     = ["fluent-bit", "consumer", "api"]
}

# TODO: 추가 변수 정의
