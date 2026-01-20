# =====================================================
# CALI 프로젝트 - Terraform 변수 값 설정
# =====================================================
# 설명: 실제 환경에 맞는 변수 값을 설정합니다.
# 주의: 이 파일은 .gitignore에 추가하여 비공개로 관리합니다.
# =====================================================

project_name = "cali"
environment  = "dev"
region       = "ap-northeast-2"

tags = {
  Project     = "CALI"
  Environment = "Development"
  ManagedBy   = "Terraform"
  Team        = "AIOps Engineers"
}

# TODO: 환경별 변수 값 추가
