# CALI Simulated Log Cases – Business Logic / Microservices (SAGA / Event / Consistency / RateLimit) 01–100
# 핀테크 도메인(주문/결제/지갑/정산/포인트/리스크) 기준
# 핵심 축: 사가(보상 트랜잭션), 이벤트 기반 아키텍처, 분산 정합성, 중복/유실, 레이트리밋/쿼터, 장애 전파

---

## 01. Saga Orchestrator Timeout
---
service: saga-orchestrator
error_message: saga step timeout exceeded
---
### Incident Summary
[ERROR] 2024-05-01T10:00:00.101Z saga-orchestrator/v3.0.0 [biz-001]: saga step timeout exceeded | Context: {Saga="order_checkout", Step="reserve_inventory", Timeout="5s", OrderId="o-7712"}

### Root Cause
다운스트림(inventory-service) 지연/타임아웃으로 사가 스텝이 제한 시간 내 완료되지 못함.

### Action Items
1. (즉시) 해당 Step 호출 대상 서비스의 P95/P99 지연 및 에러율 확인.
2. (완화) 타임아웃/재시도(backoff+jitter) 재조정, 큐잉 전환 검토.
3. (재발방지) 스텝별 SLO 정의 + 서킷브레이커 + 비동기 사가 전환.

---

## 02. Saga Compensation Failed
---
service: saga-orchestrator
error_message: compensation transaction failed
---
### Incident Summary
[CRITICAL] 2024-05-01T10:01:00.000Z saga-orchestrator/v3.0.0 [biz-002]: compensation transaction failed | Context: {Saga="order_checkout", FailedStep="capture_payment", Compensate="release_inventory", Reason="inventory 500", OrderId="o-7712"}

### Root Cause
보상 트랜잭션(release_inventory)이 실패하여 중간 상태가 남음(재고 홀드/결제 상태 불일치 가능).

### Action Items
1. (즉시) 보상 트랜잭션을 재시도 가능한 작업 큐로 이관(무한루프 방지).
2. (완화) 보상 실패 시 수동 처리 티켓/알림 생성.
3. (재발방지) 보상 로직 멱등성 보장 + DLQ + 런북/플레이북.

---

## 03. Saga State Corrupted
---
service: saga-orchestrator
error_message: saga state machine invalid transition
---
### Incident Summary
[ERROR] 2024-05-01T10:02:00.000Z saga-orchestrator/v3.0.0 [biz-003]: invalid transition | Context: {Saga="order_checkout", From="PAYMENT_CAPTURED", To="PAYMENT_AUTHORIZED", OrderId="o-9001"}

### Root Cause
이벤트 순서 역전/중복 처리로 상태 머신이 불가능한 전이를 시도.

### Action Items
1. (즉시) 이벤트에 sequence/version을 추가해 순서 보장 또는 재정렬.
2. (완화) 상태 머신에 “late/out-of-order” 이벤트 처리 규칙 추가(무시/보류).
3. (재발방지) 이벤트 계약(스키마+순서) 및 통합 테스트 강화.

---

## 04. Duplicate Event Processed (At-least-once)
---
service: order-service
error_message: duplicate event detected
---
### Incident Summary
[WARN] 2024-05-01T10:03:00.000Z order-service/v4.2.1 [biz-004]: duplicate event detected | Context: {EventId="evt-11aa", Topic="payments", OrderId="o-7712", Seen="true"}

### Root Cause
메시지 브로커는 at-least-once 보장을 제공 → 컨슈머가 중복 이벤트를 수신.

### Action Items
1. (즉시) EventId 기반 dedup 저장소(캐시/DB)로 중복 처리 차단.
2. (완화) 핸들러를 멱등하게 구현(현재 상태면 no-op).
3. (재발방지) dedup TTL/키 규칙 표준화 + 중복률 모니터링.

---

## 05. Event Lost Suspected (Gap in Sequence)
---
service: settlement-service
error_message: event sequence gap detected
---
### Incident Summary
[ERROR] 2024-05-01T10:04:00.000Z settlement-service/v2.9.0 [biz-005]: event sequence gap detected | Context: {Stream="ledger-events", Partition="7", ExpectedSeq="1881", ReceivedSeq="1884"}

### Root Cause
컨슈머 오프셋 점프/재처리 설정 오류 또는 브로커 장애로 이벤트 유실/스킵 의심.

### Action Items
1. (즉시) 브로커 레벨(오프셋, retention, DLQ) 및 컨슈머 재밸런스 로그 확인.
2. (완화) missing seq 범위 재플레이(replay) 또는 원장 재구성 잡 실행.
3. (재발방지) sequence/offset 감시 + 재플레이 런북 + 보존기간 관리.

---

## 06. Outbox Publish Lag High
---
service: outbox-publisher
error_message: outbox backlog exceeds threshold
---
### Incident Summary
[WARN] 2024-05-01T10:05:00.000Z outbox-publisher/v1.6.0 [biz-006]: outbox backlog exceeds threshold | Context: {Table="order_outbox", Backlog="1.2M", PublishRate="slow"}

### Root Cause
Outbox 퍼블리셔 처리량 부족/DB 슬로우쿼리로 이벤트 발행이 지연.

### Action Items
1. (즉시) 퍼블리셔 스케일아웃, 배치 사이즈/폴링 주기 튜닝.
2. (완화) outbox 테이블 인덱스/파티셔닝 점검.
3. (재발방지) outbox SLO/알람 + DLQ + 재처리 도구.

---

## 07. Outbox Duplicate Publish
---
service: outbox-publisher
error_message: duplicate publish detected
---
### Incident Summary
[WARN] 2024-05-01T10:06:00.000Z outbox-publisher/v1.6.0 [biz-007]: duplicate publish detected | Context: {EventId="evt-77cc", Cause="retry without lock", Topic="orders"}

### Root Cause
퍼블리셔가 락/마킹 없이 재시도하여 동일 이벤트를 여러 번 발행.

### Action Items
1. (즉시) outbox row-level 락(SELECT FOR UPDATE SKIP LOCKED) 적용.
2. (완화) 발행 성공 마킹(상태/발행시각) 트랜잭션 처리.
3. (재발방지) 퍼블리셔 멱등성 + 중복 발행 지표.

---

## 08. Consumer Idempotency Store Down
---
service: payment-consumer
error_message: idempotency store unavailable
---
### Incident Summary
[ERROR] 2024-05-01T10:07:00.000Z payment-consumer/v3.4.0 [biz-008]: idempotency store unavailable | Context: {Store="redis", Operation="SETNX", EventId="evt-91aa"}

### Root Cause
Dedup 저장소(보통 Redis) 장애로 멱등 처리 불가 → 중복 처리 위험.

### Action Items
1. (즉시) 멱등 저장소 복구 또는 DB 기반 fallback(제약조건/UPSERT) 사용.
2. (완화) 멱등 불가 시 소비를 일시 중단하고 DLQ로 보내기(안전 우선).
3. (재발방지) 멱등 저장소 HA + fallback 전략 문서화.

---

## 09. Exactly-Once Assumption Violation
---
service: ledger-service
error_message: non-idempotent handler executed twice
---
### Incident Summary
[CRITICAL] 2024-05-01T10:08:00.000Z ledger-service/v6.0.1 [biz-009]: non-idempotent handler executed twice | Context: {EventId="evt-5001", Effect="double ledger entry", Amount="12000"}

### Root Cause
핸들러가 “exactly-once”를 가정해 중복 수신 시 부작용(원장 중복 기록) 발생.

### Action Items
1. (즉시) 원장 엔트리에 unique constraint(EventId) 추가, 중복 보정 스크립트 실행.
2. (완화) 이벤트 처리 멱등화(현재 상태 검사 후 no-op).
3. (재발방지) “at-least-once” 전제 교육/가이드 + 통합 테스트.

---

## 10. Payment Captured But Order Not Confirmed (Inconsistency)
---
service: reconciliation-job
error_message: payment-order inconsistency detected
---
### Incident Summary
[ERROR] 2024-05-01T10:09:00.000Z reconciliation-job/v1.2.0 [biz-010]: payment captured but order not confirmed | Context: {OrderId="o-7712", Payment="CAPTURED", Order="PENDING", Age="15m"}

### Root Cause
결제 성공 이벤트 유실/지연 또는 order-service 처리 실패로 상태 불일치.

### Action Items
1. (즉시) PG 상태 조회로 결제 확정 여부 확인 후 order 상태 강제 동기화(런북).
2. (완화) “pending confirmation” 상태로 사용자 안내.
3. (재발방지) 이벤트 재전송/리플레이 + 정합성 배치(reconciliation) 주기화.

---

