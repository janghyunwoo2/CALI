# =====================================================
# LocalStack Provider 설정
# =====================================================
# 설명: LocalStack을 사용하여 AWS 서비스를 로컬에서 에뮬레이션
# =====================================================

terraform {
  required_version = ">= 1.9.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region                      = "ap-south-1"  # 뭄바이 (실제 AWS 계정과 일치)
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    kinesis = "http://localhost:4566"
  }
}
