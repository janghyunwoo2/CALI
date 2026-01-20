#!/bin/bash
# =====================================================
# CALI 프로젝트 배포 스크립트
# =====================================================
# 설명: Docker 이미지 빌드 및 EKS 배포
# =====================================================

set -e

echo "🚀 CALI 배포 시작..."

# 환경 변수 로드
source .env

# ECR 로그인
echo "🔐 ECR 로그인..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 1. Fluent Bit 이미지 빌드 및 푸시
echo "🐳 Fluent Bit 이미지 빌드..."
cd apps/fluent-bit
docker build -t cali/fluent-bit:latest .
docker tag cali/fluent-bit:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cali/fluent-bit:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cali/fluent-bit:latest
cd ../..

# 2. Consumer 이미지 빌드 및 푸시
echo "🐳 Consumer 이미지 빌드..."
cd apps/consumer
docker build -t cali/consumer:latest .
docker tag cali/consumer:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cali/consumer:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/cali/consumer:latest
cd ../..

# 3. EKS 배포
echo "☸️  Kubernetes 리소스 배포..."
kubectl apply -f k8s/namespaces/
kubectl apply -f k8s/fluent-bit/
kubectl apply -f k8s/consumer/

echo "✅ 배포 완료!"
echo "확인 명령: kubectl get pods -n cali-system"
