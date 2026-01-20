# CALI MVP(Minimum Viable Product) 개발 브리핑

## 🎯 현재 상황

### ✅ 완료된 것
- 📁 **프로젝트 구조 완성**: 85개 파일 생성 (Terraform, Python, K8s, Airflow, CI/CD)
- 📝 **모든 파일에 주석**: 역할 및 TODO 명시
- ⚙️ **VS Code 환경**: 확장 및 설정 완료
- 📚 **문서화**: README, 구조 설명, 계획서, 체크리스트
- ✅ **Fluent Bit 설정**: Multiline 파서 + 헤더 파싱 완료
  - **Fan-out 아키텍처 적용** (2026-01-20 변경)
    - Fluent Bit → Kinesis Stream만 전송 (단일 진입점)
    - Kinesis Stream → Consumer & Firehose로 자동 분배
    - 네트워크 효율 50% 향상 (이전: 2번 전송 → 현재: 1번 전송)
- ✅ **더미 로그 생성기**: MVP 테스트용 프로덕션급 로그 시뮬레이터 완성
  - 7개 마이크로서비스 시뮬레이션
  - 8종 실제 에러 시나리오 (DB, Payment, Cache 등)
  - Java/Python 스택 트레이스 (15-30줄)
  - **Faker 라이브러리 도입** (2026-01-20)
    - 현실적인 데이터: 사용자명, IP, 주문번호, 트랜잭션 ID
    - INFO 로그에서 주로 사용
    - ERROR 로그는 하드코딩 + random 조합
- ✅ **Consumer ERROR/WARN 필터링** (2026-01-20 추가)
  - 모든 로그 수신하지만 ERROR/WARN만 처리
  - INFO 로그는 자동 스킵

### ❌ 아직 안 된 것
- ⚠️ **Terraform 코드**: Fan-out 설계 완료, 실제 리소스 구현 대기 (TODO)
- ⚠️ **Python Consumer**: ERROR 필터링 완료, Kinesis 폴링 로직 구현 필요
- ⚠️ **AWS 인프라**: 배포 안 됨 (LocalStack으로 로컬 테스트 예정)
- ⚠️ **테스트**: 작성되지 않음

---

## 🚀 MVP 목표 (48시간 내)

핵심 파이프라인만 작동시키기:

```
테스트 로그 → Kinesis → Consumer → Slack 알림
              ↓
           S3 백업
```

**제외 항목** (나중에):
- ❌ OpenSearch & Grafana 시각화
- ❌ Milvus & RAG (간단한 룰 기반 분석으로 대체)
- ❌ Airflow & Great Expectations
- ❌ EKS (로컬 Docker로 테스트)

---

## 📋 MVP 단계별 실행 계획

### Phase 1: 기본 인프라 (Terraform) ⏱️ 4-6시간

**목표**: Kinesis + S3만 먼저 구축

#### 체크리스트:
- [ ] VPC 모듈 구현 (간소화 버전)
- [ ] Kinesis Data Stream 생성
- [ ] S3 백업 버킷 생성
- [ ] IAM 역할 (Kinesis 접근용)
- [ ] Terraform 배포 테스트

#### 검증:
```bash
aws kinesis list-streams
aws s3 ls
```

---

### Phase 2: Python Consumer 핵심 로직 ⏱️ 6-8시간

**목표**: Kinesis 구독 → 로그 검증 → Slack 알림

#### 체크리스트:
- [/] `kinesis_consumer.py` 실제 구현
  - [ ] Kinesis GetRecords 폴링
  - [x] Pydantic 검증 (골격 완료)
  - [x] **ERROR/WARN 필터링** (2026-01-20 완료)
    - 모든 로그 수신 → ERROR/WARN만 처리
    - INFO 로그 자동 스킵
  - [ ] DLQ 처리 (S3)
- [ ] `slack_notifier.py` 실제 구현
  - [ ] Webhook 전송
  - [ ] Throttling 적용
- [x] **간단한 룰 기반 분석** (RAG 대신) - 기본 완료
  - ERROR/WARN 레벨 필터링 완료
  - [ ] 특정 키워드 매칭 (선택사항)

#### 검증:
```bash
# 로컬 테스트
python apps/consumer/main.py
```

---

### Phase 3: 로컬 테스트 환경 ⏱️ 2-3시간

**목표**: LocalStack으로 AWS 서비스 에뮬레이션

#### 체크리스트:
- [x] 더미 로그 생성기 구현 (`dummy-log-generator.py`)
  - 다양한 로그 레벨 (INFO, WARN, ERROR)
  - Multiline 스택 트레이스 생성
  - 커스터마이징 가능 (간격, 에러율)
- [ ] LocalStack Kinesis 설정
- [ ] Consumer 로컬 실행
- [ ] Slack 알림 수신 확인

#### 검증:
```bash
./scripts/local-dev/start-localstack.sh

# 더미 로그 생성 (옵션 1: Python 직접 실행)
cd scripts/local-dev
python dummy-log-generator.py --interval 2 --error-rate 0.3

# 더미 로그 생성 (옵션 2: Docker)
docker build -t cali-log-generator:test -f Dockerfile.log-generator .
docker run --name log-gen cali-log-generator:test

# Slack에 알림 도착 확인
```

---

### Phase 4: Fluent Bit 로그 수집 ⏱️ 3-4시간

**목표**: 로그 수집 및 Kinesis 전송

#### 체크리스트:
- [x] Fluent Bit 설정 완료
  - Multiline 파서 (여러 줄 에러 묶기)
  - 헤더 파싱 (시간, 레벨, 서비스명)
  - 원본 로그 보존 (`log_content`)
  - Kinesis 출력 (Stream & Firehose)
