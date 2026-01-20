# =====================================================
# CALI 프로젝트 - Terraform 백엔드 설정
# =====================================================
# 설명: Terraform 상태 파일을 S3에 저장하고 DynamoDB로 잠금 관리
# 목적: 팀 협업 시 상태 파일 동기화 및 동시 수정 방지
# =====================================================

# terraform {
#   backend "s3" {
#     bucket         = "cali-terraform-state"
#     key            = "terraform.tfstate"
#     region         = "ap-northeast-2"
#     dynamodb_table = "cali-terraform-lock"
#     encrypt        = true
#   }
# }

# TODO: S3 버킷과 DynamoDB 테이블을 먼저 수동으로 생성한 후 주석 해제