## 11. Inventory Reserved But Payment Failed
---
service: reconciliation-job
error_message: inventory reserved but payment failed
---
### Incident Summary
[WARN] 2024-05-01T10:10:00.000Z reconciliation-job/v1.2.0 [biz-011]: inventory reserved but payment failed | Context: {OrderId="o-8801", Inventory="RESERVED", Payment="FAILED", Age="10m"}

### Root Cause
사가 중간 실패 후 보상(release_inventory) 미실행/실패.

### Action Items
1. (즉시) 재고 홀드 해제 보상 작업 재시도/수동 처리.
2. (재발방지) 보상 실패 DLQ + 자동 재처리 워커.

---

## 12. Wallet Balance Negative (Race Condition)
---
service: wallet-service
error_message: balance cannot be negative
---
### Incident Summary
[ERROR] 2024-05-01T10:11:00.000Z wallet-service/v5.0.0 [biz-012]: balance cannot be negative | Context: {UserId="u-9912", Before="1000", Debit="12000", Concurrency="high"}

### Root Cause
동시 차감 경쟁으로 잔액 검증이 원자적으로 보장되지 않음(레이스).

### Action Items
1. (즉시) DB 트랜잭션에서 SELECT FOR UPDATE 또는 버전 기반 낙관적 락 적용.
2. (완화) 지갑 작업을 사용자 단위 큐(serialize)로 처리.
3. (재발방지) 원장 기반 잔액 계산 + 정합성 검증 잡.

---

## 13. Ledger Append Failed (DB Timeout)
---
service: ledger-service
error_message: ledger append timeout
---
### Incident Summary
[ERROR] 2024-05-01T10:12:00.000Z ledger-service/v6.0.1 [biz-013]: ledger append timeout | Context: {TxId="tx-77aa", Timeout="2s", Retries="3"}

### Root Cause
원장 DB 지연/락 경합으로 기록 실패 → 결제/정산 경로에서 장애 전파.

### Action Items
1. (즉시) 원장 기록을 큐 기반 비동기로 전환(필요 시 임시 버퍼).
2. (완화) 타임아웃/재시도 정책을 “안전 멱등”으로 조정.
3. (재발방지) 원장 SLO/용량 계획 + 핫 파티션/인덱스 최적화.

---

## 14. Event Schema Validation Failed
---
service: event-gateway
error_message: event schema validation failed
---
### Incident Summary
[ERROR] 2024-05-01T10:13:00.000Z event-gateway/v2.0.0 [biz-014]: schema validation failed | Context: {Topic="payments", Field="amount", Expected="int64", Got="string"}

### Root Cause
프로듀서/컨슈머 스키마 버전 불일치(호환성 깨짐).

### Action Items
1. (즉시) 스키마 레지스트리/버전 확인, 프로듀서 롤백 또는 핫픽스.
2. (완화) 컨슈머는 구버전 필드 처리(backward compatible) 구현.
3. (재발방지) 스키마 호환성 게이트 + CI 계약 테스트.

---

## 15. Event Version Unsupported
---
service: payment-consumer
error_message: unsupported event version
---
### Incident Summary
[ERROR] 2024-05-01T10:14:00.000Z payment-consumer/v3.4.0 [biz-015]: unsupported event version | Context: {Event="PaymentCaptured", Version="3", Supported="1-2"}

### Root Cause
프로듀서가 새 버전을 배포했지만 컨슈머가 업데이트되지 않음.

### Action Items
1. (즉시) 컨슈머 긴급 배포 또는 이벤트 다운컨버전 적용.
2. (재발방지) “producer first” 금지, 호환성 전략(dual publish) 적용.

---

## 16. RateLimit Exceeded (API Gateway)
---
service: api-gateway
error_message: 429 Too Many Requests
---
### Incident Summary
[WARN] 2024-05-01T10:15:00.000Z api-gateway/v1.9.0 [biz-016]: 429 Too Many Requests | Context: {Route="/v1/payments", ClientId="c-1122", RPS="900", Limit="300"}

### Root Cause
클라이언트 폭주/봇 트래픽으로 레이트리밋 트리거.

### Action Items
1. (즉시) 클라이언트별 quota 조정, 악성 IP/WAF 차단.
2. (완화) 429 응답에 Retry-After 제공, 클라 백오프 준수 유도.
3. (재발방지) 동적 레이트리밋 + 사용자/앱 등급별 정책.

---

## 17. RateLimit Store Contention (Redis)
---
service: rate-limit-service
error_message: rate limit store latency high
---
### Incident Summary
[ERROR] 2024-05-01T10:16:00.000Z rate-limit-service/v2.3.0 [biz-017]: rate limit store latency high | Context: {Store="redis", P99="120ms", Script="token_bucket.lua"}

### Root Cause
레이트리밋 체크가 Redis hot key/스크립트로 병목.

### Action Items
1. (즉시) 키 샤딩(버킷 분산), 스크립트 최적화.
2. (완화) 로컬 캐시/근사 레이트리밋(슬라이딩 윈도우) 적용.
3. (재발방지) 레이트리밋 인프라 분리/스케일 + 지표 알람.

---

## 18. Burst Traffic Not Handled (Thundering Herd)
---
service: order-service
error_message: burst traffic overload
---
### Incident Summary
[CRITICAL] 2024-05-01T10:17:00.000Z order-service/v4.2.1 [biz-018]: burst traffic overload | Context: {Campaign="flash-sale", QPS="50k", ThreadPool="exhausted"}

### Root Cause
버스트 트래픽 대비 미흡(큐/백프레셔/캐시 부족)으로 스레드/커넥션 고갈.

### Action Items
1. (즉시) 긴급 트래픽 감산(레이트리밋 강화) + 필수 경로만 유지(degrade).
2. (완화) 큐잉, 캐시 워밍, 오토스케일 임계값 조정.
3. (재발방지) 부하 테스트 + 백프레셔 설계 + 캠페인 런북.

---

## 19. Circuit Breaker Open
---
service: payment-api
error_message: circuit breaker open for downstream
---
### Incident Summary
[WARN] 2024-05-01T10:18:00.000Z payment-api/v5.5.0 [biz-019]: circuit breaker open | Context: {Downstream="ledger-service", FailRate="70%", Window="30s"}

### Root Cause
다운스트림 장애로 서킷브레이커가 열림(의도된 보호).

### Action Items
1. (즉시) 사용자에게 “처리 지연/대기” 안내, 재시도 유도(백오프 포함).
2. (완화) 대체 경로(큐/임시 저장)로 전환.
3. (재발방지) 다운스트림 복구 후 half-open 튜닝 + 장애 전파 테스트.

---

## 20. Retry Storm Amplification
---
service: api-gateway
error_message: retry storm detected
---
### Incident Summary
[CRITICAL] 2024-05-01T10:19:00.000Z api-gateway/v1.9.0 [biz-020]: retry storm detected | Context: {Clients="many", Retries="unbounded", 5xx="spike"}

### Root Cause
무제한/동시 재시도가 장애를 증폭(폭풍)시켜 전체 시스템을 다운시킴.

### Action Items
1. (즉시) 재시도 상한/백오프 강제, 특정 경로 429/503로 차단.
2. (완화) 서킷브레이커/벌크헤드 적용.
3. (재발방지) 전사 표준 재시도 정책 + Chaos/DR 테스트.

---

## 21. Event Ordering Violation
---
service: payment-consumer
error_message: event out-of-order
---
### Incident Summary
[ERROR] 2024-05-01T10:20:00.000Z payment-consumer/v3.4.0 [biz-021]: event out-of-order | Context: {Key="o-7712", Got="CAPTURED", ExpectedAfter="AUTHORIZED"}

### Root Cause
파티션 키 설계가 잘못되어 동일 주문 이벤트가 다른 파티션으로 분산되어 순서 보장이 깨짐.

### Action Items
1. (즉시) 파티션 키를 주문ID로 고정(동일 키는 동일 파티션).
2. (완화) 컨슈머에서 버퍼링/재정렬(한정 시간) 적용.
3. (재발방지) 이벤트 키 설계 가이드 + 통합 테스트.

---

## 22. Poison Message Detected
---
service: payment-consumer
error_message: poison message - repeated failure
---
### Incident Summary
[ERROR] 2024-05-01T10:21:00.000Z payment-consumer/v3.4.0 [biz-022]: poison message | Context: {EventId="evt-bad1", FailCount="25", Reason="null field"}

### Root Cause
특정 이벤트가 버그/데이터 결함으로 계속 실패 → 파티션 처리 정체.

### Action Items
1. (즉시) DLQ로 격리, 본 큐 진행을 복구.
2. (완화) 결함 이벤트는 스킵/보정 처리(정책 기반).
3. (재발방지) 스키마 검증 강화 + DLQ 런북/도구.

