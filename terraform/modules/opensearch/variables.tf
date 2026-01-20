# =====================================================
# OpenSearch 모듈 - 변수 정의
# =====================================================

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "OpenSearch 배치용 서브넷 ID 목록"
  type        = list(string)
}

# TODO: 추가 변수 정의
