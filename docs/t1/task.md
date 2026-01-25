# CALI 프로젝트 Task List

## Phase 0: 프로젝트 초기 설정
- [x] 프로젝트 디렉토리 구조 설계
- [x] 기본 폴더 및 파일 생성
- [ ] Git 리포지토리 초기화

## Phase 0.5: MVP 구현 (LocalStack 로컬 테스트)

### 완료된 작업 ✅
- [x] Fluent Bit Multiline 파서 구현
  - [x] 여러 줄 스택 트레이스 묶음 (`multiline_start`)
  - [x] 헤더 파싱 (타임스탬프, 레벨, 서비스명)
  - [x] 원본 로그 보존 (`log_content` 필드)
  - [x] 듀얼 출력 (Kinesis Stream + Firehose)
- [x] 프로덕션급 로그 시뮬레이터 구현
  - [x] 7개 마이크로서비스 시뮬레이션
  - [x] 8종 실제 에러 시나리오
  - [x] Java/Python 스택 트레이스 (15-30줄)
  - [x] 상세 메타데이터 (Pod, 버전, Request ID)
  - [x] **Faker 라이브러리 도입** (현실적인 데이터 생성)
    - [x] 사용자명, 이메일, IP 주소
    - [x] 주문번호, 트랜잭션 ID, SKU
    - [x] 정확한 Decimal 금액

### 진행 중 🚧
- [ ] Kinesis Consumer 핵심 로직 구현
  - [ ] Kinesis GetRecords 폴링 (`kinesis_consumer.py`)
  - [ ] Pydantic 스키마 검증 (2차 검증)
  - [ ] 검증 실패 시 S3 DLQ 전송
  - [ ] 간단한 룰 기반 분석 (예: ERROR 레벨 시 알림)
- [ ] Slack Notifier 구현
  - [ ] Slack Webhook POST 요청 (`slack_notifier.py`)
  - [ ] Throttling 로직 (윈도우 기반 중복 방지)
  - [ ] 에러 메시지 포맷팅
- [ ] LocalStack 통합 테스트
  - [ ] LocalStack Kinesis Stream 생성
  - [ ] 로그 생성기 → Fluent Bit → Kinesis 파이프라인 테스트
  - [ ] Consumer → Slack 알림 검증
  - [ ] 전체 파이프라인 end-to-end 테스트

### 참고 문서
- `docs/mvp_plan.md`: MVP 단계별 상세 계획
- `apps/fluent-bit/TEST_GUIDE.md`: Fluent Bit 파서 테스트 가이드
- `scripts/local-dev/LOG_GENERATOR_GUIDE.md`: 로그 시뮬레이터 사용법


## Phase 1: 인프라 구축 (Terraform)
- [/] Day 1-1: 기본 인프라 설계 및 Terraform 코드 작성
  - [ ] VPC 및 네트워크 구성
  - [ ] EKS 클러스터 구성
  - [ ] Kinesis Data Stream & Firehose 구성
  - [ ] S3 버킷 (백업/DLQ) 구성
  - [ ] OpenSearch 도메인 구성
  - [ ] ECR 리포지토리 구성
  - [ ] Secrets Manager 구성
  - [ ] IAM 역할 및 정책 구성
- [ ] Day 1-2: Terraform 모듈화 및 변수 관리
- [ ] Day 1-3: GitHub Actions CI/CD 파이프라인 구성

## Phase 2: 로그 수집 파이프라인
- [ ] Day 2-1: Fluent Bit DaemonSet 구성
  - [ ] Regex 파싱 필터 설정
  - [ ] Kinesis 출력 플러그인 설정
- [ ] Day 2-2: 로그 수집 테스트

## Phase 3: 데이터 처리 및 AI 분석
- [ ] Day 3-1: Python Consumer 개발
  - [ ] Kinesis Stream 구독
  - [ ] Pydantic 모델 정의 및 검증
  - [ ] Milvus 벡터 DB 연동
  - [ ] OpenAI RAG 분석 로직
  - [ ] Slack 알림 연동
- [ ] Day 3-2: Dockerize 및 EKS 배포

## Phase 4: 시각화 (Grafana)
- [ ] Day 4-1: Grafana Helm 설치 및 구성
- [ ] Day 4-2: OpenSearch 데이터 소스 연결
- [ ] Day 4-3: 대시보드 구성

## Phase 5: 데이터 품질 및 자동화
- [ ] Day 5-1: Airflow 설치 (Helm)
- [ ] Day 5-2: Great Expectations DAG 작성
- [ ] Day 5-3: Git-Sync/S3 Sync 배포 설정

## Phase 6: 테스트 및 최적화
- [ ] Day 6-1: 전체 통합 테스트
- [ ] Day 6-2: 성능 최적화 및 모니터링
