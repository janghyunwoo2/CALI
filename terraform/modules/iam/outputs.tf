# =====================================================
# IAM 모듈 - 출력 값
# =====================================================

output "fluent_bit_role_arn" {
  description = "Fluent Bit Service Account IAM Role ARN"
  value       = "" # TODO: Role 생성 후 참조
}

output "consumer_role_arn" {
  description = "Consumer Service Account IAM Role ARN"
  value       = "" # TODO: Role 생성 후 참조
}

# TODO: 추가 출력 값 정의
