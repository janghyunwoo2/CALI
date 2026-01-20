# =====================================================
# IAM 모듈 - 메인 설정
# =====================================================
# 설명: EKS 노드, Fluent Bit, Consumer, Firehose용 IAM 역할 및 정책
# IRSA: IAM Roles for Service Accounts 사용
# =====================================================

# TODO: IAM 리소스 정의
# - EKS 노드 역할 (ECR 접근, CloudWatch Logs)
# - Fluent Bit Service Account 역할 (Kinesis PutRecord)
# - Consumer Service Account 역할 (Kinesis GetRecords, Secrets Manager, S3)
# - Firehose 역할 (S3 쓰기, OpenSearch 쓰기)
