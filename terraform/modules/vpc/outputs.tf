# =====================================================
# VPC 모듈 - 출력 값
# =====================================================
# 설명: 다른 모듈에서 사용할 VPC 정보를 출력합니다.
# =====================================================

output "vpc_id" {
  description = "VPC ID"
  value       = "" # TODO: VPC 리소스 생성 후 참조
}

output "public_subnet_ids" {
  description = "Public 서브넷 ID 목록"
  value       = [] # TODO: 서브넷 리소스 생성 후 참조
}

output "private_subnet_ids" {
  description = "Private 서브넷 ID 목록"
  value       = [] # TODO: 서브넷 리소스 생성 후 참조
}

output "database_subnet_ids" {
  description = "Database 서브넷 ID 목록"
  value       = [] # TODO: 서브넷 리소스 생성 후 참조
}

# TODO: 추가 출력 값 정의
