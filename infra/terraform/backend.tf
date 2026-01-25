# ==============================================================================
# CALI Infrastructure - Terraform Backend Configuration
# ==============================================================================
# S3 원격 State 저장 + DynamoDB Lock (팀 협업용)
# ==============================================================================

# ------------------------------------------------------------------------------
# 주의: 최초 실행 시 아래 S3 버킷과 DynamoDB 테이블을 먼저 생성해야 함
# AWS CLI로 생성:
#   aws s3 mb s3://cali-terraform-state-{ACCOUNT_ID} --region ap-northeast-2
#   aws dynamodb create-table \
#     --table-name cali-terraform-lock \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST \
#     --region ap-northeast-2
# ------------------------------------------------------------------------------

terraform {
  backend "s3" {
    bucket         = "cali-terraform-state"
    key            = "infra/terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "cali-terraform-lock"
  }
}
