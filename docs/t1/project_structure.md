# CALI 프로젝트 디렉토리 구조

## 전체 구조 개요

```
CALI/
├── README.md                          # 프로젝트 소개 및 Quick Start
├── .gitignore                         # Git 무시 파일 설정
├── .env.example                       # 환경 변수 템플릿
│
├── docs/                              # 📚 프로젝트 문서
│   ├── task.md                        # 작업 체크리스트
│   ├── implementation_plan.md         # 구현 계획서
│   ├── project_structure.md           # 이 문서
│   ├── architecture.md                # 시스템 아키텍처 다이어그램
│   └── deployment_guide.md            # 배포 가이드
│
├── terraform/                         # 🏗️ Infrastructure as Code
│   ├── main.tf                        # 메인 설정
│   ├── variables.tf                   # 입력 변수
│   ├── outputs.tf                     # 출력 값
│   ├── versions.tf                    # Provider 버전
│   ├── terraform.tfvars               # 환경별 변수 값
│   ├── backend.tf                     # S3 백엔드 설정
│   │
│   └── modules/                       # Terraform 모듈
│       ├── vpc/                       # VPC 및 네트워크
│       │   ├── main.tf
│       │   ├── variables.tf
│       │   └── outputs.tf
│       ├── eks/                       # EKS 클러스터
│       ├── kinesis/                   # Kinesis Stream & Firehose
│       ├── s3/                        # S3 버킷 (백업/DLQ)
│       ├── opensearch/                # OpenSearch 도메인
│       ├── ecr/                       # ECR 리포지토리
│       ├── secrets/                   # Secrets Manager
│       └── iam/                       # IAM 역할 및 정책
│
├── apps/                              # 🐳 애플리케이션 코드
│   ├── fluent-bit/                    # Fluent Bit 로그 수집기
│   │   ├── Dockerfile
│   │   ├── fluent-bit.conf            # 메인 설정
│   │   ├── parsers.conf               # Regex 파서 정의
│   │   └── filters/                   # 커스텀 필터 스크립트
│   │
│   ├── consumer/                      # Python Consumer (RAG 분석)
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── pyproject.toml             # Poetry 설정 (선택)
│   │   ├── main.py                    # 엔트리포인트
│   │   ├── config/
│   │   │   ├── __init__.py
│   │   │   └── settings.py            # Pydantic Settings
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── log_schema.py          # Pydantic 로그 스키마
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── kinesis_consumer.py    # Kinesis 구독
│   │   │   ├── milvus_client.py       # Milvus 벡터 검색
│   │   │   ├── openai_client.py       # OpenAI RAG 분석
│   │   │   └── slack_notifier.py      # Slack 알림 (Throttling)
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── logger.py              # 구조화된 로깅
│   │   │   └── throttle.py            # 윈도우 기반 집계
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       └── test_services.py
│   │
│   └── api/                           # (향후) REST API 서버
│       ├── Dockerfile
│       ├── requirements.txt
│       └── main.py
│
├── k8s/                               # ☸️ Kubernetes 매니페스트
│   ├── namespaces/
│   │   └── cali-system.yaml          # CALI 전용 네임스페이스
│   │
│   ├── fluent-bit/
│   │   ├── daemonset.yaml             # DaemonSet 배포
│   │   ├── configmap.yaml             # 설정 맵
│   │   └── serviceaccount.yaml        # IRSA 서비스 계정
│   │
│   ├── consumer/
│   │   ├── deployment.yaml            # Consumer 배포
│   │   ├── serviceaccount.yaml        # IRSA 서비스 계정
│   │   └── secrets.yaml               # (외부 시크릿 참조)
│   │
│   ├── grafana/
│   │   ├── values.yaml                # Helm Values
│   │   └── datasources.yaml           # OpenSearch 데이터 소스
│   │
│   └── milvus/
│       └── values.yaml                # Milvus Helm Values
│
├── airflow/                           # 🔄 Apache Airflow
│   ├── dags/                          # DAG 정의
│   │   ├── data_quality_check.py      # Great Expectations 검증
│   │   └── log_aggregation.py         # 로그 집계 배치
│   │
│   ├── plugins/                       # 커스텀 플러그인
│   │   └── great_expectations/
│   │       └── expectations/          # GE 검증 규칙
│   │
│   ├── config/
│   │   └── airflow.cfg                # Airflow 설정
│   │
│   ├── docker-compose.yaml            # 로컬 개발용
│   ├── Dockerfile                     # 커스텀 Airflow 이미지
│   └── requirements.txt               # Airflow 의존성
│
├── scripts/                           # 🛠️ 유틸리티 스크립트
│   ├── setup.sh                       # 초기 환경 설정
│   ├── deploy.sh                      # 배포 스크립트
│   ├── cleanup.sh                     # 리소스 정리
│   └── local-dev/
│       ├── start-localstack.sh        # LocalStack 시작
│       └── seed-data.sh               # 테스트 데이터 생성
│
└── .github/                           # 🚀 GitHub Actions CI/CD
    └── workflows/
        ├── terraform.yml              # 인프라 배포
        ├── consumer.yml               # Consumer 앱 배포
        ├── fluent-bit.yml             # Fluent Bit 이미지 빌드
        └── airflow-dags.yml           # DAG 배포
```

