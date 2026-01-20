# =====================================================
# VPC 모듈 - 메인 설정
# =====================================================
# 설명: VPC, 서브넷, NAT Gateway, Internet Gateway 등 네트워크 인프라 구성
# 구성: 3개 AZ, Public/Private/Database 서브넷
# =====================================================

# TODO: VPC 리소스 정의
# - VPC (10.0.0.0/16)
# - Public 서브넷 3개 (각 AZ당 1개)
# - Private 서브넷 3개 (EKS 워커 노드용)
# - Database 서브넷 3개 (OpenSearch용)
# - Internet Gateway
# - NAT Gateway 3개 (고가용성)
# - Route Tables
