# =====================================================
# CALI 프로젝트 - Terraform 메인 설정
# =====================================================
# 설명: 모든 인프라 모듈을 통합하고 상호 의존성을 관리합니다.
# 담당: VPC, EKS, Kinesis, S3, OpenSearch, ECR, Secrets, IAM 모듈 호출
# =====================================================

# VPC 모듈
module "vpc" {
  source = "./modules/vpc"
  
  # TODO: VPC 설정 변수 추가
}

# EKS 모듈
module "eks" {
  source = "./modules/eks"
  
  # TODO: EKS 설정 변수 추가
  # VPC 모듈 출력 참조 필요
}

# Kinesis 모듈
module "kinesis" {
  source = "./modules/kinesis"
  
  # TODO: Kinesis 설정 변수 추가
}

# S3 모듈
module "s3" {
  source = "./modules/s3"
  
  # TODO: S3 버킷 설정 변수 추가
}

# OpenSearch 모듈
module "opensearch" {
  source = "./modules/opensearch"
  
  # TODO: OpenSearch 설정 변수 추가
  # VPC 모듈 출력 참조 필요
}

# ECR 모듈
module "ecr" {
  source = "./modules/ecr"
  
  # TODO: ECR 리포지토리 설정 변수 추가
}

# Secrets Manager 모듈
module "secrets" {
  source = "./modules/secrets"
  
  # TODO: 시크릿 설정 변수 추가
}

# IAM 모듈
module "iam" {
  source = "./modules/iam"
  
  # TODO: IAM 역할 및 정책 설정 변수 추가
  # EKS 모듈 출력 참조 필요 (OIDC Provider)
}
