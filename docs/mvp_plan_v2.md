# CALI MVP - 로컬 환경 파이프라인 구현

## 🎯 목표

로컬 환경(LocalStack)에서 핵심 로그 파이프라인을 구축하여 동작 검증

```
로그 생성기 → Fluent Bit → Kinesis (LocalStack) → Consumer → Slack
```

## 📋 MVP 실행 계획

### Step 1: LocalStack + Terraform 인프라 구성 ⏱️ 2시간

**목적**: Terraform으로 LocalStack에 Kinesis Stream 생성

**작업**:
1. Docker Compose에 LocalStack 추가
2. Terraform LocalStack Provider 설정
3. Kinesis Stream 리소스 정의
4. Terraform apply

**결과물**:
- `docker-compose.yml` (LocalStack 서비스)
- `terraform/localstack/main.tf`
- `terraform/localstack/kinesis.tf`

**검증**:
```bash
aws --endpoint-url=http://localhost:4566 kinesis list-streams
# 출력: cali-log-stream
```

---

### Step 2: Fluent Bit LocalStack 연동 ⏱️ 1시간

**목적**: Fluent Bit이 LocalStack Kinesis로 로그 전송

**작업**:
1. `fluent-bit.conf`에 LocalStack endpoint 추가
2. Docker Compose에 Fluent Bit 추가
3. 로그 생성기 → Fluent Bit 연결

**수정 파일**:
- `apps/fluent-bit/fluent-bit.conf` (endpoint 추가)
- `docker-compose.yml` (fluent-bit, log-generator 서비스)

**검증**:
```bash
docker-compose up -d
docker logs fluent-bit  # Kinesis 전송 로그 확인
```

---

### Step 3: Consumer Kinesis 폴링 구현 ⏱️ 3시간

**목적**: Kinesis에서 로그 수신 및 ERROR 필터링

**작업**:
1. LocalStack endpoint 설정
2. Kinesis GetRecords 폴링 루프
3. ERROR/WARN 필터링 (이미 완료)
4. Consumer Docker 이미지 작성

**구현 파일**:
- `apps/consumer/services/kinesis_consumer.py`
- `apps/consumer/config/settings.py` (LocalStack endpoint)
- `apps/consumer/Dockerfile`

**검증**:
```bash
docker-compose up consumer
# Consumer 로그에서 "에러 로그 처리" 확인
```

---

### Step 4: Slack 알림 구현 ⏱️ 2시간

**목적**: ERROR 로그를 Slack으로 전송

**작업**:
1. Slack Webhook URL 설정
2. 간단한 메시지 포맷
3. 기본 Throttling (1분 5개)

**구현 파일**:
- `apps/consumer/services/slack_notifier.py`
- `.env` (SLACK_WEBHOOK_URL)

**검증**:
```bash
# Slack 채널에서 알림 도착 확인
```

---

### Step 5: 통합 테스트 ⏱️ 1시간

**목적**: 전체 파이프라인 End-to-End 검증

**작업**:
1. 전체 서비스 Docker Compose 실행
2. 로그 생성 → Slack 알림 확인
3. ERROR만 알림 오는지 확인

**검증**:
```bash
docker-compose up

# 확인 사항:
# 1. 로그 생성기 실행 중
# 2. Fluent Bit이 Kinesis로 전송
# 3. Consumer가 ERROR 감지
# 4. Slack 알림 도착
```

---

## ✅ MVP 성공 기준

- [ ] LocalStack Kinesis Stream 생성됨 (Terraform)
- [ ] 로그 생성기 → Fluent Bit → Kinesis 전송
- [ ] Consumer가 Kinesis에서 로그 수신
- [ ] ERROR/WARN 로그만 필터링
- [ ] Slack에 알림 도착
- [ ] 모든 것이 로컬 환경에서 동작

---

## 📁 필요한 파일 체크리스트

### 인프라 (Terraform)
- [ ] `terraform/localstack/provider.tf`
- [ ] `terraform/localstack/kinesis.tf`
- [ ] `terraform/localstack/variables.tf`

### Docker 환경
- [ ] `docker-compose.yml` (전체 서비스)
- [ ] `apps/consumer/Dockerfile`
- [x] `scripts/local-dev/Dockerfile.log-generator` (완료)

### 설정 파일
- [ ] `apps/fluent-bit/fluent-bit.conf` (LocalStack endpoint 추가)
- [ ] `apps/consumer/config/settings.py` (LocalStack endpoint)
- [ ] `.env` (환경 변수)

### Consumer 구현
- [ ] `apps/consumer/services/kinesis_consumer.py` (폴링 로직)
- [ ] `apps/consumer/services/slack_notifier.py` (Webhook 전송)
- [x] `apps/consumer/models/log_schema.py` (완료)

---

## 🔧 환경 변수 (.env)

```bash
# LocalStack
LOCALSTACK_ENDPOINT=http://localhost:4566
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test

# Kinesis
KINESIS_STREAM_NAME=cali-log-stream

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Consumer
THROTTLE_MAX_PER_MINUTE=5
```

---

## 📊 Docker Compose 구조

```yaml
services:
  localstack:
    image: localstack/localstack
    # Kinesis 서비스 제공
  
  log-generator:
    build: scripts/local-dev/Dockerfile.log-generator
    # stdout으로 로그 출력
  
  fluent-bit:
    image: fluent/fluent-bit:3.2
    # 로그 수집 → Kinesis 전송
  
  consumer:
    build: apps/consumer/
    # Kinesis 구독 → Slack 알림
```

---

## ⏱️ 총 예상 시간

| Step | 소요 시간 | 누적 |
|------|----------|------|
| 1. LocalStack + Terraform | 2시간 | 2시간 |
| 2. Fluent Bit 연동 | 1시간 | 3시간 |
| 3. Consumer 폴링 | 3시간 | 6시간 |
| 4. Slack 알림 | 2시간 | 8시간 |
| 5. 통합 테스트 | 1시간 | 9시간 |

**총: 약 9시간 (1-2일)**

---

## 🚀 MVP 이후 확장

**v2**: K8s 배포 (EKS + DaemonSet)  
**v3**: S3 + OpenSearch 추가  
**v4**: AI/RAG 분석 추가
