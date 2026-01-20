# =====================================================
# Kinesis 모듈 - 변수 정의
# =====================================================

variable "project_name" {
  description = "프로젝트 이름"
  type        = string
}

variable "environment" {
  description = "환경"
  type        = string
}

variable "shard_count" {
  description = "Kinesis Stream 샤드 수"
  type        = number
  default     = 2
}

# TODO: 추가 변수 정의
