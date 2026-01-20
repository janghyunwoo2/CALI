# =====================================================
# EKS 모듈 - 메인 설정
# =====================================================
# 설명: EKS 클러스터, 노드 그룹, OIDC Provider 구성
# 버전: Kubernetes 1.31 (최신 안정 버전)
# =====================================================

# TODO: EKS 리소스 정의
# - EKS 클러스터
# - 노드 그룹 (t3.medium 2-4개, Auto Scaling)
# - OIDC Provider (IRSA용)
# - 클러스터 애드온 (VPC CNI, CoreDNS, kube-proxy)
# - CloudWatch 로깅 (API, Audit, Authenticator)