---

## 23. DLQ Backlog Growing
---
service: dlq-processor
error_message: DLQ backlog exceeds threshold
---
### Incident Summary
[WARN] 2024-05-01T10:22:00.000Z dlq-processor/v1.0.0 [biz-023]: DLQ backlog growing | Context: {Queue="payments-dlq", Backlog="380k", Oldest="6h"}

### Root Cause
DLQ 재처리 워커 처리량 부족 또는 원인 미해결 상태로 재처리가 계속 실패.

### Action Items
1. (즉시) 실패 원인 분류(스키마/의존성/데이터) 후 우선 해결.
2. (완화) 워커 스케일아웃 + 배치 처리.
3. (재발방지) DLQ SLO/알람 + 자동 라우팅(근본 원인별).

---

## 24. Event Consumer Rebalance Storm
---
service: broker-consumer
error_message: consumer group rebalance too frequent
---
### Incident Summary
[WARN] 2024-05-01T10:23:00.000Z broker-consumer/v3.4.0 [biz-024]: rebalance too frequent | Context: {Group="payments", Rebalances="12/10m", Reason="pod restarts"}

### Root Cause
빈번한 파드 재시작/스케일링으로 리밸런스가 잦아 처리량 저하.

### Action Items
1. (즉시) pod stability(리소스/헬스체크) 개선.
2. (완화) session.timeout/heartbeat 튜닝.
3. (재발방지) 롤링 배포/오토스케일 완화 + 안정성 SLO.

---

## 25. Exactly-Once Transaction Timeout (Kafka-like)
---
service: outbox-publisher
error_message: transactional.id timeout
---
### Incident Summary
[ERROR] 2024-05-01T10:24:00.000Z outbox-publisher/v1.6.0 [biz-025]: transactional.id timeout | Context: {Producer="tx-producer-1", Timeout="60s"}

### Root Cause
트랜잭션 프로듀서가 브로커와의 상태 동기화 실패/지연으로 타임아웃.

### Action Items
1. (즉시) 브로커 상태/네트워크 지연 확인.
2. (완화) 트랜잭션 타임아웃/배치 크기 조정.
3. (재발방지) 트랜잭션 사용 범위 최소화 + 모니터링.

---

## 26. Inconsistent Read (Stale Cache)
---
service: api-gateway
error_message: stale cache served beyond TTL
---
### Incident Summary
[WARN] 2024-05-01T10:25:00.000Z api-gateway/v1.9.0 [biz-026]: stale cache served | Context: {Key="order:o-7712", TTL="60s", Age="180s", Cause="origin timeout"}

### Root Cause
Origin 타임아웃 시 stale-while-revalidate 전략이 과도하게 적용되어 오래된 데이터를 제공.

### Action Items
1. (즉시) stale 허용 시간 상한 설정 및 민감 데이터(결제/정산)는 stale 금지.
2. (재발방지) 캐시 정책을 도메인별로 분리 + SLO 기반 조정.

---

## 27. Read-Your-Writes Violation
---
service: wallet-api
error_message: read-your-writes violation
---
### Incident Summary
[ERROR] 2024-05-01T10:26:00.000Z wallet-api/v5.0.0 [biz-027]: read-your-writes violation | Context: {UserId="u-9912", Write="debit", Read="balance", ReplicaLag="8s"}

### Root Cause
쓰기 직후 읽기가 리플리카로 라우팅되어 lag 때문에 최신 반영이 안 보임.

### Action Items
1. (즉시) 쓰기 직후 읽기는 primary 강제 또는 session affinity 적용.
2. (재발방지) lag 기반 라우팅 + 사용자 경로 일관성 정책.

---

## 28. Concurrent Update Conflict (Optimistic Lock)
---
service: points-service
error_message: optimistic lock conflict
---
### Incident Summary
[WARN] 2024-05-01T10:27:00.000Z points-service/v3.1.0 [biz-028]: optimistic lock conflict | Context: {UserId="u-3001", VersionExpected="19", VersionActual="20"}

### Root Cause
동일 리소스에 동시 업데이트가 발생하여 버전 조건이 실패(정상).

### Action Items
1. (즉시) 재시도(backoff) 또는 사용자 단위 직렬화 큐 적용.
2. (재발방지) 충돌률 모니터링, 핫키 분산/샤딩.

---

## 29. Business Rule Violation – Daily Limit Exceeded
---
service: risk-service
error_message: daily transaction limit exceeded
---
### Incident Summary
[INFO] 2024-05-01T10:28:00.000Z risk-service/v2.7.0 [biz-029]: daily transaction limit exceeded | Context: {UserId="u-9912", Limit="500000", Attempt="120000", Used="490000"}

### Root Cause
일일 한도 정책에 의해 정상 차단. 그러나 상위 서비스가 500으로 처리하면 UX/재시도 폭주 가능.

### Action Items
1. (즉시) 4xx(정책 위반)로 명확히 응답, 재시도 금지 안내.
2. (재발방지) 한도/정책 에러 코드 표준화 + 프론트 메시지 일관화.

---

## 30. Business Rule Violation – KYC Required
---
service: risk-service
error_message: kyc_required_for_amount
---
### Incident Summary
[INFO] 2024-05-01T10:29:00.000Z risk-service/v2.7.0 [biz-030]: kyc_required_for_amount | Context: {UserId="u-5511", Amount="2000000", KYC="NONE"}

### Root Cause
고액 거래 정책상 KYC 미완료 사용자는 차단(정상).

### Action Items
1. (즉시) 사용자에게 KYC 절차 안내, 차단 사유를 명확히 표시.
2. (재발방지) 정책 변경 시 알림/가이드 업데이트.

---

## 31. Idempotency Key Collision Across Endpoints
---
service: payment-api
error_message: idempotency key collision
---
### Incident Summary
[ERROR] 2024-05-01T10:30:00.000Z payment-api/v5.5.0 [biz-031]: idempotency key collision | Context: {Key="idem-123", EndpointA="/capture", EndpointB="/refund"}

### Root Cause
멱등키 스코프가 엔드포인트/오퍼레이션을 포함하지 않아 서로 다른 작업이 충돌.

### Action Items
1. (즉시) 멱등키 저장 키를 (operation + orderId + key)로 확장.
2. (재발방지) 멱등 스펙 문서화 + SDK 강제.

---

## 32. Partial Failure – Payment Success but Notification Failed
---
service: notification-service
error_message: failed to send receipt notification
---
### Incident Summary
[WARN] 2024-05-01T10:31:00.000Z notification-service/v1.8.0 [biz-032]: failed to send receipt | Context: {OrderId="o-7712", Channel="kakao", Error="429"}

### Root Cause
부가 기능(영수증 알림)이 실패했지만 결제 자체는 성공(부분 실패).

### Action Items
1. (즉시) 알림은 비동기/재시도 큐로 분리(DLQ 포함).
2. (재발방지) 핵심/비핵심 경로 분리(벌크헤드) + 서킷브레이커.

---

## 33. Partial Failure – Order Confirmed but Ledger Append Delayed
---
service: reconciliation-job
error_message: ledger append delayed
---
### Incident Summary
[WARN] 2024-05-01T10:32:00.000Z reconciliation-job/v1.2.0 [biz-033]: ledger append delayed | Context: {OrderId="o-8801", Ledger="missing", Age="30m"}

### Root Cause
원장 이벤트 지연/유실로 정산/감사 경로에 영향.

### Action Items
1. (즉시) outbox 재발행 또는 재처리 워커로 보완.
2. (재발방지) 원장 이벤트는 강한 내구성 경로로(트랜잭션 outbox) 고정.

---

## 34. SAGA – Step Retried Beyond Max Attempts
---
service: saga-orchestrator
error_message: saga step retries exceeded
---
### Incident Summary
[ERROR] 2024-05-01T10:33:00.000Z saga-orchestrator/v3.0.0 [biz-034]: retries exceeded | Context: {Saga="refund_flow", Step="release_points", Attempts="10", Max="10"}

### Root Cause
다운스트림 장애가 장기화되었는데 재시도만 반복되어 복구 불가.

### Action Items
1. (즉시) 재시도 중단 후 DLQ/수동 처리로 전환.
2. (재발방지) 재시도 정책(상한/쿨다운) + 장애시 degrade 설계.

---

## 35. Event Handler Timeout
---
service: points-consumer
error_message: handler timeout exceeded
---
### Incident Summary
[ERROR] 2024-05-01T10:34:00.000Z points-consumer/v2.2.0 [biz-035]: handler timeout exceeded | Context: {EventId="evt-7711", Timeout="3s", Work="heavy"}

