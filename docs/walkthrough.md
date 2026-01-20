# CALI 프로젝트 초기 구조 생성 완료

## 📋 작업 요약

CALI(Cloud-native AI Log Insight) 프로젝트의 전체 디렉토리 구조와 기본 파일을 생성했습니다.

---

## ✅ 생성된 파일 통계

총 **85개 이상**의 파일이 생성되었습니다.

### 주요 카테고리별 파일 수

| 카테고리 | 파일 수 | 설명 |
|---------|---------|------|
| **Terraform** | 32개 | 인프라 코드 (8개 모듈 × 3파일 + 메인 설정 8개) |
| **Consumer App** | 20개 | Python 애플리케이션 (서비스, 모델, 유틸, 테스트) |
| **Fluent Bit** | 4개 | 로그 수집기 설정 및 Dockerfile |
| **Kubernetes** | 10개 | 매니페스트 (Namespace, DaemonSet, Deployment, Helm) |
| **Airflow** | 6개 | DAG 및 설정 파일 |
| **Scripts** | 5개 | 자동화 스크립트 (설정, 배포, 정리) |
| **CI/CD** | 4개 | GitHub Actions 워크플로우 |
| **문서** | 4개 | README, 구조 설명, 계획서, 작업 체크리스트 |

---

## 📁 디렉토리 구조

```
CALI/
├── .github/workflows/      # CI/CD 파이프라인
├── .gitignore
├── .env.example
├── README.md
│
├── docs/                   # 프로젝트 문서
│   ├── task.md
│   ├── implementation_plan.md
│   └── project_structure.md
│
├── terraform/              # 인프라 코드
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── versions.tf
│   ├── terraform.tfvars
│   ├── backend.tf
│   └── modules/
│       ├── vpc/           # VPC 및 네트워크
│       ├── eks/           # EKS 클러스터
│       ├── kinesis/       # Kinesis Stream & Firehose
│       ├── s3/            # S3 버킷
│       ├── opensearch/    # OpenSearch 도메인
│       ├── ecr/           # ECR 리포지토리
│       ├── secrets/       # Secrets Manager
│       └── iam/           # IAM 역할 및 정책
│
├── apps/                   # 애플리케이션
│   ├── fluent-bit/
│   │   ├── Dockerfile
│   │   ├── fluent-bit.conf
│   │   ├── parsers.conf
│   │   └── filters/
│   │
│   └── consumer/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── main.py
│       ├── config/
│       │   └── settings.py
│       ├── models/
│       │   └── log_schema.py
│       ├── services/
│       │   ├── kinesis_consumer.py
│       │   ├── milvus_client.py
│       │   ├── openai_client.py
│       │   └── slack_notifier.py
│       ├── utils/
│       │   ├── logger.py
│       │   └── throttle.py
│       └── tests/
│
├── k8s/                    # Kubernetes 매니페스트
│   ├── namespaces/
│   ├── fluent-bit/
│   ├── consumer/
│   ├── grafana/
│   └── milvus/
│
├── airflow/                # Airflow 오케스트레이션
│   ├── dags/
│   │   ├── data_quality_check.py
│   │   └── log_aggregation.py
│   ├── plugins/
│   ├── config/
│   ├── docker-compose.yaml
│   ├── Dockerfile
│   └── requirements.txt
│
└── scripts/                # 자동화 스크립트
    ├── setup.sh
    ├── deploy.sh
    ├── cleanup.sh
    └── local-dev/
```

---

## 🎯 주요 컴포넌트별 설명

### 1. Terraform 인프라 (32개 파일)

**8개 모듈로 구성**:
- **VPC**: 3개 가용 영역, Public/Private/Database 서브넷
- **EKS**: Kubernetes 1.31, t3.medium 노드 2-4개
- **Kinesis**: Data Stream(샤드 2개) + Firehose(OpenSearch & S3)
- **S3**: 로그 백업, DLQ, Terraform 상태 저장
- **OpenSearch**: v2.11, t3.small.search 3개 (Multi-AZ)
- **ECR**: Fluent Bit, Consumer, API 이미지 저장소
- **Secrets Manager**: OpenAI API Key, Slack Webhook 등
- **IAM**: IRSA 기반 서비스 계정 역할

각 모듈은 `main.tf`, `variables.tf`, `outputs.tf`로 구성되어 있습니다.

---

### 2. Python Consumer 애플리케이션 (20개 파일)

**역할**: Kinesis 구독 → Pydantic 검증 → RAG 분석 → Slack 알림

**주요 파일**:
- `config/settings.py`: Pydantic Settings로 환경 변수 관리
- `models/log_schema.py`: Pydantic 로그 스키마 (2차 검증)
- `services/kinesis_consumer.py`: Kinesis Stream 구독
- `services/milvus_client.py`: 벡터 검색
- `services/openai_client.py`: RAG 분석
- `services/slack_notifier.py`: Throttling 적용 알림
- `utils/throttle.py`: 윈도우 기반 알림 제어

---

### 3. Fluent Bit 로그 수집기 (4개 파일)

**역할**: EKS 노드의 로그를 수집하여 Kinesis로 전송

- `Dockerfile`: 커스텀 Fluent Bit 이미지
- `fluent-bit.conf`: 메인 설정 (Multi-Output: Stream & Firehose)
- `parsers.conf`: Regex 기반 로그 파싱 규칙

---

### 4. Kubernetes 매니페스트 (10개 파일)

