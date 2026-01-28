# CALI 프로젝트 진행 리포트 (2026-01-27)

## 1. 개요
Day 2 긴급 인프라 업그레이드 수행. 시스템 안정성(Autoscaling), 스토리지 확장성(StorageClass), 보안(IAM Permissions)을 강화하고 운영 효율화를 위한 자동화 구성을 완료함.

## 2. 주요 진행 사항
### 인프라 코어 업그레이드
- **Cluster Autoscaler 도입 (`infra/terraform/08-autoscaler.tf`)**
    - Terraform을 통한 IAM Role 및 Helm Chart 배포 코드 작성.
    - 노드 리소스 부족 시 자동으로 워커 노드를 확장(Scale-out)할 수 있는 기반 마련.
- **StorageClass `gp2` 기본값 설정 (`infra/k8s/storage-class.yaml`)**
    - `ebs.csi.aws.com` 프로비저너를 사용하는 StorageClass 생성.
    - Milvus, PostgreSQL 등 유상태(Stateful) 애플리케이션의 영구 저장소(PVC) 문제 해결.
    - 파일 위치 재정리: `infra/terraform/` -> `infra/k8s/` (Best Practice 준수).

### 보안 및 협업 환경 개선
- **팀원 EKS 접근 권한 관리 (`infra/terraform/05-eks.tf`)**
    - `terraform.tfvars`를 활용한 안전한 IAM ARN 주입 구조 설계.
    - `aws_eks_access_entry` 리소스를 사용하여 팀원들에게 **Cluster Admin** 권한 자동 부여.
    - GitHub에 민감 정보가 노출되지 않도록 `.tfvars` 파일 분리 및 예제 파일(`example`) 제공.

### 운영 편의성 증대
- **README.md 가이드 업데이트**
    - Terraform 운영, EKS 연결, 각 서비스(Airflow, Milvus 등) 배포 및 트러블슈팅 명령어 완벽 정리.
    - 팀원 전달용 **"EKS 접근 가이드"** 섹션 신설.
- **Fluent Bit 설정 최적화**
    - Kustomization을 통한 ConfigMap 관리로 전환.
    - `@timestamp` 강제 주입 전략 확정.

## 3. 시행착오 및 트러블슈팅 (Troubleshooting)

### 이슈 1: Autoscaler 구성 누락
- **현상**: IAM Role만 생성하고 실제 Autoscaler 파드를 설치하는 Helm 차트 코드가 누락됨.
- **해결**: `providers.tf`에 Helm/Kubernetes 프로바이더 추가 및 `08-autoscaler.tf` 작성하여 설치 자동화 구현.

### 이슈 2: IAM ARN 보안 관리
- **고민**: 팀원 접근 권한 설정 시 IAM ARN이 코드에 하드코딩되면 GitHub에 노출될 위험 존재.
- **해결**: `variables.tf`와 `terraform.tfvars` 패턴을 사용하여 코드와 데이터를 분리. `terraform.tfvars`는 `.gitigonore` 처리하여 로컬에서만 관리하도록 가이드.

### 이슈 3: OpenSearch 권한 모호성
- **확인**: EKS Admin 권한이 있다고 해서 AWS OpenSearch Service에 자동으로 접근 가능한 것은 아님.
- **결론**: 복잡한 IAM 매핑 대신 **Basic Auth(ID/PW)** 방식을 채택하여 팀원 접속 용이성 확보. (비밀번호는 `tfvars`로 관리)

## 4. 향후 과제 (Next Steps) - Day 3 목표
- [ ] **Terraform Apply 완료**: 작성된 모든 인프라 변경 사항 실제 클라우드 반영.
- [ ] **K8s 리소스 배포**: `StorageClass`, Fluent Bit ConfigMap 등 매니페스트 적용.
- [ ] **서비스 전면 기동**: Airflow(GitSync 포함), Milvus, Grafana 헬름 차트 배포 및 연동 테스트.
- [ ] **End-to-End 검증**: 로그 생성부터 분석, 시각화까지 데이터 흐름 최종 확인.

---
**기록자**: CALI Lead SRE (Antigravity)
**상태**: 인프라 확장 준비 완료 (Ready for Deployment)
