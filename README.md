# CALI (Cloud-native AI Log Insight)

> **EKS 로그를 실시간 정제 → AI(RAG) 분석 → Slack 알림하는 지능형 로그 분석 플랫폼**

## 📖 프로젝트 소개

CALI는 Kubernetes(EKS) 환경의 방대한 비정형 로그를 실시간으로 정제하고, AI 기반 분석을 통해 장애 원인을 자동으로 파악하여 Slack으로 알림하는 AIOps 플랫폼입니다.

### 핵심 가치
- ⚡ **실시간성**: Fluent Bit → Kinesis → Consumer로 이어지는 Push 방식 파이프라인
- 🤖 **AI 분석**: Milvus + OpenAI RAG를 통한 과거 장애 사례 기반 지능형 추론
- 📊 **시각화**: Grafana + OpenSearch 연동으로 로그 통계 대시보드 제공
- 🏗️ **인프라 자동화**: Terraform + GitHub Actions를 통한 완전 자동화된 배포

---

## 🏗️ 시스템 아키텍처

```
App Logs → Fluent Bit (Multiline 묶음 + 헤더 파싱) → Kinesis Stream/Firehose
                                                      ↓              ↓
                                              Consumer (RAG)   OpenSearch (시각화)
                                                      ↓              ↓
                                              Slack 알림        Grafana
                                                                     ↓
                                                                 S3 백업
```

**Data Flow**:
1. **Fast Path**: Kinesis Stream → Consumer → Milvus 벡터 검색 → OpenAI 분석 → Slack
2. **Slow Path**: Kinesis Firehose → OpenSearch (Grafana 데이터 소스) & S3 백업

---

## 🚀 Quick Start

### 1. 사전 요구사항
- AWS 계정 및 자격 증명
- Terraform >= 1.9.0
- kubectl
- Docker
- Python 3.11

### 2. 초기 설정
```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력

# 초기 설정 스크립트 실행
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 3. 인프라 배포
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 4. 애플리케이션 배포
```bash
# EKS 클러스터 연결
aws eks update-kubeconfig --name cali-eks --region ap-northeast-2

# Kubernetes 리소스 배포
./scripts/deploy.sh
```

---

## 📁 프로젝트 구조

```
CALI/
├── docs/              # 프로젝트 문서
├── terraform/         # 인프라 코드 (VPC, EKS, Kinesis, OpenSearch 등)
├── apps/              # 애플리케이션 (Fluent Bit, Consumer)
├── k8s/               # Kubernetes 매니페스트
├── airflow/           # Airflow DAG (데이터 품질 검증)
├── scripts/           # 자동화 스크립트
└── .github/workflows/ # CI/CD 파이프라인
```

상세 구조는 [`docs/project_structure.md`](docs/project_structure.md)를 참조하세요.

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| **Infrastructure** | AWS (EKS, Kinesis, S3, OpenSearch, ECR), Terraform |
| **Logging** | Fluent Bit (DaemonSet), Multiline 파싱, Regex 헤더 추출, 원본 로그 보존 |
| **Data Processing** | Python 3.11, Pydantic, Boto3 |
| **AI/ML** | OpenAI GPT-4o, Milvus (Vector DB) |
| **Visualization** | Grafana, OpenSearch |
| **Orchestration** | Apache Airflow, Great Expectations |
| **CI/CD** | GitHub Actions |

---

## ✨ 핵심 기능

### 🔍 스마트 로그 수집 (Fluent Bit)

Fluent Bit이 단순 수집을 넘어 **지능형 전처리**를 수행합니다:

1. **Multiline 로그 묶음**: 여러 줄에 걸친 스택 트레이스를 하나의 논리적 이벤트로 통합
2. **헤더 파싱**: 타임스탬프, 로그 레벨, 서비스명만 추출하여 구조화
3. **원본 보존**: `log_content` 필드에 원본 로그 전문 저장 (데이터 유실 방지)
4. **듀얼 출력**: Kinesis Stream (실시간 분석) + Firehose (백업/검색)

**예시**:
```
입력 (3줄):
[ERROR] 2026-01-19 15:30:01 payment-api: Connection pool exhausted
  at com.example.payment.Service.connect(Service.java:42)
  at com.example.Main.run(Main.java:15)