- [ ] Docker Compose로 로컬 테스트
  - Fluent Bit 컨테이너
  - 더미 로그 생성기 컨테이너

#### 검증:
```bash
# 더미 로그 생성기 + Fluent Bit 통합 테스트
docker-compose up
# Fluent Bit이 로그 수집 → 파싱 → Kinesis 전송 확인
# Slack 알림 확인
```

---

### Phase 5: AWS 실제 배포 ⏱️ 4-6시간

**목표**: 실제 AWS에 배포 및 통합 테스트

#### 체크리스트:
- [ ] Terraform apply (실제 AWS)
- [ ] Consumer Docker 이미지 빌드 및 ECR 푸시
- [ ] EC2 또는 로컬에서 Consumer 실행
  - (EKS는 나중에, 먼저 단순하게)
- [ ] 실제 AWS Kinesis로 로그 전송

#### 검증:
```bash
# 실제 Kinesis Stream에 데이터 전송
aws kinesis put-record --stream-name cali-log-stream --data ...
# Slack 알림 수신
# S3에 백업 데이터 확인
```

---

### Phase 6: 최소 문서화 ⏱️ 1-2시간

**목표**: MVP 데모 및 사용법 정리

#### 체크리스트:
- [ ] MVP Demo 문서 작성
- [ ] 스크린샷 (Slack 알림, S3 백업)
- [ ] 알려진 제한사항 정리
- [ ] 다음 단계 계획

---

## 📊 MVP 우선순위 요약

| 우선순위 | 컴포넌트 | MVP 포함 | 나중에 |
|---------|---------|---------|--------|
| 🥇 1위 | Kinesis Stream | ✅ | - |
| 🥇 1위 | S3 백업 | ✅ | - |
| 🥇 1위 | Python Consumer | ✅ (간단 버전) | RAG 추가 |
| 🥇 1위 | Slack 알림 | ✅ | - |
| 🥈 2위 | Fluent Bit | ✅ (최소 설정) | 고급 필터 |
| 🥉 3위 | VPC & IAM | ✅ (간소화) | 완전 구성 |
| ❌ 나중에 | OpenSearch | - | ✅ |
| ❌ 나중에 | Grafana | - | ✅ |
| ❌ 나중에 | Milvus & RAG | - | ✅ |
| ❌ 나중에 | EKS | - | ✅ |
| ❌ 나중에 | Airflow & GE | - | ✅ |

---

## 🛠️ 개발 전략

### 1. **Bottom-Up 접근**
- 작은 단위부터 완성
- 각 단계마다 검증
- 통합은 마지막에

### 2. **로컬 우선**
- LocalStack으로 AWS 에뮬레이션
- 비용 절감 및 빠른 반복

### 3. **간소화**
- VPC: 단일 AZ, Public 서브넷만
- Kinesis: 샤드 1개
- Consumer: 단일 인스턴스
- 분석: 룰 기반 (RAG 나중에)

---

## 🚨 주의사항

### 비용 관리
- **Kinesis**: 샤드당 시간 과금 ($0.015/시간)
- **S3**: 거의 무료 (GB당 $0.023)
- **예상 비용**: 하루 $1 미만

### 개발 시간 배분
```
Day 1 (24시간):
  - Phase 1: Terraform (6시간)
  - Phase 2: Consumer (8시간)
  - Phase 3: 로컬 테스트 (3시간)
  - 나머지: 디버깅 & 휴식

Day 2 (24시간):
  - Phase 4: Fluent Bit (4시간)
  - Phase 5: AWS 배포 (6시간)
  - Phase 6: 문서화 (2시간)
  - 나머지: 최종 검증 & 데모 준비
```

---

## 🎯 첫 번째로 할 일

### Option A: Terraform부터 시작 (추천)
**이유**: 인프라가 있어야 Consumer 테스트 가능

```bash
# 1. VPC & Kinesis 모듈 구현
cd terraform/modules/vpc
# main.tf 작성

cd ../kinesis
# main.tf 작성

# 2. 로컬 검증
terraform init
terraform plan
```

### Option B: Consumer부터 시작
**이유**: LocalStack으로 먼저 로직 완성 후 배포

```bash
# 1. LocalStack 실행
./scripts/local-dev/start-localstack.sh

# 2. Consumer 구현
cd apps/consumer
# kinesis_consumer.py 작성
python main.py
```

---

## 💡 추천 순서

**제 추천은 Option B (Consumer 먼저)**입니다!

### 이유:
1. ✅ LocalStack으로 빠른 반복 가능
2. ✅ AWS 비용 발생 없음
3. ✅ 로직 완성 후 Terraform 배포가 더 안전
4. ✅ 문제 발견 시 롤백 쉬움

### 다음 단계:
```bash
# Step 1: LocalStack 시작
./scripts/local-dev/start-localstack.sh

# Step 2: Kinesis Stream 생성
aws --endpoint-url=http://localhost:4566 kinesis create-stream \
  --stream-name cali-log-stream --shard-count 1

# Step 3: Consumer 구현 시작
cd apps/consumer
# 코드 작성...
```

---

## 📞 준비되셨나요?

어떤 방법으로 시작하시겠습니까?

1. **🔧 Terraform부터** - 인프라 먼저 구축
2. **🐍 Consumer부터** - 로직 먼저 완성 (추천)
3. **🤔 다른 방법** - 말씀해주세요!

선택하시면 바로 시작하겠습니다! 🚀
