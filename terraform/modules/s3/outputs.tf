# =====================================================
# S3 모듈 - 출력 값
# =====================================================

output "backup_bucket_name" {
  description = "백업 버킷 이름"
  value       = "" # TODO: 버킷 생성 후 참조
}

output "dlq_bucket_name" {
  description = "DLQ 버킷 이름"
  value       = "" # TODO: 버킷 생성 후 참조
}

# TODO: 추가 출력 값 정의