출력 (JSON 1개):
{
  "timestamp": "2026-01-19 15:30:01",
  "level": "ERROR",
  "service": "payment-api",
  "message": "Connection pool exhausted",
  "log_content": { "log": "[전체 원본 로그 3줄]" }
}
```

### 🎭 프로덕션급 로그 시뮬레이터

실제 운영 환경처럼 현실적인 로그를 생성하여 데모 및 테스트에 활용:

- **7개 마이크로서비스** 시뮬레이션 (payment, order, auth, inventory 등)
- **8종 에러 시나리오**: DB 커넥션 풀 고갈, Redis 장애, Kafka Lag, OOM 등
- **상세 메타데이터**: Pod 이름, 버전, Request ID, Correlation ID 포함
- **Java/Python 스택 트레이스**: 실제 프레임워크 에러처럼 15-30줄 출력

### 🤖 RAG 기반 AI 분석

- Milvus에 저장된 과거 장애 사례와 현재 로그 비교
- OpenAI GPT-4o를 통한 원인 분석 및 조치 권고안 생성
- 할루시네이션 방지: 실제 데이터 기반 응답만 생성

### 📊 데이터 검증 및 시각화

**2차 검증 (Consumer)**:
- Consumer에서 Pydantic으로 2차 검증
- 검증 실패 시 S3 DLQ(Dead Letter Queue)로 격리

**Grafana 시각화**:
- OpenSearch를 데이터 소스로 연결
- 에러 빈도, 서비스별 통계 대시보드
- 실시간 로그 검색 및 필터링

**Throttling 알림**:
- 윈도우 기반 집계로 동일 에러 폭주 시 Slack 알림 최적화
- 중복 알림 방지 및 비용 절감

**데이터 품질 보증**:
- Airflow + Great Expectations를 통한 S3 데이터 검증
- 무결성 리포트 자동 생성

---

## 📚 문서

- [프로젝트 구조](docs/project_structure.md): 상세 디렉토리 구조 및 각 컴포넌트 설명
- [구현 계획서](docs/implementation_plan.md): Terraform 인프라 구축 계획
- [작업 체크리스트](docs/task.md): 단계별 작업 진행 상황
- [MVP 계획](docs/mvp_plan.md): MVP 단계별 실행 계획
- [Fluent Bit 테스트 가이드](apps/fluent-bit/TEST_GUIDE.md): Multiline 파서 및 헤더 파싱 테스트
- [로그 생성기 가이드](scripts/local-dev/LOG_GENERATOR_GUIDE.md): 프로덕션급 로그 시뮬레이터 사용법

---

## 🧪 로컬 개발 환경

### LocalStack으로 AWS 서비스 로컬 에뮬레이션

```bash
cd scripts/local-dev
./start-localstack.sh

# Kinesis Stream 생성
aws --endpoint-url=http://localhost:4566 kinesis create-stream \
  --stream-name cali-log-stream --shard-count 1
```

### 프로덕션급 로그 시뮬레이터 실행

```bash
cd scripts/local-dev

# 기본 설정 (2초 간격, 30% 에러율)
python dummy-log-generator.py

# 고부하 테스트 (0.5초 간격, 50% 에러율)
python dummy-log-generator.py --interval 0.5 --error-rate 0.5

# Docker로 실행
docker build -t cali-log-generator -f Dockerfile.log-generator .
docker run --name log-gen cali-log-generator
```

### Consumer 로컬 테스트

```bash
cd apps/consumer
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 환경 변수 설정
export KINESIS_STREAM_NAME=cali-log-stream
export KINESIS_ENDPOINT=http://localhost:4566

python main.py
```

### 테스트 실행
```bash
cd apps/consumer
pytest tests/
```

---

## 🧪 개발 & 테스트

### 로컬 개발 환경
```bash
# LocalStack 시작 (AWS 서비스 에뮬레이션)
cd scripts/local-dev
./start-localstack.sh

# 테스트 데이터 생성
./seed-data.sh

# Consumer 로컬 실행
cd apps/consumer
python main.py
```

### 테스트 실행
```bash
cd apps/consumer
pytest tests/
```

---

## 🚦 CI/CD 파이프라인

### Terraform 인프라
- PR 생성 시: `terraform plan` 자동 실행
- main 브랜치 머지 시: `terraform apply` 자동 배포

### 애플리케이션 (Fluent Bit, Consumer)
- 코드 변경 시: Docker 이미지 빌드 및 ECR 푸시
- 자동 배포 (옵션)

### Airflow DAG
- DAG 파일 검증 및 S3 동기화

### 테스트 실행
```bash
cd apps/consumer
pytest tests/
```

---

## 🚦 CI/CD 파이프라인

### Terraform 인프라
- PR 생성 시: `terraform plan` 자동 실행
- main 브랜치 머지 시: `terraform apply` 자동 배포

### 애플리케이션 (Fluent Bit, Consumer)
- 코드 변경 시: Docker 이미지 빌드 및 ECR 푸시
- 자동 배포 (옵션)

### Airflow DAG
- DAG 파일 검증 및 S3 동기화

---

## 🤝 기여 가이드

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## 👥 팀

**AIOps 엔지니어즈**
- 팀원A
- 팀원B

---

## 📞 문의

프로젝트 관련 문의사항은 Issue를 통해 남겨주세요.
