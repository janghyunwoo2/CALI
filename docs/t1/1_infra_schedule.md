# CALI 인프라 5일 개발 일정

> **시작일**: 2026-01-25  
> **담당**: 인프라 (역할 1)  
> **방식**: GitOps 기반 CI/CD 자동화

---

## 📊 일정 요약

| Day | 주제 | 핵심 산출물 |
|-----|------|------------|
| **Day 1** | **Terraform 전체 완성 & 배포** | 모든 AWS 리소스 생성 완료 |
| **Day 2** | K8s 앱 배포 & Helm | Fluent Bit, Consumer, Milvus, Airflow 배포 |
| **Day 3** | CI/CD 파이프라인 | GitHub Actions 4개 완성 |
| **Day 4** | 통합 테스트 & 안정화 | E2E 검증, HPA, 버그 수정 |
| **Day 5** | 프로덕션 & 문서화 | 최종 배포, 운영 가이드 |

---

## 🗓️ Day 1: Terraform 전체 완성 & 배포 (1/25)

### 작업 순서 (의존성 고려)

```
[Phase 1: 기초 설정]
providers.tf → backend.tf

[Phase 2: IAM 먼저 (다른 리소스가 참조)]
06-iam.tf

[Phase 3: 핵심 리소스]
01-kinesis.tf → 02-s3.tf → 03-opensearch.tf

[Phase 4: 컴퓨팅 & 시각화]
05-eks.tf → 04-grafana.tf (AMG + OpenSearch 연결) → 07-ecr.tf

[Phase 5: 출력]
outputs.tf
```

### 상세 작업

| 순서 | 파일 | 리소스 | 예상 시간 |
|------|------|--------|----------|
| 1 | `providers.tf` | AWS Provider, 리전 | 10분 |
| 2 | `backend.tf` | S3 State, DynamoDB Lock | 15분 |
| 3 | `06-iam.tf` | EKS Role, Kinesis Policy, Firehose Role, Grafana Role | 30분 |
| 4 | `01-kinesis.tf` | Stream 1개, Firehose 2개 (S3, OpenSearch) | 45분 |
| 5 | `02-s3.tf` | cali-logs 버킷 (raw/, new_errors/) | 20분 |
| 6 | `03-opensearch.tf` | OpenSearch 도메인 (t3.small) | 30분 |
| 7 | `05-eks.tf` | EKS 클러스터, Node Group | 45분 |
| 8 | `04-grafana.tf` | AWS Managed Grafana (AMG) + OpenSearch 데이터 소스 | 30분 |
| 9 | `07-ecr.tf` | ECR 리포지토리 2개 | 15분 |
| 10 | `outputs.tf` | 팀원 공유용 ARN, Endpoint | 15분 |

**총 예상 시간**: ~4시간 (리소스 생성 대기 포함)

### 핵심 설정값

| 리소스 | 설정 |
|--------|------|
| Kinesis Stream | 샤드 1개, 24h 보존 |
| Firehose #1 | → S3 raw/ (버퍼 60초) |
| Firehose #2 | → OpenSearch (버퍼 60초) |
| S3 | raw/, new_errors/ prefix |
| OpenSearch | t3.small.search, 1노드 |
| EKS | t3.medium, min 2 / max 4 |
| Grafana | AWS Managed Grafana, OpenSearch 데이터 소스 연결 |
| ECR | consumer, log-generator |

### 배포 명령어

```bash
cd infra/terraform

# 1. 초기화
terraform init

# 2. 문법 검증
terraform validate
# 2.1 미리보기
terraform plan

# 3. 배포
terraform apply -auto-approve

# 4. 출력값 확인
terraform output
```

### Day 1 완료 기준

- [ ] `terraform apply` 성공 (에러 0)
- [ ] AWS 콘솔에서 모든 리소스 확인:
  - [ ] Kinesis Stream: Active
  - [ ] Firehose x2: Active
  - [ ] S3 버킷: 생성됨
  - [ ] OpenSearch: Active (20분 소요)
  - [ ] EKS: Active (15분 소요)
  - [ ] **Grafana (AMG): Active, OpenSearch 데이터 소스 연결됨**
  - [ ] ECR: 생성됨
- [ ] `terraform output`으로 ARN/Endpoint 확인
- [ ] 팀원에게 접근 정보 공유

---

## 🗓️ Day 2: K8s 앱 배포 & Helm (1/26)

### 오전: kubectl 설정 & Helm 배포

