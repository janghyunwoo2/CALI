# =====================================================
# EKS 모듈 - 변수 정의
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

variable "private_subnet_ids" {
  description = "Private 서브넷 ID 목록 (노드 그룹 배치용)"
  type        = list(string)
}

# TODO: 추가 변수 정의
