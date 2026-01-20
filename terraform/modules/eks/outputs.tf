# =====================================================
# EKS 모듈 - 출력 값
# =====================================================

output "cluster_name" {
  description = "EKS 클러스터 이름"
  value       = "" # TODO: EKS 클러스터 생성 후 참조
}

output "cluster_endpoint" {
  description = "EKS 클러스터 엔드포인트"
  value       = "" # TODO: EKS 클러스터 생성 후 참조
}

output "oidc_provider_arn" {
  description = "OIDC Provider ARN (IRSA용)"
  value       = "" # TODO: OIDC Provider 생성 후 참조
}

# TODO: 추가 출력 값 정의