```bash
# EKS 연결
aws eks update-kubeconfig --name cali-cluster --region ap-northeast-2

# Helm 배포
helm install fluent-bit fluent/fluent-bit -f helm-values/fluent-bit.yaml
helm install milvus milvus/milvus -f helm-values/milvus.yaml
helm install airflow apache-airflow/airflow -f helm-values/airflow.yaml
```

### Helm 배포 대상

| 앱 | Helm Chart | Values 파일 |
|----|------------|-------------|
| Fluent Bit | `fluent/fluent-bit` | `helm-values/fluent-bit.yaml` |
| Milvus | `milvus/milvus` | `helm-values/milvus.yaml` |
| Airflow | `apache-airflow/airflow` | `helm-values/airflow.yaml` |

### 오후: Consumer & 앱 배포

| 대상 | 파일 |
|------|------|
| Consumer | `k8s/consumer-deployment.yaml` |
| Log Generator | `k8s/log-generator-deployment.yaml` |

### Day 2 완료 기준

- [ ] kubectl 연결 성공
- [ ] Fluent Bit DaemonSet 동작
- [ ] Consumer Pod Running
- [ ] Milvus Standalone 동작
- [ ] Airflow Web UI 접근 가능 (localhost:8080)
- [ ] 로그 → Kinesis 흐름 확인

---

## 🗓️ Day 3: CI/CD 파이프라인 (1/27)

### GitHub Actions 워크플로우

| 파일 | 트리거 | 동작 |
|------|--------|------|
| `terraform.yml` | `terraform/**` | plan → apply |
| `helm.yml` | `helm-values/**` | helm upgrade |
| `consumer.yml` | `consumer/**` | build → ECR → kubectl |
| `log-generator.yml` | `log-generator/**` | build → ECR → kubectl |

### Day 3 완료 기준

- [ ] git push → 자동 배포 동작
- [ ] Slack 배포 알림 수신

---

## 🗓️ Day 4: 통합 테스트 & 안정화 (1/28)

### E2E 테스트 (10단계)

```
1. 로그 생성기 → 2. Fluent Bit → 3. Kinesis Stream
→ 4. Firehose → S3 → 5. Firehose → OpenSearch
→ 6. Consumer 폴링 → 7. Pydantic 검증
→ 8. Milvus 검색 → 9. OpenAI 분석 → 10. Slack 알림
```

### 추가 작업

- [ ] HPA 설정 (min 2, max 10, CPU 70%)
- [ ] 성능 테스트 (Latency < 5초)
- [ ] Grafana 대시보드 구성 (OpenSearch 데이터 기반)
- [ ] 버그 수정

### Day 4 완료 기준

- [ ] 전체 파이프라인 안정 동작
- [ ] 성능 기준 충족 (Latency < 5초)
- [ ] Grafana 대시보드 완성

---

## 🗓️ Day 5: 프로덕션 & 문서화 (1/29)

### 작업 목록

- [ ] 프로덕션 시뮬레이션
- [ ] 비용 최적화 검토
- [ ] 배포 가이드 작성
- [ ] 아키텍처 다이어그램 업데이트
- [ ] 팀 데모

### Day 5 완료 기준

- [ ] 프로덕션 시뮬레이션 성공
- [ ] 문서 완성
- [ ] 팀 데모 완료

---

## 📁 Terraform 파일 작업 순서

```
Day 1 (순서대로):
1. providers.tf    # AWS Provider
2. backend.tf      # State 관리
3. 06-iam.tf       # IAM (다른 리소스 의존)
4. 01-kinesis.tf   # Stream + Firehose
5. 02-s3.tf        # S3 버킷
6. 03-opensearch.tf # OpenSearch
7. 05-eks.tf       # EKS 클러스터
8. 04-grafana.tf   # AWS Managed Grafana + OpenSearch 연결
9. 07-ecr.tf       # ECR
10. outputs.tf     # 출력값 정리
```

---

## ⚠️ 주의사항

> **OpenSearch**: 생성에 15-20분 소요, 먼저 apply 권장  
> **EKS**: 생성에 10-15분 소요  
> **Grafana (AMG)**: AWS SSO 설정 필요, OpenSearch 데이터 소스 연결 후 대시보드 구성  
> **IAM**: 다른 리소스보다 먼저 생성해야 참조 가능  
> **Secrets**: API Key는 Secrets Manager 사용, 코드 노출 금지

---

*작성일: 2026-01-25*