### Root Cause
이벤트 핸들러가 과도한 I/O/외부 호출로 타임아웃.

### Action Items
1. (즉시) 핸들러를 경량화(외부 호출은 비동기).
2. (완화) 배치 처리/병렬성 조정, 타임아웃 현실화.
3. (재발방지) 핸들러 성능 예산(SLO) + 프로파일링.

---

## 36. Fanout Storm From Single Event
---
service: event-gateway
error_message: fanout storm detected
---
### Incident Summary
[WARN] 2024-05-01T10:35:00.000Z event-gateway/v2.0.0 [biz-036]: fanout storm | Context: {Event="PromotionStarted", Subscribers="80", Downstreams="timeouts"}

### Root Cause
단일 이벤트가 많은 다운스트림 호출을 유발해 연쇄 타임아웃/장애 전파.

### Action Items
1. (즉시) 브로드캐스트 이벤트는 큐 기반 비동기 처리로 전환.
2. (완화) 구독자별 벌크헤드/서킷브레이커 적용.
3. (재발방지) 이벤트 설계(세분화/샤딩) + 부하 테스트.

---

## 37. RateLimit Misconfiguration (Too Strict)
---
service: api-gateway
error_message: rate limit configured too low
---
### Incident Summary
[WARN] 2024-05-01T10:36:00.000Z api-gateway/v1.9.0 [biz-037]: rate limit too strict | Context: {Route="/v1/orders", Limit="10rps", Normal="100rps"}

### Root Cause
설정 실수로 정상 트래픽이 차단되어 장애처럼 보임.

### Action Items
1. (즉시) 최근 설정 변경 이력 확인 및 롤백.
2. (재발방지) 설정 변경 승인/검증(카나리) + safe defaults.

---

## 38. RateLimit Misconfiguration (Too Loose)
---
service: api-gateway
error_message: rate limit disabled
---
### Incident Summary
[WARN] 2024-05-01T10:37:00.000Z api-gateway/v1.9.0 [biz-038]: rate limit disabled | Context: {Route="/v1/payments", Allowed="unbounded", Attack="suspected"}

### Root Cause
레이트리밋 비활성으로 공격/폭주가 직접 다운스트림을 타격.

### Action Items
1. (즉시) 기본 레이트리밋 정책 복구, 공격 IP/WAF 차단.
2. (재발방지) 설정 드리프트 감시 + “최소 레이트리밋” 강제.

---

## 39. Quota Exceeded (Partner)
---
service: partner-api
error_message: partner quota exceeded
---
### Incident Summary
[WARN] 2024-05-01T10:38:00.000Z partner-api/v1.0.0 [biz-039]: partner quota exceeded | Context: {Partner="affiliate-22", DailyQuota="1M", Used="1M"}

### Root Cause
파트너 쿼터 초과로 요청 차단(정상). 상위 서비스 재시도 시 폭풍.

### Action Items
1. (즉시) 429 + Retry-After 제공, 재시도 금지 안내.
2. (재발방지) 파트너 등급/쿼터 모니터링 + 사전 알림.

---

## 40. SAGA – Duplicate Step Execution (Non-idempotent)
---
service: saga-orchestrator
error_message: step executed twice
---
### Incident Summary
[CRITICAL] 2024-05-01T10:39:00.000Z saga-orchestrator/v3.0.0 [biz-040]: step executed twice | Context: {Saga="refund_flow", Step="refund_payment", Effect="double refund risk"}

### Root Cause
사가 스텝이 멱등하지 않은데 재시도/중복 이벤트로 2회 실행됨.

### Action Items
1. (즉시) 스텝 실행 키(SagaId+Step)로 유니크 보장 및 상태 저장.
2. (완화) 외부 작업(환불)은 PG 멱등키/상태조회 기반으로 수행.
3. (재발방지) 사가 스텝 멱등성 체크리스트/테스트.

---

# 41–100 (추가 케이스: 정합성/이벤트/레이트리밋/사가 심화)

## 41. Event Publish Failed (Broker Unavailable)
---
service: event-publisher
error_message: failed to publish event to broker
---
### Incident Summary
[ERROR] 2024-05-01T10:40:00.000Z event-publisher/v2.0.0 [biz-041]: failed to publish event | Context: {Topic="orders", Error="broker unavailable", Retries="5"}

### Root Cause
브로커 장애/네트워크 이슈로 이벤트 발행 실패.

### Action Items
1. (즉시) outbox에 적재되어 있는지 확인(없으면 데이터 유실 위험).
2. (완화) publish 재시도는 outbox 기반으로 전환.
3. (재발방지) 브로커 HA + 퍼블리셔 서킷브레이커 + outbox 강제.

---

## 42. Event Published But Consumer Down (Backlog Growth)
---
service: broker
error_message: consumer lag exceeds threshold
---
### Incident Summary
[WARN] 2024-05-01T10:41:00.000Z broker/cluster [biz-042]: consumer lag exceeds threshold | Context: {Group="ledger", Lag="2.1M", Oldest="4h"}

### Root Cause
컨슈머 장애/처리량 부족으로 lag 증가 → 정합성 지연.

### Action Items
1. (즉시) 컨슈머 복구/스케일아웃, 병목 제거.
2. (완화) 처리 우선순위(핵심 이벤트 먼저) 적용.
3. (재발방지) lag SLO/알람 + autoscaling 정책.

---

## 43. Event Handler Side-Effect Not Atomic (No Outbox)
---
service: order-service
error_message: side-effect not atomic with state update
---
### Incident Summary
[ERROR] 2024-05-01T10:42:00.000Z order-service/v4.2.1 [biz-043]: state updated but event missing | Context: {OrderId="o-7001", DBCommit="ok", Event="not sent"}

### Root Cause
DB 상태 변경과 이벤트 발행이 트랜잭션으로 묶이지 않아 이벤트 누락.

### Action Items
1. (즉시) outbox 패턴 도입(상태 변경과 outbox insert를 동일 tx).
2. (재발방지) “event-driven consistency” 체크리스트에 포함.

---

## 44. Duplicate Message Due To Producer Retry Without Idempotence
---
service: event-publisher
error_message: duplicate message produced
---
### Incident Summary
[WARN] 2024-05-01T10:43:00.000Z event-publisher/v2.0.0 [biz-044]: duplicate message produced | Context: {Reason="producer retry", EventId="evt-88dd", Count="3"}

### Root Cause
프로듀서가 발행 실패를 재시도하면서 동일 메시지를 여러 번 전송.

### Action Items
1. (즉시) EventId 기반 dedup을 컨슈머에서 보장.
2. (재발방지) 프로듀서 idempotent publish(가능 시) + outbox.

---

## 45. Inconsistent State – Refund Completed But Points Not Reverted
---
service: reconciliation-job
error_message: refund-points inconsistency
---
### Incident Summary
[ERROR] 2024-05-01T10:44:00.000Z reconciliation-job/v1.2.0 [biz-045]: refund completed but points not reverted | Context: {OrderId="o-8123", Refund="DONE", Points="NOT_REVERTED", Age="1h"}

### Root Cause
사가 보상(revert_points) 실패 또는 이벤트 유실.

### Action Items
1. (즉시) revert_points 재처리(멱등) 실행.
2. (재발방지) 사가 보상 실패 DLQ + 정합성 배치 강화.

---

## 46. Payment Captured Twice (Idempotency Broken Upstream)
---
service: payment-api
error_message: duplicate capture detected
---
### Incident Summary
[CRITICAL] 2024-05-01T10:45:00.000Z payment-api/v5.5.0 [biz-046]: duplicate capture detected | Context: {OrderId="o-9009", PG="XPay", CaptureCount="2", IdemKey="missing"}

### Root Cause
캡처 요청이 멱등키 없이 수행되거나 스코프가 잘못되어 중복 캡처 발생.

### Action Items
1. (즉시) PG 조회로 실제 중복 캡처 여부 확인 후 즉시 취소/환불 조치.
2. (완화) 캡처는 반드시 멱등키+상태조회 기반으로만 수행.
3. (재발방지) 멱등키 필수화 + 계약 테스트.

---

## 47. Eventual Consistency Window Exceeded
---
service: reconciliation-job
error_message: consistency window exceeded
---
### Incident Summary
[WARN] 2024-05-01T10:46:00.000Z reconciliation-job/v1.2.0 [biz-047]: consistency window exceeded | Context: {Entity="order", ExpectedWithin="2m", Actual="15m", Cause="lag"}

### Root Cause
이벤트 기반 정합성 수렴 시간이 SLA를 초과(컨슈머 lag/브로커 지연).

### Action Items
1. (즉시) lag 원인 제거/스케일아웃.
2. (완화) 사용자 UI에 “처리중” 상태 유지, 확정 전 노출 최소화.
3. (재발방지) 정합성 SLO 정의 + 자동 리커버리(runbook).

