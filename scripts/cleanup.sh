#!/bin/bash
# =====================================================
# CALI 프로젝트 리소스 정리 스크립트
# =====================================================
# 설명: Kubernetes 리소스 및 Terraform 인프라 삭제
# =====================================================

set -e

echo "🗑️  CALI 리소스 정리 시작..."

# 확인
read -p "⚠️  모든 리소스를 삭제하시겠습니까? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "취소되었습니다."
    exit 0
fi

# 1. Kubernetes 리소스 삭제
echo "☸️  Kubernetes 리소스 삭제..."
kubectl delete -f k8s/consumer/ || true
kubectl delete -f k8s/fluent-bit/ || true
kubectl delete -f k8s/namespaces/ || true

# 2. Terraform 인프라 삭제 (옵션)
read -p "Terraform 인프라도 삭제하시겠습니까? (yes/no): " terraform_destroy
if [ "$terraform_destroy" = "yes" ]; then
    echo "🏗️  Terraform 인프라 삭제..."
    cd terraform
    terraform destroy -auto-approve
    cd ..
fi

echo "✅ 정리 완료!"
