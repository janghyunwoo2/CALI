# =====================================================
# CALI 프로젝트 - Terraform 출력 값
# =====================================================
# 설명: 인프라 배포 후 필요한 정보를 출력합니다.
# 사용: EKS 클러스터명, OpenSearch 엔드포인트, ECR URL 등
# =====================================================

# VPC 출력
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

# EKS 출력
output "eks_cluster_name" {
  description = "EKS 클러스터 이름"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS 클러스터 엔드포인트"
  value       = module.eks.cluster_endpoint
}

# Kinesis 출력
output "kinesis_stream_name" {
  description = "Kinesis Data Stream 이름"
  value       = module.kinesis.stream_name
}

# S3 출력
output "s3_backup_bucket" {
  description = "S3 백업 버킷 이름"
  value       = module.s3.backup_bucket_name
}

# OpenSearch 출력
output "opensearch_endpoint" {
  description = "OpenSearch 도메인 엔드포인트"
  value       = module.opensearch.endpoint
}

# ECR 출력
output "ecr_repositories" {
  description = "ECR 리포지토리 URL 목록"
  value       = module.ecr.repository_urls
}

# TODO: 추가 출력 값 정의
