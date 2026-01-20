# 프로덕션급 로그 시뮬레이터 사용 가이드

## 🎯 용도

실제 운영 환경의 에러 패턴을 시뮬레이션하여 데모, 테스트, AI 학습 데이터 생성에 활용합니다.

## ✨ 주요 기능

### 1. 실제 마이크로서비스 아키텍처 시뮬레이션

**7개 서비스**:
- `payment-api`: 결제 처리
- `order-service`: 주문 관리
- `auth-service`: 인증/인가
- `inventory-service`: 재고 관리
- `notification-service`: 알림 발송
- `user-profile-api`: 사용자 프로필
- `analytics-engine`: 분석 엔진

각 서비스마다:
- 버전 정보 (예: `v2.3.1`)
- Pod 인스턴스 (예: `payment-api-7d8f9c-abc123`)

### 2. 프로덕션 에러 시나리오 8종

| 시나리오 | 설명 | 예시 |
|---------|------|------|
| **Database** | 커넥션 풀 고갈 | HikariCP 20/20 active, 100 waiting threads |
| **Payment** | 결제 게이트웨이 타임아웃 | Stripe API no response within 15s |
| **Cache** | Redis 클러스터 장애 | 2/3 nodes available, failover in progress |
| **API** | 외부 API Rate Limit | 1000 req/min quota reached |
| **Auth** | JWT 토큰 검증 실패 | RS256 signature verification error |
| **Inventory** | 재고 동시성 락 타임아웃 | Pessimistic lock timeout after 10s |
| **Message Queue** | Kafka Consumer Lag | 50000 messages behind |
| **Memory** | OutOfMemory | Metaspace 245MB/256MB, 15 Full GC in 5min |

### 3. 상세 메타데이터

모든 로그에 포함:
- Pod 이름 및 버전
- Request ID
- User ID
- Correlation ID (분산 추적)
- 복구 조치 정보

### 4. Java/Python 스택 트레이스

**Java 스타일** (15-30줄):
```
[ERROR] 2026-01-19 15:30:01.234 payment-api/v2.3.1 pod/payment-api-7d8f9c-abc123: 
Connection pool exhausted: unable to acquire connection within 30s timeout
Details: HikariCP connection pool size: 20/20 active, 100 waiting threads
Recovery Action: Auto-retry enabled, circuit breaker: OPEN
java.sql.SQLTransientConnectionException: Connection pool exhausted
    at com.cali.payment.api.service.BusinessService.executeTransaction(BusinessService.java:142)
    at com.cali.payment.api.controller.ApiController.handleRequest(ApiController.java:78)
    at jdk.internal.reflect.GeneratedMethodAccessor542.invoke(Unknown Source)
    at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1032)
Caused by: org.postgresql.util.PSQLException: Connection refused
    at org.postgresql.jdbc.PgConnection.connect(PgConnection.java:234)
    ... 28 more
Thread: http-nio-8080-exec-23, Request: POST /api/v1/payments/8472
```

**Python 스타일** (15-30줄):
```
ERROR: auth-service/v3.1.0 pod/auth-service-9p4q5r-ghi345 
JWT token validation failed: signature verification error
Details: Token issuer: auth-service, Algorithm: RS256, Key ID mismatch
Recovery Action: User session invalidated, re-authentication required
Traceback (most recent call last):
  File "/app/main.py", line 85, in <module>
    app.run()
  File "/app/auth_service/application.py", line 142, in run
    self.process_request(request)
  File "/app/auth_service/handlers.py", line 98, in process_request
    result = self.execute_business_logic(data)
  File "/app/auth_service/services.py", line 267, in execute_business_logic
    return self.validate_token(token)
io.jsonwebtoken.security.SignatureException: JWT token validation failed
Request ID: req-842951, User ID: user-7234, Correlation ID: a3f8b2c1-4d5e-6f7g
```

---

## 🚀 사용 방법

### 방법 1: Python 스크립트 직접 실행

```bash
cd scripts/local-dev

# 기본 설정 (2초 간격, 30% 에러율)
python dummy-log-generator.py

# 커스텀 설정
python dummy-log-generator.py --interval 1 --error-rate 0.5
```

**옵션**:
- `--interval`: 로그 생성 간격 (초, 기본값: 2.0)
- `--error-rate`: 에러 로그 발생 비율 (0.0 ~ 1.0, 기본값: 0.3)