---

## 48. Event Processing Skipped Due To Version Filter
---
service: order-consumer
error_message: event skipped - version too old
---
### Incident Summary
[WARN] 2024-05-01T10:47:00.000Z order-consumer/v1.9.1 [biz-048]: event skipped | Context: {EventId="evt-1991", Version="1", MinSupported="2"}

### Root Cause
컨슈머가 구버전 이벤트를 무시하여 상태 갱신 누락.

### Action Items
1. (즉시) 다운컨버전 또는 다중 버전 지원 추가.
2. (재발방지) 버전 정책(지원 기간) 합의 + 마이그레이션 계획.

---

## 49. SAGA Orchestrator Restart Without Persisted State
---
service: saga-orchestrator
error_message: saga state not found after restart
---
### Incident Summary
[ERROR] 2024-05-01T10:48:00.000Z saga-orchestrator/v3.0.0 [biz-049]: saga state not found | Context: {SagaId="s-7712", Storage="in-memory", Restart="true"}

### Root Cause
사가 상태를 메모리에만 두어 재시작 시 진행 상태 유실.

### Action Items
1. (즉시) 사가 상태 저장소(DB/Redis)로 영속화.
2. (재발방지) 오케스트레이터 stateless 원칙 + 복구 가능 설계.

---

## 50. Compensation Executed After Success (Late Failure)
---
service: saga-orchestrator
error_message: compensation executed after saga success
---
### Incident Summary
[CRITICAL] 2024-05-01T10:49:00.000Z saga-orchestrator/v3.0.0 [biz-050]: compensation after success | Context: {Saga="order_checkout", OrderId="o-7712", LateEvent="inventory_failed"}

### Root Cause
늦게 도착한 실패 이벤트를 잘못 처리해 이미 성공한 사가에 보상을 실행(상태 머신 결함).

### Action Items
1. (즉시) 상태 머신에 terminal 상태 보호(성공 후 보상 금지) 추가.
2. (완화) late event는 별도 재조정 흐름으로 보내기.
3. (재발방지) 이벤트 순서/지연 시뮬레이션 테스트.

---

## 51. RateLimit Bypass Detected (Header Spoof)
---
service: api-gateway
error_message: rate limit bypass suspected
---
### Incident Summary
[WARN] 2024-05-01T10:50:00.000Z api-gateway/v1.9.0 [biz-051]: bypass suspected | Context: {Key="X-Client-Id", Value="randomized", Requests="high"}

### Root Cause
레이트리밋 키를 클라이언트 헤더에만 의존하여 조작 가능.

### Action Items
1. (즉시) 키를 인증된 주체(user_id/api_key) 기반으로 변경.
2. (재발방지) 서명된 클라이언트 식별자 + WAF 룰.

---

## 52. Token Bucket Drift (Clock Skew)
---
service: rate-limit-service
error_message: token bucket drift due to clock skew
---
### Incident Summary
[ERROR] 2024-05-01T10:51:00.000Z rate-limit-service/v2.3.0 [biz-052]: token bucket drift | Context: {NodeTimeSkew="4s", Effect="over/under limit"}

### Root Cause
노드 시간 차이로 레이트리밋 계산이 일관되지 않음.

### Action Items
1. (즉시) NTP/시간 동기화 확인.
2. (재발방지) 중앙 스토어 기반 계산 또는 skew 허용 설계.

---

## 53. Bulkhead Limit Reached (Thread Pool)
---
service: payment-api
error_message: bulkhead rejected execution
---
### Incident Summary
[WARN] 2024-05-01T10:52:00.000Z payment-api/v5.5.0 [biz-053]: bulkhead rejected execution | Context: {Pool="pg-calls", Active="200", Queue="1000"}

### Root Cause
다운스트림 지연으로 bulkhead 풀이 가득 차 요청이 거절됨(의도된 보호).

### Action Items
1. (즉시) 다운스트림 장애/지연 원인 해결.
2. (완화) 사용자에게 재시도 안내(백오프), 큐잉/비동기 전환.
3. (재발방지) bulkhead sizing + SLO 기반 튜닝.

---

## 54. Consistency Check Failed (Ledger Sum Mismatch)
---
service: audit-service
error_message: ledger sum mismatch
---
### Incident Summary
[CRITICAL] 2024-05-01T10:53:00.000Z audit-service/v1.0.0 [biz-054]: ledger sum mismatch | Context: {UserId="u-9912", Expected="0", Actual="-12000", Window="24h"}

### Root Cause
중복/유실 이벤트 또는 보상 누락으로 원장 합계가 맞지 않음.

### Action Items
1. (즉시) 원장 엔트리를 EventId 기준으로 재검증, 중복 제거/누락 재적재.
2. (완화) 영향 사용자/거래 격리 및 임시 제한.
3. (재발방지) 정합성 검증 배치 + 재처리 파이프라인.

---

## 55. Event Replay Triggered (Manual)
---
service: replay-service
error_message: replay executed
---
### Incident Summary
[INFO] 2024-05-01T10:54:00.000Z replay-service/v1.0.0 [biz-055]: replay executed | Context: {Topic="payments", Range="10:00-10:10", Reason="incident"}

### Root Cause
장애 대응으로 이벤트 리플레이를 수행(정상). 단, 컨슈머 멱등성 없으면 사고.

### Action Items
1. (즉시) 리플레이 전 멱등성/중복 처리 준비 확인.
2. (재발방지) 리플레이 런북/체크리스트 + 리플레이 전용 환경.

---

## 56. Replay Caused Side-Effects (Non-idempotent)
---
service: ledger-service
error_message: replay caused duplicate side-effects
---
### Incident Summary
[CRITICAL] 2024-05-01T10:55:00.000Z ledger-service/v6.0.1 [biz-056]: replay caused duplicates | Context: {EventId="evt-5001", Duplicate="true"}

### Root Cause
리플레이는 필연적으로 중복을 만들 수 있는데 핸들러가 멱등하지 않음.

### Action Items
1. (즉시) unique constraint/EventId dedup 적용, 보정 실행.
2. (재발방지) 리플레이 가능성을 전제한 핸들러 표준화.

---

## 57. Event Contract Break – Field Removed
---
service: points-consumer
error_message: missing required field
---
### Incident Summary
[ERROR] 2024-05-01T10:56:00.000Z points-consumer/v2.2.0 [biz-057]: missing required field | Context: {Field="reason", Event="PointsGranted", ProducerVersion="5"}

### Root Cause
프로듀서가 필수 필드를 제거하여 하위 호환성을 깨뜨림.

### Action Items
1. (즉시) producer 롤백 또는 default 처리로 hotfix.
2. (재발방지) 스키마 호환성 규칙(필드 제거 금지) + CI 게이트.

---

## 58. Event Contract Break – Type Changed
---
service: order-consumer
error_message: invalid type for field
---
### Incident Summary
[ERROR] 2024-05-01T10:57:00.000Z order-consumer/v1.9.1 [biz-058]: invalid type | Context: {Field="amount", Expected="int64", Got="float"}

### Root Cause
타입 변경은 하위 호환을 깨며 런타임 파싱 실패를 유발.

### Action Items
1. (즉시) 다운컨버전 또는 dual field(amount_int, amount_float)로 단계적 이전.
2. (재발방지) 스키마 규칙/리뷰 프로세스.

---

## 59. Poison Event Blocks Partition
---
service: broker-consumer
error_message: partition blocked by poison event
---
### Incident Summary
[ERROR] 2024-05-01T10:58:00.000Z broker-consumer/v3.4.0 [biz-059]: partition blocked | Context: {Partition="12", EventId="evt-bad1", Retries="infinite"}

### Root Cause
특정 이벤트가 계속 실패하여 해당 파티션 진행이 멈춤.

### Action Items
1. (즉시) DLQ로 격리(스킵) 후 파티션 진행 재개.
2. (재발방지) 스킵/격리 정책 + 자동 DLQ 라우팅.

---

## 60. Ordering Key Mispartitioned
---
service: event-publisher
error_message: wrong partition key used
---
### Incident Summary
[WARN] 2024-05-01T10:59:00.000Z event-publisher/v2.0.0 [biz-060]: wrong partition key | Context: {ExpectedKey="order_id", Used="user_id", Impact="order events out-of-order"}

### Root Cause
파티션 키가 잘못되어 순서 보장이 필요한 단위가 깨짐.

### Action Items
1. (즉시) 파티션 키 수정 후 재배포, 영향 구간 리플레이로 복구.
2. (재발방지) 이벤트 키 설계 가이드 + e2e 테스트.

---

