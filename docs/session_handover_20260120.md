# 🔄 CALI MVP 작업 인계서 (2026-01-20)

> **이 문서의 목적**: 프로젝트 시작부터 현재까지의 모든 작업을 새 AI 에이전트에게 전달하여, 마치 같은 대화를 이어가듯 작업을 계속할 수 있도록 합니다.

---

## 📌 프로젝트 개요

### 1. CALI란?
**CALI (Cloud AI Log Intelligence)**는 Kubernetes 환경의 에러 로그를 실시간으로 수집·분석하여 Slack으로 알림을 보내는 지능형 로그 모니터링 시스템입니다.

### 2. 핵심 파이프라인 (최종 목표)
```
마이크로서비스 로그 
  ↓
Fluent Bit (수집·파싱)
  ↓
Kinesis Data Stream (버퍼링)
  ↓
Consumer (Python)
  ↓
├─ RAG 분석 (OpenAI + Milvus) → Slack 알림
└─ S3 백업 + OpenSearch 저장
```

### 3. 현재 진행 상황
- **프로젝트명**: CALI (Cloud AI Log Intelligence)
- **현재 단계**: MVP v2 실행 중 (로컬 전용 5단계 계획)
- **완료**: Step 1 / 5단계
- **목표**: 로그 파이프라인 MVP 구축 (`로그 생성기 → Fluent Bit → Kinesis → Consumer → Slack`)
- **현재 브랜치**: `feat/t1/mvp` (GitHub 푸시 완료)
- **핵심 작업 폴더**: `C:\Users\3571\Desktop\projects\CALI\mvp`

---

## 🏗️ 이전 세션에서 완성된 것들 (MVP 시작 전)

### 1. 프로젝트 구조 생성 (85개 파일)
- Terraform 모듈 골격 (`terraform/modules/`)
- Kubernetes 매니페스트 (`k8s/`)
- Python Consumer 골격 (`apps/consumer/`)
- Airflow DAG 골격 (`airflow/dags/`)
- CI/CD 파이프라인 (`github/workflows/`)

### 2. Fluent Bit 설정 완료 ✅
**파일**: `apps/fluent-bit/fluent-bit.conf`

**주요 기능**:
- ✅ **Multiline 파서**: Java/Python 스택 트레이스 15-30줄을 한 덩어리로 인식
- ✅ **헤더 파싱**: 타임스탬프, 로그 레벨, 서비스명 추출
- ✅ **원본 보존**: `log_content` 필드에 전체 로그 저장
- ✅ **Kinesis 출력**: Fan-out 아키텍처 (Kinesis Stream으로만 전송)

### 3. 로그 생성기 완성 ✅
**파일**: `scripts/local-dev/dummy-log-generator.py`

**주요 기능**:
- ✅ 7개 마이크로서비스 시뮬레이션
- ✅ 8종 실제 에러 시나리오 (DB 커넥션 풀 고갈, OOM 등)
- ✅ **Faker 라이브러리** 사용: 사용자명, IP, 주문번호, 트랜잭션 ID 등 현실적인 데이터 생성
- ✅ Java/Python 스택 트레이스 생성 (15-30줄)
- ✅ 상세 메타데이터 (Pod명, 버전, Request ID)

### 4. Consumer 골격 완성 ✅
**파일**: `apps/consumer/services/kinesis_consumer.py`

**주요 기능**:
- ✅ Pydantic 로그 검증 모델 정의
- ✅ **ERROR/WARN 필터링 로직**: INFO 로그는 스킵, 중요 로그만 처리
- ⏳ Kinesis 폴링 로직 (TODO: boto3 구현 필요)
- ⏳ Slack 알림 (TODO: Webhook 연동 필요)

### 5. 아키텍처 결정사항

#### 📌 Fan-out 아키텍처
**기존**: Fluent Bit → 여러 출력 (Kinesis Stream + Firehose)
**변경**: Fluent Bit → **Kinesis Stream만** → Consumer가 Fan-out

**이유**:
- Consumer에서 데이터 분기 처리 (S3, OpenSearch, RAG)
- Kinesis Stream 하나로 중앙 집중식 관리
- 유연한 Consumer 확장 가능

#### 📌 Consumer 필터링
**전략**: 모든 로그를 Kinesis로 받되, Consumer에서 ERROR/WARN만 처리

**이유**:
- Fluent Bit은 단순하게 유지 (복잡한 필터 로직 제거)
- Consumer에서 동적으로 필터 규칙 변경 가능
- 나중에 INFO 로그도 필요하면 Consumer 코드만 수정

---

## ✅ 오늘 완료한 작업 (Step 1: LocalStack + Terraform 인프라 구성)

### 1. MVP 계획 수립
- `docs/mvp_plan_v2.md` 작성: 로컬 전용 5단계 실행 계획
- AI/RAG, S3, OpenSearch, K8s는 MVP에서 제외하고 핵심 파이프라인에만 집중