---

## 디렉토리별 설명

### 1. **`docs/`** - 문서화
모든 프로젝트 문서를 중앙화하여 관리합니다.
- `architecture.md`: Mermaid 다이어그램 포함 시스템 설계
- `deployment_guide.md`: 단계별 배포 가이드

### 2. **`terraform/`** - 인프라 코드
모든 AWS 리소스를 코드로 관리합니다.
- **모듈 기반 설계**: 재사용성과 유지보수성 향상
- **백엔드 설정**: S3 + DynamoDB로 상태 관리

### 3. **`apps/`** - 애플리케이션
각 마이크로서비스를 독립적으로 관리합니다.

#### 3.1 **`fluent-bit/`**
- EKS 노드의 로그를 수집하여 Kinesis로 전송
- Regex 기반 1차 정형화

#### 3.2 **`consumer/`**
- Kinesis Stream에서 로그를 구독
- Pydantic으로 2차 검증
- Milvus + OpenAI로 RAG 분석
- Slack 알림 (Throttling 적용)

### 4. **`k8s/`** - Kubernetes 배포
Helm Charts 및 매니페스트를 관리합니다.
- **IRSA**: IAM Roles for Service Accounts 사용
- **Grafana**: OpenSearch 데이터 소스 연결
- **Milvus**: 벡터 DB 배포

### 5. **`airflow/`** - 데이터 오케스트레이션
- **Great Expectations**: S3 데이터 품질 검증
- **KubernetesPodOperator**: EKS 내 Pod로 작업 실행
- **Git-Sync**: DAG 자동 동기화

### 6. **`scripts/`** - 자동화 스크립트
- 초기 설정, 배포, 정리 등 반복 작업 자동화
- 로컬 개발 환경 구성 (LocalStack 등)

### 7. **`.github/workflows/`** - CI/CD
- **인프라**: Terraform 검증 및 배포
- **애플리케이션**: Docker 이미지 빌드 및 ECR 푸시
- **Airflow**: DAG 파일 검증 및 S3 동기화

---

## 개발 워크플로우

### Phase 1: 로컬 개발
```bash
# 1. 로컬 환경 설정
cd scripts/local-dev
./start-localstack.sh

# 2. Consumer 로컬 테스트
cd apps/consumer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Phase 2: 인프라 배포
```bash
# Terraform 초기화 및 배포
cd terraform
terraform init
terraform plan
terraform apply
```

### Phase 3: 애플리케이션 배포
```bash
# EKS 클러스터 연결
aws eks update-kubeconfig --name cali-eks --region ap-northeast-2

# Fluent Bit 배포
kubectl apply -f k8s/fluent-bit/

# Consumer 배포
kubectl apply -f k8s/consumer/

# Grafana 설치
helm install grafana grafana/grafana -f k8s/grafana/values.yaml
```

---

## 파일명 규칙

- **Terraform**: `snake_case` (예: `main.tf`, `data_sources.tf`)
- **Python**: `snake_case` (예: `kinesis_consumer.py`)
- **Kubernetes**: `kebab-case` (예: `fluent-bit-daemonset.yaml`)
- **문서**: `snake_case` (예: `deployment_guide.md`)

---

## 다음 단계

1. ✅ 디렉토리 구조 승인
2. 🔨 실제 폴더 및 기본 파일 생성
3. 📝 Terraform 코드 작성 시작
4. 🐍 Python Consumer 개발
5. ☸️ Kubernetes 매니페스트 작성