## 61. RateLimit Key Explosion (Cardinality)
---
service: rate-limit-service
error_message: rate limit key cardinality high
---
### Incident Summary
[WARN] 2024-05-01T11:00:00.000Z rate-limit-service/v2.3.0 [biz-061]: cardinality high | Context: {Keys="20M", TTL="30m", StoreMem="growing"}

### Root Cause
레이트리밋 키가 지나치게 세분화(IP+UA+path 등)되어 키 수 폭증.

### Action Items
1. (즉시) 키 구성을 단순화(user_id 중심), TTL 조정.
2. (재발방지) 키 카디널리티 가이드 + 메모리 알람.

---

## 62. Quota Window Misaligned
---
service: quota-service
error_message: quota window misaligned
---
### Incident Summary
[ERROR] 2024-05-01T11:01:00.000Z quota-service/v1.4.0 [biz-062]: window misaligned | Context: {User="u-1", Window="daily", TZ="KST", Reset="UTC"}

### Root Cause
일일 쿼터 리셋 기준(UTC vs KST)이 혼재하여 사용자 불만/정책 오류.

### Action Items
1. (즉시) 정책 기준 시간을 명확히 통일(KST 등)하고 표시.
2. (재발방지) 정책 문서/테스트에 타임존 포함.

---

## 63. Distributed Lock Contention
---
service: wallet-service
error_message: distributed lock contention
---
### Incident Summary
[WARN] 2024-05-01T11:02:00.000Z wallet-service/v5.0.0 [biz-063]: lock contention | Context: {Lock="wallet:u-9912", Wait="800ms", QPS="high"}

### Root Cause
사용자 단위 분산 락이 병목(핫 유저/동시 요청).

### Action Items
1. (즉시) 큐 기반 직렬화로 전환하거나 락 범위 축소.
2. (재발방지) 핫키/핫유저 대응(샤딩/리밋) + 지표.

---

## 64. Distributed Lock Lost (TTL Too Short)
---
service: wallet-service
error_message: distributed lock lost before completion
---
### Incident Summary
[ERROR] 2024-05-01T11:03:00.000Z wallet-service/v5.0.0 [biz-064]: lock lost | Context: {Lock="wallet:u-9912", TTL="500ms", Work="900ms"}

### Root Cause
락 TTL이 작업 시간보다 짧아 락이 중간에 풀리고 중복 실행 가능.

### Action Items
1. (즉시) TTL을 늘리거나 watchdog/renew 적용.
2. (재발방지) 락 TTL은 P99 작업 시간을 반영하도록 표준화.

---

## 65. Dedup TTL Too Short (Duplicate After Expiry)
---
service: payment-consumer
error_message: duplicate processed after dedup expiry
---
### Incident Summary
[WARN] 2024-05-01T11:04:00.000Z payment-consumer/v3.4.0 [biz-065]: duplicate after expiry | Context: {EventId="evt-abc1", DedupTTL="5m", Replay="10m later"}

### Root Cause
Dedup TTL이 리플레이/지연보다 짧아 중복 처리가 발생.

### Action Items
1. (즉시) dedup TTL을 “최대 지연 + 안전 버퍼” 이상으로 상향.
2. (재발방지) 지연/리플레이 정책과 TTL 연동.

---

## 66. SAGA – Inventory Release Idempotency Missing
---
service: inventory-service
error_message: release executed multiple times
---
### Incident Summary
[ERROR] 2024-05-01T11:05:00.000Z inventory-service/v3.8.0 [biz-066]: release executed multiple times | Context: {OrderId="o-7712", Released="2", Expected="1"}

### Root Cause
release 보상 로직이 멱등하지 않아 중복 호출 시 재고가 과다 복구됨.

### Action Items
1. (즉시) 보상 작업에 idempotency key(OrderId+Step) 적용.
2. (재발방지) 재고/보상 로직 멱등성 테스트 추가.

---

## 67. SAGA – Payment Cancel Called After Capture
---
service: payment-api
error_message: cancel requested after capture
---
### Incident Summary
[WARN] 2024-05-01T11:06:00.000Z payment-api/v5.5.0 [biz-067]: cancel requested after capture | Context: {OrderId="o-7712", Payment="CAPTURED", Policy="refund required"}

### Root Cause
사가 보상 단계가 잘못되어 capture 이후 cancel을 호출(정책상 refund가 맞음).

### Action Items
1. (즉시) 상태 기반 라우팅: AUTH → CANCEL, CAPTURED → REFUND.
2. (재발방지) 상태 머신/사가 정의서 업데이트 + 테스트.

---

## 68. Duplicate Refund Request (User Retry)
---
service: refund-service
error_message: duplicate refund request
---
### Incident Summary
[INFO] 2024-05-01T11:07:00.000Z refund-service/v2.5.0 [biz-068]: duplicate refund request | Context: {OrderId="o-6601", IdemKey="idem-r-91", Seen="true"}

### Root Cause
사용자 재시도/지연으로 환불 요청 중복(정상 멱등 필요).

### Action Items
1. (즉시) 환불은 멱등키+PG 조회 기반으로 동일 응답 반환.
2. (재발방지) 환불 상태 머신(REQUESTED/PROCESSING/DONE) 강화.

---

## 69. Refund Completed But Shipment Not Cancelled
---
service: reconciliation-job
error_message: refund-shipment inconsistency
---
### Incident Summary
[ERROR] 2024-05-01T11:08:00.000Z reconciliation-job/v1.2.0 [biz-069]: refund done but shipment active | Context: {OrderId="o-7009", Refund="DONE", Shipment="SHIPPED"}

### Root Cause
환불과 배송 취소 간 이벤트/사가 연동이 깨짐(정책 위반).

### Action Items
1. (즉시) 정책 기반 조치(반품 프로세스 전환) 또는 배송사 연동 취소 시도.
2. (재발방지) 사가 정의(배송 단계 분기) + 정합성 검증.

---

## 70. Settlement Delayed Due To Event Lag
---
service: settlement-service
error_message: settlement delayed
---
### Incident Summary
[WARN] 2024-05-01T11:09:00.000Z settlement-service/v2.9.0 [biz-070]: settlement delayed | Context: {MerchantId="m-22", Expected="T+1", Lag="8h", Cause="ledger consumer lag"}

### Root Cause
원장 이벤트 처리 지연으로 정산 데이터가 늦게 수렴.

### Action Items
1. (즉시) lag 해소(컨슈머 스케일/병목 제거).
2. (재발방지) 정산은 수렴 지연을 고려한 버퍼/컷오프 설계.

---

## 71. Settlement Duplicate Payout
---
service: settlement-service
error_message: duplicate payout detected
---
### Incident Summary
[CRITICAL] 2024-05-01T11:10:00.000Z settlement-service/v2.9.0 [biz-071]: duplicate payout detected | Context: {PayoutId="p-7712", Count="2", Cause="retry without idempotency"}

### Root Cause
정산 지급이 멱등하지 않아 재시도 시 중복 지급 위험.

### Action Items
1. (즉시) PayoutId 유니크 보장 + 지급 API 멱등키 적용.
2. (재발방지) 지급 상태 머신 + 재시도 정책 표준화.

---

## 72. Partner Webhook Flood (RateLimit Needed)
---
service: partner-webhook
error_message: partner webhook flood detected
---
### Incident Summary
[WARN] 2024-05-01T11:11:00.000Z partner-webhook/v1.0.0 [biz-072]: webhook flood | Context: {Partner="affiliate-22", RPS="2000", Normal="50"}

### Root Cause
파트너가 잘못된 재시도/버그로 웹훅을 폭주 전송.

### Action Items
1. (즉시) 파트너별 레이트리밋/차단 적용, 429 + Retry-After 제공.
2. (재발방지) 파트너 가이드/계약에 재시도 규칙 명시.

---

## 73. Event Dedup Store Memory Leak
---
service: idempotency-store
error_message: dedup store memory usage growing
---
### Incident Summary
[WARN] 2024-05-01T11:12:00.000Z idempotency-store/v1.0.0 [biz-073]: memory usage growing | Context: {Keys="50M", TTL="none", Evictions="0"}

### Root Cause
dedup 키에 TTL이 없거나 너무 길어 메모리 누수처럼 증가.

### Action Items
1. (즉시) TTL 강제, 키 샘플링 정리.
2. (재발방지) dedup TTL 정책 표준화 + 메모리 알람.

---

## 74. Reconciliation Job Overrun
---
service: reconciliation-job
error_message: reconciliation runtime exceeds window
---
### Incident Summary
[WARN] 2024-05-01T11:13:00.000Z reconciliation-job/v1.2.0 [biz-074]: runtime exceeds window | Context: {Window="15m", Actual="45m", Data="3x"}