### 2. LocalStack 환경 구축
- `mvp/docker-compose.yml` 생성 및 LocalStack 컨테이너 실행
- 초기 볼륨 마운트 오류(`Device busy`) 해결을 위해 볼륨 설정 제거
- **주의**: 현재 LocalStack은 휘발성 설정이므로, `docker-compose down` 시 데이터 소멸

### 3. Terraform 설치 및 설정
- **Terraform 설치**: `winget install Hashicorp.Terraform` (v1.14.3)
- **PATH 설정**: 영구 등록 완료 (`C:\Users\3571\AppData\Local\Microsoft\WinGet\Packages\Hashicorp.Terraform_...`)
- **Provider 설정** (`mvp/terraform/provider.tf`):
  - Region: `ap-south-1` (뭄바이, 사용자의 AWS 강의 계정과 일치)
  - Endpoint: `http://localhost:4566` (LocalStack)
  - Access Key: `test/test` (LocalStack 표준값)

### 4. Kinesis Stream 생성
- `mvp/terraform/kinesis.tf` 작성: `cali-log-stream` 정의
- `terraform init` → `terraform apply` 성공
- **결과 확인**: `kinesis_stream_name = "cali-log-stream"`

### 5. Python 가상환경
- `mvp/venv` 생성 (Python 3.13.5)
- `mvp/requirements.txt` 작성 (boto3, pydantic, requests 등)

---

## 🎓 오늘 학습한 핵심 개념 (사용자가 질문한 내용)

1. **Terraform 동작 원리**: 폴더 내 모든 `.tf` 파일을 자동 스캔하여 하나의 설정으로 합침
2. **Terraform 키워드**: `terraform{}` (준비물), `provider{}` (연결 설정), `resource{}` (실제 생성)
3. **init vs apply**: `init`은 도구 다운로드, `apply`는 실제 리소스 생성
4. **Terraform ↔ LocalStack 관계**: Terraform은 설계자, LocalStack은 가상 AWS 실습장
5. **구축 순서 vs 데이터 흐름**: 데이터는 `Generator→FluentBit→Kinesis`지만, 구축은 `Kinesis→FluentBit→Generator` (받는 쪽 먼저)

---

## 📂 주요 파일 위치

| 파일/폴더 | 설명 |
|-----------|------|
| `docs/mvp_plan_v2.md` | 전체 5단계 MVP 실행 계획서 |
| `mvp/docker-compose.yml` | LocalStack 컨테이너 설정 |
| `mvp/terraform/provider.tf` | Terraform AWS Provider 설정 (LocalStack용) |
| `mvp/terraform/kinesis.tf` | Kinesis Stream 리소스 정의 |
| `mvp/requirements.txt` | Python 의존성 목록 |
| `mvp/venv/` | Python 가상환경 |

---

## 🚀 다음 작업 (Step 2: Fluent Bit LocalStack 연동)

### 해야 할 일
1. `apps/fluent-bit/fluent-bit.conf`에 LocalStack endpoint 추가
2. `mvp/docker-compose.yml`에 Fluent Bit 서비스 추가
3. 로그 생성기 → Fluent Bit → Kinesis 연결 테스트

### Step 2 완료 조건
- 로그 생성기가 만든 로그가 Fluent Bit을 통해 LocalStack Kinesis에 도착하는 것을 확인

---

## 🛠️ 새 컴퓨터에서 환경 세팅 (Quick Start)

```powershell
# 1. 코드 가져오기
git checkout feat/t1/mvp
git pull origin feat/t1/mvp

# 2. Python 가상환경 (선택: 이미 있으면 스킵)
cd mvp
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 3. LocalStack 실행
docker-compose up -d

# 4. Kinesis 다시 생성 (휘발성이므로 필수)
cd terraform
terraform init
terraform apply -auto-approve
```

---

## ⚠️ 주의사항

1. **LocalStack 휘발성**: 현재 설정에서는 `docker-compose down` 시 모든 데이터가 삭제됨
2. **Terraform PATH**: 새 터미널 세션에서는 PATH가 적용되어 있어야 함 (영구 등록 완료)
3. **AWS CLI 미설치**: 현재 사용자 PC에 AWS CLI가 없음. 검증은 Python boto3로 수행

---

## 💬 사용자 선호 스타일

- 모든 설명은 **한국어**로
- 왜 그 과정이 필요한지 **비유와 함께 쉽게 설명** 선호
- 코드 실행 전 **목적과 의미를 먼저 설명**받기를 원함
- 복잡한 작업은 사용자가 직접 타이핑하여 실행하는 것을 선호

---

## 📞 에이전트에게 부탁

> "이 문서를 읽었다면, `feat/t1/mvp` 브랜치에서 **Step 2: Fluent Bit LocalStack 연동**을 시작해주세요. 각 단계의 목적을 쉽게 설명하면서 진행해주시면 감사하겠습니다!"

---

*작성일: 2026-01-20 20:00*