- **Fluent Bit DaemonSet**: 모든 노드에서 로그 수집
- **Consumer Deployment**: 2개 레플리카
- **IRSA ServiceAccount**: IAM 역할 연결
- **Grafana Helm Values**: OpenSearch 데이터 소스 연결
- **Milvus Helm Values**: 벡터 DB 배포

---

### 5. Airflow 오케스트레이션 (6개 파일)

**역할**: 데이터 품질 검증 및 로그 집계

- `dags/data_quality_check.py`: Great Expectations 검증 DAG
- `dags/log_aggregation.py`: 로그 집계 배치 DAG
- `docker-compose.yaml`: 로컬 개발 환경

---

### 6. CI/CD 파이프라인 (4개 파일)

- `terraform.yml`: Terraform 검증 및 자동 배포
- `consumer.yml`: Consumer 이미지 빌드 및 ECR 푸시
- `fluent-bit.yml`: Fluent Bit 이미지 빌드
- `airflow-dags.yml`: DAG 검증 및 S3 동기화

---

### 7. 자동화 스크립트 (5개 파일)

- `setup.sh`: 초기 환경 설정
- `deploy.sh`: Docker 이미지 빌드 및 EKS 배포
- `cleanup.sh`: 리소스 정리
- `local-dev/start-localstack.sh`: AWS 로컬 에뮬레이션
- `local-dev/seed-data.sh`: 테스트 데이터 생성

---

## 📝 각 파일의 특징

### 모든 파일에 주석 포함
- **목적**: 각 파일의 역할 명확화
- **형식**: 파일 상단에 구조화된 주석 블록
- **내용**: 설명, 역할, 사용 방법, TODO 항목

### TODO 마크 포함
- 실제 구현이 필요한 부분은 `TODO` 주석으로 표시
- 다음 단계에서 구현할 내용을 명확히 안내

### 타입 안정성
- Python 코드: Pydantic을 통한 엄격한 타입 검증
- Terraform: 변수 타입 명시

---

## 🎉 완료된 작업

✅ **Phase 0: 프로젝트 초기 설정**
- [x] 프로젝트 디렉토리 구조 설계
- [x] 기본 폴더 및 파일 생성 (85개+)
- [x] Fluent Bit Multiline 파서 및 헤더 파싱 구현
- [x] 프로덕션급 로그 시뮬레이터 구현
- [ ] Git 리포지토리 초기화 (다음 단계)

### ✨ Fluent Bit 스마트 로그 수집

**구현 완료**:
- Multiline 파서: 여러 줄 스택 트레이스를 하나의 이벤트로 묶음
- 헤더 파싱: 타임스탬프, 레벨, 서비스명 추출
- 원본 보존: `log_content` 필드에 전체 로그 저장
- 듀얼 출력: Kinesis Stream + Firehose

### 🎭 프로덕션급 로그 시뮬레이터

**구현 완료**:
- 7개 마이크로서비스 시뮬레이션
- 8종 실제 에러 시나리오 (DB 풀 고갈, Redis 장애, Kafka Lag, OOM 등)
- 상세 메타데이터 (Pod, 버전, Request ID, Correlation ID)
- Java/Python 스택 트레이스 15-30줄 생성

---

## 🚀 다음 단계

### Phase 1: MVP 개발 (Consumer 구현)
1. **Kinesis Consumer 구현**: `apps/consumer/services/kinesis_consumer.py`
2. **Slack Notifier 구현**: `apps/consumer/services/slack_notifier.py`
3. **로컬 통합 테스트**: LocalStack + 로그 생성기 + Consumer

### Phase 2: Terraform 인프라 구축
1. **VPC 모듈 구현**: VPC, 서브넷, NAT Gateway 등 리소스 정의
2. **EKS 모듈 구현**: EKS 클러스터, 노드 그룹, OIDC Provider 구성
3. **Kinesis 모듈 구현**: Data Stream 및 Firehose 리소스
4. **나머지 모듈 구현**: S3, OpenSearch, ECR, Secrets, IAM

### 시작 명령어
```bash
# 초기 설정 (최초 1회)
./scripts/setup.sh

# LocalStack 시작 (개발 세션마다)
./scripts/local-dev/start-localstack.sh

# 로그 생성기 실행
cd scripts/local-dev
python dummy-log-generator.py

# Consumer 구현 후 테스트
cd apps/consumer
python main.py
```

---

## 💡 사용 가이드

### 로컬 개발 환경 구성
```bash
# LocalStack으로 AWS 서비스 에뮬레이션
cd scripts/local-dev
./start-localstack.sh

# Consumer 로컬 테스트
cd apps/consumer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### 테스트 실행
```bash
cd apps/consumer
pytest tests/
```

---

## 📊 파일 생성 통계

- **총 파일 수**: 85개+
- **총 코드 라인**: 약 3,000+ 라인 (주석 포함)
- **주요 언어**: Python, HCL (Terraform), YAML, Shell
- **문서화 수준**: 모든 파일에 상세 주석 포함

---

## ✨ 특징

1. **모듈화된 구조**: 각 컴포넌트가 독립적으로 관리됨
2. **완전한 주석**: 모든 파일에 역할과 용도 명시
3. **테스트 가능**: Pytest 기반 테스트 구조
4. **CI/CD 준비 완료**: GitHub Actions 워크플로우 포함
5. **로컬 개발 지원**: LocalStack으로 AWS 서비스 에뮬레이션

---

이제 Terraform 코드를 실제로 구현하여 AWS 인프라를 구축할 준비가 완료되었습니다! 🎉