### Root Cause
데이터 증가/쿼리 비효율로 정합성 배치가 시간 초과.

### Action Items
1. (즉시) 배치 파티셔닝/증분 처리(변경분만) 적용.
2. (재발방지) 배치 SLO/리소스 계획 + 성능 테스트.

---

## 75. Event Fanout Causes DB Hotspot
---
service: loyalty-service
error_message: db hotspot due to fanout
---
### Incident Summary
[ERROR] 2024-05-01T11:14:00.000Z loyalty-service/v3.0.0 [biz-075]: db hotspot | Context: {Event="OrderPaid", Writes="200k/min", Table="user_points"}

### Root Cause
팬아웃 이벤트로 특정 테이블/키에 쓰기 집중 → DB 핫스팟.

### Action Items
1. (즉시) 배치/버퍼링(큐)로 쓰기 평탄화.
2. (재발방지) 샤딩/파티셔닝 + 핫키 감지.

---

## 76. Idempotent Handler Returned 500 (Wrong Semantics)
---
service: payment-consumer
error_message: idempotent duplicate treated as error
---
### Incident Summary
[WARN] 2024-05-01T11:15:00.000Z payment-consumer/v3.4.0 [biz-076]: duplicate treated as error | Context: {EventId="evt-11aa", Action="upsert", Response="500"}

### Root Cause
중복 이벤트를 정상(no-op) 처리해야 하는데 예외로 처리해 재시도 폭풍 유발.

### Action Items
1. (즉시) 중복은 성공(200)으로 처리하도록 수정.
2. (재발방지) 멱등 핸들러 에러 분류 가이드(정책 위반 vs 시스템 오류).

---

## 77. Anti-Fraud Model Service RateLimited
---
service: risk-service
error_message: upstream model rate limit
---
### Incident Summary
[ERROR] 2024-05-01T11:16:00.000Z risk-service/v2.7.0 [biz-077]: upstream model rate limit | Context: {Upstream="fraud-ml", 429="true", QPS="high"}

### Root Cause
리스크 평가 호출이 모델 서비스 한도를 초과.

### Action Items
1. (즉시) 큐잉/비동기 평가로 전환, 중요도 기반 샘플링.
2. (재발방지) 모델 서비스 쿼터/스케일 계획 + 캐시.

---

## 78. Fraud Check Skipped Due To Timeout (Policy Risk)
---
service: risk-service
error_message: fraud check timed out and was skipped
---
### Incident Summary
[CRITICAL] 2024-05-01T11:17:00.000Z risk-service/v2.7.0 [biz-078]: fraud check skipped | Context: {OrderId="o-9012", Timeout="150ms", Default="allow"}

### Root Cause
타임아웃 시 기본 허용(allow) 정책으로 리스크 증가.

### Action Items
1. (즉시) 타임아웃 시 정책을 “review/hold”로 변경(리스크 수준에 따라).
2. (재발방지) 리스크 정책 런북 + 모델 SLO.

---

## 79. Event Processing Parallelism Too High (Duplicate Side-Effects)
---
service: ledger-service
error_message: parallel processing caused race
---
### Incident Summary
[ERROR] 2024-05-01T11:18:00.000Z ledger-service/v6.0.1 [biz-079]: race detected | Context: {Key="u-9912", Workers="64", Conflict="true"}

### Root Cause
동일 키(사용자/주문)를 병렬 처리하여 경쟁 조건 발생.

### Action Items
1. (즉시) key-based partitioning/serial processing 적용.
2. (재발방지) 병렬성은 키 단위로 제한하도록 설계.

---

## 80. SAGA – Step Dependency Missing (Wrong Order)
---
service: saga-orchestrator
error_message: step dependency missing
---
### Incident Summary
[ERROR] 2024-05-01T11:19:00.000Z saga-orchestrator/v3.0.0 [biz-080]: dependency missing | Context: {Step="capture_payment", DependsOn="authorize_payment", Missing="true"}

### Root Cause
사가 정의/코드가 바뀌면서 스텝 의존성 검증이 누락.

### Action Items
1. (즉시) 사가 정의서/코드 동기화, 스텝 선행조건 체크 추가.
2. (재발방지) 사가 DSL/검증기 도입 + 테스트.

---

## 81. RateLimit Not Applied To Internal Calls (East-West)
---
service: internal-gateway
error_message: internal rate limit missing
---
### Incident Summary
[WARN] 2024-05-01T11:20:00.000Z internal-gateway/v1.0.0 [biz-081]: internal rate limit missing | Context: {Caller="batch", Callee="payment-api", QPS="30k"}

### Root Cause
동서 트래픽(서비스 간 호출)에 레이트리밋이 없어 배치가 온라인 경로를 압도.

### Action Items
1. (즉시) internal caller별 quota 적용.
2. (재발방지) 배치/온라인 트래픽 분리 + priority queue.

---

## 82. Priority Inversion (Batch Starves Online)
---
service: scheduler
error_message: priority inversion detected
---
### Incident Summary
[ERROR] 2024-05-01T11:21:00.000Z scheduler/v1.0.0 [biz-082]: priority inversion | Context: {Batch="settlement", Online="payment", Resources="cpu"}

### Root Cause
배치가 리소스를 점유해 온라인 결제가 지연.

### Action Items
1. (즉시) 리소스 분리(노드풀/큐) + 우선순위 정책 적용.
2. (재발방지) SLO 기반 리소스 가드레일.

---

## 83. Event Store Retention Too Short
---
service: broker
error_message: retention too short caused replay failure
---
### Incident Summary
[ERROR] 2024-05-01T11:22:00.000Z broker/cluster [biz-083]: replay failed due to retention | Context: {Topic="ledger-events", Retention="6h", Needed="24h"}

### Root Cause
보존 기간이 짧아 장애 복구 리플레이가 불가능.

### Action Items
1. (즉시) retention 상향(비용/정책 고려).
2. (재발방지) RTO/RPO 요구사항과 retention을 연동.

---

## 84. Audit Trail Missing (Compliance Risk)
---
service: audit-service
error_message: audit trail missing for transaction
---
### Incident Summary
[CRITICAL] 2024-05-01T11:23:00.000Z audit-service/v1.0.0 [biz-084]: audit trail missing | Context: {TxId="tx-77aa", Required="true", Found="false"}

### Root Cause
이벤트/원장 기록이 누락되어 감사 추적 불가(컴플라이언스 위험).

### Action Items
1. (즉시) 원천 데이터(PG/DB)에서 재구성하여 감사 로그 보정.
2. (재발방지) 감사 이벤트는 별도 내구성 경로(append-only)로 분리.

---

## 85. SAGA – Orchestrator Duplicate Saga Start
---
service: saga-orchestrator
error_message: duplicate saga start
---
### Incident Summary
[WARN] 2024-05-01T11:24:00.000Z saga-orchestrator/v3.0.0 [biz-085]: duplicate saga start | Context: {OrderId="o-7712", SagaId="s-1", Count="2"}

### Root Cause
사가 시작 요청이 중복 수신되었는데 시작 멱등성이 없음.

### Action Items
1. (즉시) OrderId 기반으로 saga start를 유니크 보장.
2. (재발방지) 시작/종료 이벤트 모두 멱등 처리.

---

## 86. Inbound Event Auth Failed (Service-to-Service)
---
service: event-gateway
error_message: invalid service token
---
### Incident Summary
[ERROR] 2024-05-01T11:25:00.000Z event-gateway/v2.0.0 [biz-086]: invalid service token | Context: {Producer="order-service", Token="expired", Topic="orders"}

### Root Cause
서비스 토큰 만료/로테이션 미반영으로 이벤트 발행 인증 실패.

### Action Items
1. (즉시) 토큰/시크릿 로테이션 상태 확인 및 재배포.
2. (재발방지) 만료 알람 + 자동 로테이션/검증.

---

## 87. Out-of-Policy Retry (Non-Idempotent Endpoint)
---
service: api-gateway
error_message: retry applied to non-idempotent endpoint
---
### Incident Summary
[CRITICAL] 2024-05-01T11:26:00.000Z api-gateway/v1.9.0 [biz-087]: retry on non-idempotent | Context: {Route="/v1/payments/capture", Retries="3", Risk="double charge"}

### Root Cause
게이트웨이가 비멱등 엔드포인트에 자동 재시도를 적용.

### Action Items
1. (즉시) 비멱등 경로는 retry 비활성 또는 멱등키 필수.
2. (재발방지) 라우트별 retry 정책 표준화/검증.

---

## 88. Consistency Repair Job Failed
---
service: repair-job
error_message: repair job failed
---
### Incident Summary
[ERROR] 2024-05-01T11:27:00.000Z repair-job/v1.0.0 [biz-088]: repair job failed | Context: {Job="ledger_repair", Reason="db timeout", Batch="large"}

