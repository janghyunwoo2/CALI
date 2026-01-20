#!/bin/bash
# =====================================================
# CALI 프로젝트 초기 환경 설정 스크립트
# =====================================================
# 설명: 로컬 개발 환경 구성 및 의존성 설치
# =====================================================

set -e

echo "🚀 CALI 프로젝트 초기 설정 시작..."

# 1. Python 가상환경 생성 (Consumer용)
echo "📦 Python 가상환경 생성..."
cd apps/consumer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cd ../..

# 2. .env 파일 생성
echo "📝 .env 파일 생성..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ .env 파일이 생성되었습니다. 실제 값을 입력해주세요."
else
    echo "⚠️  .env 파일이 이미 존재합니다."
fi

# 3. Terraform 초기화 (옵션)
read -p "Terraform을 초기화하시겠습니까? (y/n): " terraform_init
if [ "$terraform_init" = "y" ]; then
    echo "🏗️  Terraform 초기화..."
    cd terraform
    terraform init
    cd ..
fi

echo "✅ 초기 설정 완료!"
echo ""
echo "다음 단계:"
echo "1. .env 파일에 실제 API 키 및 설정 입력"
echo "2. Terraform으로 인프라 배포: cd terraform && terraform apply"
echo "3. Consumer 실행: cd apps/consumer && python main.py"
