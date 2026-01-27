# ==============================================================================
# CALI Infrastructure - Outputs
# ==============================================================================
# 팀원 공유용 ARN, Endpoint 등 출력값
# ==============================================================================

# ------------------------------------------------------------------------------
# Kinesis
# ------------------------------------------------------------------------------
output "kinesis_stream_arn" {
  description = "Kinesis Data Stream ARN"
  value       = aws_kinesis_stream.logs.arn
}

output "kinesis_stream_name" {
  description = "Kinesis Data Stream 이름"
  value       = aws_kinesis_stream.logs.name
}

# ------------------------------------------------------------------------------
# S3
# ------------------------------------------------------------------------------
output "s3_bucket_name" {
  description = "S3 버킷 이름"
  value       = aws_s3_bucket.logs.id
}

output "s3_bucket_arn" {
  description = "S3 버킷 ARN"
  value       = aws_s3_bucket.logs.arn
}

# ------------------------------------------------------------------------------
# OpenSearch
# ------------------------------------------------------------------------------
output "opensearch_endpoint" {
  description = "OpenSearch 도메인 Endpoint"
  value       = aws_opensearch_domain.logs.endpoint
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch Dashboard URL"
  value       = "https://${aws_opensearch_domain.logs.endpoint}/_dashboards"
}

# ------------------------------------------------------------------------------
# EKS
# ------------------------------------------------------------------------------
output "eks_cluster_name" {
  description = "EKS 클러스터 이름"
  value       = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  description = "EKS API 서버 Endpoint"
  value       = aws_eks_cluster.main.endpoint
}

output "eks_cluster_arn" {
  description = "EKS 클러스터 ARN"
  value       = aws_eks_cluster.main.arn
}

# ------------------------------------------------------------------------------
# Grafana - Helm으로 EKS에 배포 예정, kubectl get svc로 확인
# ------------------------------------------------------------------------------
# output "grafana_workspace_endpoint" {
#   description = "Grafana 워크스페이스 URL"
#   value       = aws_grafana_workspace.main.endpoint
# }

# ------------------------------------------------------------------------------
# ECR
# ------------------------------------------------------------------------------
output "ecr_consumer_url" {
  description = "Consumer ECR 리포지토리 URL"
  value       = aws_ecr_repository.consumer.repository_url
}

output "ecr_log_generator_url" {
  description = "Log Generator ECR 리포지토리 URL"
  value       = aws_ecr_repository.log_generator.repository_url
}

# ------------------------------------------------------------------------------
# 연결 가이드 (kubectl)
# ------------------------------------------------------------------------------
output "kubectl_config_command" {
  description = "kubectl 연결 명령어"
  value       = "aws eks update-kubeconfig --name ${aws_eks_cluster.main.name} --region ${var.aws_region}"
}

# ------------------------------------------------------------------------------
# App Role (IRSA)
# ------------------------------------------------------------------------------
output "app_role_arn" {
  description = "Application IRSA Role ARN (Consumer, Fluent Bit)"
  value       = aws_iam_role.app_role.arn
}

output "cluster_autoscaler_role_arn" {
  description = "Cluster Autoscaler Role ARN"
  value       = aws_iam_role.cluster_autoscaler.arn
}