### Root Cause
정합성 복구 작업이 DB 부하를 유발해 실패.

### Action Items
1. (즉시) 복구 작업을 chunking/속도 제한으로 재실행.
2. (재발방지) 복구 잡은 오프피크 + 리소스 가드레일.

---

## 89. Inconsistent Idempotency Record (Write Lost)
---
service: payment-api
error_message: idempotency record missing after success
---
### Incident Summary
[ERROR] 2024-05-01T11:28:00.000Z payment-api/v5.5.0 [biz-089]: idempotency record missing | Context: {IdemKey="idem-8c1a", Payment="CAPTURED", StoreWrite="failed"}

### Root Cause
결제는 성공했는데 멱등 레코드 저장 실패로 재시도 시 중복 위험.

### Action Items
1. (즉시) 멱등 레코드 저장을 결제 상태 머신의 필수 단계로 강제.
2. (재발방지) 멱등 저장 실패 시 “PENDING_CONFIRMATION”으로 전환 + 조회 기반 확정.

---

## 90. Event Handler Performed External Call (Non-Deterministic)
---
service: order-consumer
error_message: external call inside handler caused inconsistency
---
### Incident Summary
[WARN] 2024-05-01T11:29:00.000Z order-consumer/v1.9.1 [biz-090]: external call inside handler | Context: {External="coupon-service", Timeout="2s", Retries="many"}

### Root Cause
이벤트 처리 중 외부 호출을 직접 수행해 지연/실패가 정합성에 영향을 줌.

### Action Items
1. (즉시) 외부 호출은 비동기 워크플로우로 분리.
2. (재발방지) “handler purity” 가이드(부작용 최소화) 제정.

---

## 91. RateLimit Leak (Missing TTL)
---
service: rate-limit-service
error_message: rate limit counter missing TTL
---
### Incident Summary
[WARN] 2024-05-01T11:30:00.000Z rate-limit-service/v2.3.0 [biz-091]: counter missing TTL | Context: {Key="rl:u-9912:/payments", TTL="none", KeysGrowing="fast"}

### Root Cause
카운터 키 TTL 누락으로 저장소가 계속 커짐.

### Action Items
1. (즉시) 모든 카운터는 TTL 강제.
2. (재발방지) 키 생성 공통 라이브러리로 강제 + 테스트.

---

## 92. Quota Double Count (Race)
---
service: quota-service
error_message: quota double counted
---
### Incident Summary
[ERROR] 2024-05-01T11:31:00.000Z quota-service/v1.4.0 [biz-092]: quota double counted | Context: {User="u-1", Increment="2", Expected="1", Cause="retry"}

### Root Cause
재시도/중복 요청을 quota 증가로 두 번 반영.

### Action Items
1. (즉시) quota increment도 멱등키로 보호.
2. (재발방지) quota는 이벤트 기반/원장 기반으로 산정하도록 개선.

---

## 93. Saga Step Uses Non-Idempotent DB Update
---
service: inventory-service
error_message: non-idempotent update in saga step
---
### Incident Summary
[WARN] 2024-05-01T11:32:00.000Z inventory-service/v3.8.0 [biz-093]: non-idempotent update | Context: {Step="reserve", Update="stock = stock - qty", Retry="true"}

### Root Cause
재시도 시 같은 차감이 반복되어 재고가 음수로 갈 수 있음.

### Action Items
1. (즉시) “예약 레코드” 기반으로 차감(이미 예약이면 no-op).
2. (재발방지) 재고는 원자적 조건 업데이트 + 예약 상태 머신.

---

## 94. Eventual Consistency – UI Shows Wrong Status
---
service: frontend-api
error_message: status mismatch due to eventual consistency
---
### Incident Summary
[INFO] 2024-05-01T11:33:00.000Z frontend-api/v1.0.0 [biz-094]: status mismatch | Context: {OrderId="o-7712", UI="PAID", Backend="PENDING_CONFIRMATION"}

### Root Cause
UI가 캐시/리플리카를 보거나 업데이트 지연으로 상태가 다르게 보임.

### Action Items
1. (즉시) 사용자-facing 상태 정의(처리중/확정) 정리.
2. (재발방지) 쓰기 직후 읽기 일관성 정책 + 캐시 무효화.

---

## 95. Competing Consumers Caused Duplicate Processing
---
service: broker-consumer
error_message: competing consumers misconfigured
---
### Incident Summary
[ERROR] 2024-05-01T11:34:00.000Z broker-consumer/v3.4.0 [biz-095]: misconfigured consumers | Context: {Group="payments", Instances="2", SamePartition="true"}

### Root Cause
컨슈머 그룹/파티션 설정 오류로 동일 파티션을 두 인스턴스가 동시에 처리.

### Action Items
1. (즉시) 컨슈머 그룹 설정 교정, 단일 소유권 보장.
2. (재발방지) 배포 전 컨슈머 토폴로지 검증.

---

## 96. Event Handler Non-Deterministic Time Dependency
---
service: settlement-service
error_message: nondeterministic time dependency
---
### Incident Summary
[WARN] 2024-05-01T11:35:00.000Z settlement-service/v2.9.0 [biz-096]: nondeterministic time dependency | Context: {Uses="now()", Effect="different settlement day"}

### Root Cause
핸들러가 now()에 의존해 재처리/리플레이 시 결과가 달라짐.

### Action Items
1. (즉시) 이벤트에 기준 시각(event_time)을 포함해 그 값을 사용.
2. (재발방지) 결정성(determinism) 가이드 + 테스트.

---

## 97. Cascade Failure From Single Downstream (No Bulkhead)
---
service: api-gateway
error_message: cascading failure detected
---
### Incident Summary
[CRITICAL] 2024-05-01T11:36:00.000Z api-gateway/v1.9.0 [biz-097]: cascading failure | Context: {Downstream="coupon-service", Latency="10s", AffectedRoutes="many"}

### Root Cause
벌크헤드/타임아웃이 없어서 하나의 다운스트림 지연이 전체 서비스로 전파.

### Action Items
1. (즉시) 타임아웃/서킷브레이커/벌크헤드 적용.
2. (재발방지) 장애 전파 차단 설계 표준화 + chaos 테스트.

---

## 98. SAGA – Manual Override Needed
---
service: ops-console
error_message: manual override required for stuck saga
---
### Incident Summary
[ALERT] 2024-05-01T11:37:00.000Z ops-console/v1.0.0 [biz-098]: manual override required | Context: {SagaId="s-9001", State="STUCK", Age="2h"}

### Root Cause
자동 보상/재시도로 복구 불가한 케이스(외부 시스템 불일치 등).

### Action Items
1. (즉시) 런북에 따라 수동 조정(결제 조회/원장 보정/재고 복구).
2. (재발방지) stuck saga 탐지/자동 티켓 + 수동 도구 개선.

---

## 99. Reconciliation Found Widespread Drift
---
service: reconciliation-job
error_message: widespread drift detected
---
### Incident Summary
[CRITICAL] 2024-05-01T11:38:00.000Z reconciliation-job/v1.2.0 [biz-099]: widespread drift | Context: {Entities="orders/payments/ledger", DriftRate="2.3%", Window="1h"}

### Root Cause
브로커 장애/대규모 lag/스키마 문제로 정합성 붕괴 범위가 확대.

### Action Items
1. (즉시) 이벤트 파이프라인 안정화 후, 기준 원장(ledger)을 source of truth로 복구 시나리오 수행.
2. (완화) 위험 구간 거래 제한/홀드.
3. (재발방지) 정합성 SLO/자동 차단(degrade) 정책.

---

## 100. Critical Fintech Incident – Money Movement Inconsistency
---
service: audit-service
error_message: money movement inconsistency detected
---
### Incident Summary
[CRITICAL] 2024-05-01T11:39:00.000Z audit-service/v1.0.0 [biz-100]: money movement inconsistency detected | Context: {UserId="u-9912", OrderId="o-7712", Payment="CAPTURED", Ledger="MISSING", Severity="SEV-1"}

### Root Cause
결제 성공(외부 사실)과 내부 원장 기록(내부 사실)이 불일치 → 금전 이동 정합성 위기.

### Action Items
1. (즉시) 결제/PG 조회를 기준으로 “사실” 확정 후 원장 재적재(append-only)로 복구.
2. (즉시) 영향 범위 트랜잭션 격리/홀드, 고객 응대/CS 공지 템플릿 가동.
3. (재발방지) outbox+멱등+재처리 파이프라인을 표준으로 강제하고, 정합성 배치/알람을 SEV-1 수준으로 상향.

---