### 방법 2: Docker로 실행

```bash
# 이미지 빌드
docker build -t cali-log-generator -f Dockerfile.log-generator .

# 컨테이너 실행
docker run --name log-gen cali-log-generator

# 실시간 로그 확인
docker logs -f log-gen
```

### 방법 3: Docker Compose와 Fluent Bit 통합

`docker-compose.yml` 예시:
```yaml
version: '3.8'

services:
  log-generator:
    build:
      context: ./scripts/local-dev
      dockerfile: Dockerfile.log-generator
    container_name: cali-log-generator
    
  fluent-bit:
    image: fluent/fluent-bit:3.2
    volumes:
      - ./apps/fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
      - ./apps/fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    depends_on:
      - log-generator
```

실행:
```bash
docker-compose up
```

---

## 🧪 테스트 시나리오

### 시나리오 1: Multiline 파서 테스트
```bash
# 에러율 100%로 설정하여 스택 트레이스만 생성
python dummy-log-generator.py --error-rate 1.0
```
→ Fluent Bit이 15-30줄 에러를 하나로 묶는지 확인

### 시나리오 2: 헤더 파싱 테스트
```bash
# 일반 로그와 에러 로그 혼합
python dummy-log-generator.py --error-rate 0.3
```
→ 파싱된 필드 (`timestamp`, `level`, `service`) 확인

### 시나리오 3: 고부하 테스트
```bash
# 0.1초마다 로그 생성
python dummy-log-generator.py --interval 0.1
```
→ Fluent Bit 성능 및 버퍼링 동작 확인

### 시나리오 4: 프로덕션 데모
```bash
# 0.5초 간격, 50% 에러율로 현실적인 장애 상황 시뮬레이션
python dummy-log-generator.py --interval 0.5 --error-rate 0.5
```
→ 실제 운영 환경 시연용

---

## 📊 출력 예시

### 정상 로그 (INFO)
```
[INFO] 2026-01-19 15:30:01.234 order-service/v1.8.4: Order processed successfully: ORDER-847239 ($234.56, 3 items)
```

### 경고 로그 (WARN)
```
[WARN] 2026-01-19 15:30:05.456 payment-api/v2.3.1: Response time degraded: p95=1250ms (SLA: 500ms)
```

### 에러 로그 (ERROR) - 상세 스택 트레이스
```
[ERROR] 2026-01-19 15:30:10.789 inventory-service/v2.1.5 pod/inventory-service-6t7u8v-mno901: 
Stock synchronization failed: pessimistic lock timeout after 10s
Details: SKU: PROD-8472, Requested: 5, Available: 2, Waitlist: 15 customers
Recovery Action: Transaction rolled back, stock reservation cancelled
org.hibernate.exception.LockAcquisitionException: Stock synchronization failed
    at com.cali.inventory.service.service.BusinessService.executeTransaction(BusinessService.java:342)
    at com.cali.inventory.service.controller.ApiController.handleRequest(ApiController.java:127)
    ...
    at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:1024)
Caused by: javax.persistence.PessimisticLockException: could not execute statement
    at org.postgresql.jdbc.PgConnection.connect(PgConnection.java:189)
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:172)
    ... 21 more
Thread: http-nio-8080-exec-17, Request: POST /api/v1/inventory/4829
```

---

## 💡 활용 팁

1. **AI 학습 데이터 생성**: 다양한 에러 시나리오로 학습 데이터셋 구축
2. **Fluent Bit 파서 검증**: Multiline 및 헤더 파싱 로직 테스트
3. **Consumer 통합 테스트**: 로그 → Kinesis → Consumer → Slack 전체 파이프라인 검증
4. **데모 준비**: 실제 운영 환경처럼 보이는 로그로 시연

---

## 🔧 생성되는 로그 유형

| 유형 | 비율 | 설명 |
|------|-----|------|
| **ERROR** | 30% (기본) | 상세 스택 트레이스 포함 |
| **WARN** | 15% | 성능 저하, 리소스 부족 경고 |
| **INFO** | 55% | 정상 동작 로그 |

---

이제 본 프로젝트 데모 및 테스트를 위한 완벽한 프로덕션급 로그 시뮬레이터가 준비되었습니다! 🎉
