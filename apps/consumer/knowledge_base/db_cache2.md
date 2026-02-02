# CALI Simulated Log Cases – DB / Cache (01–100)
# 핀테크 도메인(주문/결제/정산/지갑/인증) 기준 + "로그 한 줄 + 대응 가이드" 형태

---

## 01. PostgreSQL Transaction Deadlock
---
service: order-service
error_message: deadlock detected (Process 123 waits for ShareLock)
---
### Incident Summary
[ERROR] 2024-03-15T11:00:00.101Z order-service/v3.2.1 [pg-001]: deadlock detected (Process 123 waits for ShareLock on transaction 987; blocked by process 456) | Context: {Table="orders", Tx="update status", Concurrency="high", TxId="tx-9a1f"}

### Root Cause
동일 레코드를 서로 다른 순서로 잠그는 트랜잭션이 동시에 실행되어 교착 상태 발생.

### Action Items
1. (즉시) Deadlock 로그에서 관련 쿼리/테이블/락 타입 확인.
2. (완화) 트랜잭션 내 락 획득 순서를 고정(항상 orders→payments 등).
3. (완화) 애플리케이션 레벨 retry(backoff+jitter) 적용.
4. (재발방지) 긴 트랜잭션 제거/인덱스 최적화/쿼리 단순화.

---

## 02. PostgreSQL Lock Timeout
---
service: wallet-service
error_message: canceling statement due to lock timeout
---
### Incident Summary
[ERROR] 2024-03-15T11:01:10.212Z wallet-service/v2.8.0 [pg-002]: canceling statement due to lock timeout | Context: {Table="wallet_balance", Timeout="5s", Query="UPDATE ...", Holders="batch-settlement"}

### Root Cause
배치/정산 작업이 장시간 락을 점유하여 온라인 트랜잭션이 lock_timeout에 걸림.

### Action Items
1. (즉시) 어떤 세션이 락을 잡고 있는지 확인(락 대기/보유 세션).
2. (완화) 배치 쿼리 chunking(범위 분할) + 커밋 단위 축소.
3. (완화) 온라인 경로는 짧은 쿼리로 유지, 인덱스 점검.
4. (재발방지) 배치 윈도우 분리 + 우선순위/리밋 정책.

---

## 03. PostgreSQL Connection Pool Exhausted
---
service: payment-api
error_message: remaining connection slots are reserved for non-replication superuser
---
### Incident Summary
[ERROR] 2024-03-15T11:02:00.333Z payment-api/v5.1.2 [pg-003]: remaining connection slots are reserved for non-replication superuser | Context: {DB="payments", PoolMax="50", InUse="50", Waiting="120", Spike="traffic"}

### Root Cause
트래픽 급증/커넥션 누수/풀 설정 미스매치로 커넥션 슬롯 고갈.

### Action Items
1. (즉시) 풀 사용량/대기 큐 확인, 누수 여부(미반납) 점검.
2. (완화) 임시로 풀 상향(주의: DB 부하) 또는 앱 스케일아웃.
3. (확인) 쿼리 지연으로 커넥션 점유 시간이 길어진 원인(슬로우쿼리).
4. (재발방지) pgbouncer 도입/적정 pool sizing/timeout 표준화.

---

## 04. PostgreSQL Too Many Clients (RDS max_connections)
---
service: settlement-worker
error_message: too many clients already
---
### Incident Summary
[ERROR] 2024-03-15T11:03:20.010Z settlement-worker/v1.9.0 [pg-004]: too many clients already | Context: {DB="settlement", MaxConn="200", Active="200", NewConn="retries"}

### Root Cause
애플리케이션이 재시도하면서 신규 커넥션 폭증. pool 미사용 또는 pool이 DB보다 큼.

### Action Items
1. (즉시) 앱의 풀 사용 여부 확인(매 요청 신규 연결 금지).
2. (완화) 재시도에 backoff+jitter 적용, 커넥션 생성 rate-limit.
3. (재발방지) pgbouncer/풀 표준화 + RDS 파라미터 적정화.

---

## 05. PostgreSQL Read Replica Lag High
---
service: analytics-api
error_message: replica lag exceeds threshold
---
### Incident Summary
[WARN] 2024-03-15T11:04:00.000Z analytics-api/v2.4.3 [pg-005]: replica lag exceeds threshold | Context: {Replica="read-1", Lag="12s", Threshold="2s", Writes="high"}

### Root Cause
쓰기 급증/장기 트랜잭션/IO 병목으로 리플리카 적용 지연. 읽기 일관성 문제 발생 가능.

### Action Items
1. (즉시) lag 원인(쓰기량, long tx, vacuum) 파악.
2. (완화) 중요한 읽기는 primary로 우회 또는 lag 기반 라우팅.
3. (재발방지) 인덱스/쿼리 최적화 + 배치 분산 + 스토리지 튜닝.

---

## 06. PostgreSQL Autovacuum Falling Behind
---
service: order-service
error_message: autovacuum not keeping up
---
### Incident Summary
[WARN] 2024-03-15T11:05:00.000Z order-service/v3.2.1 [pg-006]: autovacuum not keeping up | Context: {Table="orders", DeadTuples="12M", Bloat="high", TPS="peak"}

### Root Cause
삭제/업데이트가 많아 dead tuple 누적, vacuum 지연 → bloat 증가, 쿼리 느려짐.

### Action Items
1. (즉시) bloat/DeadTuples 상위 테이블 확인.
2. (완화) autovacuum 튜닝(진행률, 비용) 또는 수동 vacuum(주의).
3. (재발방지) 파티셔닝/아카이빙 + 업데이트 패턴 개선.

---

## 07. PostgreSQL Slow Query (Seq Scan)
---
service: payment-api
error_message: slow query detected > 2s
---
### Incident Summary
[WARN] 2024-03-15T11:06:00.000Z payment-api/v5.1.2 [pg-007]: slow query detected > 2s | Context: {Query="SELECT * FROM payments WHERE merchant_id=... AND created_at>...", Plan="Seq Scan", P95="2.7s"}

### Root Cause
인덱스 누락/통계 부정확/조건 비선택성으로 Seq Scan 발생.

### Action Items
1. (즉시) 실행 계획(EXPLAIN ANALYZE) 확인.
2. (완화) 필요한 복합 인덱스 생성(merchant_id, created_at).
3. (재발방지) 슬로우쿼리 알람 + 주기적 통계 갱신/인덱스 리뷰.

---

## 08. PostgreSQL Statement Timeout
---
service: wallet-service
error_message: canceling statement due to statement timeout
---
### Incident Summary
[ERROR] 2024-03-15T11:07:00.000Z wallet-service/v2.8.0 [pg-008]: canceling statement due to statement timeout | Context: {Timeout="3s", Query="SELECT ... FOR UPDATE", HotKey="user_1283"}

### Root Cause
핫키/락 경합/슬로우 플랜으로 쿼리 시간이 timeout 초과.

### Action Items
1. (즉시) 핫키/락 대기 확인, 동일 키 집중 트래픽 여부 확인.
2. (완화) 큐잉/샤딩/락 범위 축소, 인덱스 최적화.
3. (재발방지) 핫키 탐지 + 레이트리밋/분산 설계.

---

## 09. PostgreSQL Unique Constraint Violation (Idempotency)
---
service: payment-api
error_message: duplicate key value violates unique constraint "payments_idempotency_key_key"
---
### Incident Summary
[WARN] 2024-03-15T11:08:00.000Z payment-api/v5.1.2 [pg-009]: duplicate key value violates unique constraint "payments_idempotency_key_key" | Context: {IdempotencyKey="idem-8c1a", OrderId="o-7712", Retries="client"}

### Root Cause
멱등키가 정상 작동하여 중복 결제를 차단. 하지만 앱이 예외를 에러로 처리하며 불필요 재시도할 수 있음.

### Action Items
1. (즉시) 해당 키의 기존 결제 상태 조회 후 동일 응답 반환(멱등).
2. (완화) 중복 요청은 200/409 등 설계된 응답으로 처리.
3. (재발방지) 멱등 처리 경로 표준화 + 클라 재시도 정책 정리.

---

## 10. PostgreSQL Serialization Failure
---
service: inventory-service
error_message: could not serialize access due to read/write dependencies among transactions
---
### Incident Summary
[ERROR] 2024-03-15T11:09:00.000Z inventory-service/v2.1.0 [pg-010]: could not serialize access due to read/write dependencies | Context: {Isolation="SERIALIZABLE", HotSKU="sku-55", Concurrency="peak"}

### Root Cause
SERIALIZABLE 격리 수준에서 동시성 충돌이 발생. 재시도 없으면 실패율 증가.

### Action Items
1. (즉시) 애플리케이션 레벨 재시도(backoff+jitter) 적용.
2. (완화) 격리 수준 조정(가능 시) 또는 트랜잭션 범위 축소.
3. (재발방지) 핫 리소스 분산(샤딩/큐) + 재고 업데이트 전략 개선.

---

## 11. MySQL Lock Wait Timeout
---
service: merchant-service
error_message: Lock wait timeout exceeded; try restarting transaction
---
### Incident Summary
[ERROR] 2024-03-15T11:10:00.000Z merchant-service/v1.7.2 [my-011]: Lock wait timeout exceeded | Context: {Table="merchant_config", Tx="update", Timeout="50s"}

### Root Cause
긴 트랜잭션/배치가 락을 점유해 대기 timeout 발생.

### Action Items
1. (즉시) 락 보유 트랜잭션 확인 및 배치 중단/분할.
2. (완화) 인덱스/쿼리 최적화로 락 시간 축소.
3. (재발방지) 배치 오프피크/작업 단위 축소.

---

## 12. MongoDB Primary Stepdown
---
service: analytics-worker
error_message: not primary and secondaryOk=false
---
### Incident Summary
[ERROR] 2024-03-15T11:11:00.000Z analytics-worker/v1.2.0 [mg-012]: not primary and secondaryOk=false | Context: {ReplicaSet="rs0", Write="true", Stepdown="detected"}

### Root Cause
Primary stepdown/선출로 쓰기 요청이 잠시 실패.

### Action Items
1. (즉시) 드라이버 재시도/리트라이어블 라이트 설정 확인.
2. (확인) stepdown 원인(리소스/네트워크) 확인.
3. (재발방지) 모니터링/적정 리소스/선출 안정화.

---

## 13. Redis Max Memory Reached
---
service: cache-common
error_message: OOM command not allowed when used memory > 'maxmemory'
---
### Incident Summary
[ERROR] 2024-03-15T11:12:00.000Z cache-common/v6.2 [rd-013]: OOM command not allowed when used memory > 'maxmemory' | Context: {Used="15.9Gi", Max="16Gi", TopKeys="session:*", TTL="missing"}

### Root Cause
TTL 미설정 키 누적 또는 eviction 정책 부적절로 메모리 고갈.

### Action Items
1. (즉시) eviction policy(allkeys-lru 등) 및 maxmemory 확인.
2. (완화) TTL 누락 키 정리(패턴 삭제/샘플링) + TTL 적용.
3. (재발방지) 캐시 키 표준(필수 TTL) + 키 사이즈 알람.

---

## 14. Redis Eviction Storm
---
service: cache-common
error_message: evicted_keys rate high
---
### Incident Summary
[WARN] 2024-03-15T11:13:00.000Z cache-common/v6.2 [rd-014]: eviction storm detected | Context: {Evicted="2M/10m", HitRate="45%", Latency="increasing"}

### Root Cause
메모리 부족으로 eviction이 폭주 → 캐시 미스 증가 → DB 부하 상승(캐시-DB 스파이크).

### Action Items
1. (즉시) 캐시 용량 확장(샤드/메모리) 또는 TTL 조정.
2. (완화) 핫키/큰 키 제거, 캐시 워밍 전략 조정.
3. (재발방지) 캐시 히트율/eviction 알람 + 데이터 분산.

---

## 15. Redis Latency Spike (Slowlog)
---
service: cache-common
error_message: redis latency spike
---
### Incident Summary
[WARN] 2024-03-15T11:14:00.000Z cache-common/v6.2 [rd-015]: redis latency spike | Context: {P99="80ms", Baseline="2ms", SlowlogTop="HGETALL large hash"}

### Root Cause
큰 키/비효율 명령(HGETALL, KEYS) 또는 네트워크/CPU 포화.

### Action Items
1. (즉시) SLOWLOG 확인, 상위 명령 식별 및 차단/개선.
2. (완화) 큰 키 분할, SCAN 사용, 파이프라이닝 적용.
3. (재발방지) 금지 명령 정책 + 키 사이즈 관측.

---

## 16. Redis Replication Lag
---
service: cache-common
error_message: replication lag high
---
### Incident Summary
[WARN] 2024-03-15T11:15:00.000Z cache-common/v6.2 [rd-016]: replication lag high | Context: {Lag="5s", Threshold="1s", Writes="spike"}

### Root Cause
쓰기 폭증/네트워크 지연으로 replica가 따라가지 못함.

### Action Items
1. (즉시) 읽기 라우팅을 primary로 우회(일시).
2. (완화) shard 확장/쓰기 감소(배치 분산).
3. (재발방지) 리플리카 지표 알람 + 용량 계획.

---

## 17. Redis Failover Loop
---
service: cache-common
error_message: failover triggered repeatedly
---
### Incident Summary
[CRITICAL] 2024-03-15T11:16:00.000Z cache-common/v6.2 [rd-017]: failover loop | Context: {Failovers="6/30m", Reason="node flapping", ClientErrors="spike"}

### Root Cause
노드/네트워크 불안정으로 failover가 반복 발생 → 클라 재연결 폭주.

### Action Items
1. (즉시) 네트워크/노드 안정화, 문제 노드 격리.
2. (완화) 클라 reconnect/backoff 설정 확인.
3. (재발방지) 멀티 AZ/안정화 설정 + 장애 테스트.

---

## 18. Redis Cluster Slot Migration Stuck
---
service: cache-common
error_message: CLUSTERDOWN Hash slot migration
---
### Incident Summary
[ERROR] 2024-03-15T11:17:00.000Z cache-common/v6.2 [rd-018]: CLUSTERDOWN during slot migration | Context: {State="migrating", Slots="2048", Stuck="true"}

### Root Cause
리샤딩/슬롯 이동 중 네트워크/노드 문제로 cluster 상태 불안정.

### Action Items
1. (즉시) 리샤딩 작업 중단/롤백 여부 판단, 노드 상태 확인.
2. (완화) 트래픽 제한 후 작업 재개.
3. (재발방지) 리샤딩 런북/오프피크 작업.

---

## 19. Cache Stampede (Miss Storm)
---
service: cache-common
error_message: cache miss storm
---
### Incident Summary
[WARN] 2024-03-15T11:18:00.000Z cache-common/v6.2 [rd-019]: cache miss storm | Context: {HitRate="10%", QPS="200k", ExpiredKeys="many", DBLoad="high"}

### Root Cause
동시에 TTL 만료/콜드스타트로 캐시 미스가 폭주하며 DB를 때림.

### Action Items
1. (즉시) TTL에 jitter 적용, hot key 사전 워밍.
2. (완화) singleflight/락으로 동시 재생성 방지.
3. (재발방지) 캐시 갱신 전략(early refresh) + 미스 알람.

---

## 20. Hot Key Detected (Redis)
---
service: cache-common
error_message: hot key detected
---
### Incident Summary
[WARN] 2024-03-15T11:19:00.000Z cache-common/v6.2 [rd-020]: hot key detected | Context: {Key="price:btc-krw", QPS="60k", Shard="1", Latency="increasing"}

### Root Cause
특정 키로 트래픽 집중 → 단일 샤드/노드 병목.

### Action Items
1. (즉시) 키 샤딩(예: price:btc-krw:{0..N}) 또는 로컬 캐시 적용.
2. (완화) 응답 캐싱 계층 추가(CDN/Edge).
3. (재발방지) 핫키 탐지/자동 분산.

---

## 21. PostgreSQL Disk Full
---
service: rds-postgresql
error_message: could not extend file: No space left on device
---
### Incident Summary
[CRITICAL] 2024-03-15T11:20:00.000Z rds-postgresql/15 [pg-021]: could not extend file: No space left on device | Context: {DB="orders", VolumeUsed="99%", Table="orders_idx"}

### Root Cause
데이터/인덱스/로그(bloat 포함) 증가로 스토리지 고갈.

### Action Items
1. (즉시) 스토리지 확장(운영 절차에 따라) + 긴급 정리(아카이브).
2. (확인) 상위 테이블/인덱스/로그 사용량 분석.
3. (재발방지) 파티셔닝/아카이빙 + vacuum/인덱스 관리 + 용량 알람.

---

## 22. PostgreSQL WAL Growth Spike
---
service: rds-postgresql
error_message: WAL size exceeds threshold
---
### Incident Summary
[WARN] 2024-03-15T11:21:00.000Z rds-postgresql/15 [pg-022]: WAL size exceeds threshold | Context: {WAL="180Gi", Threshold="50Gi", ReplicaLag="high"}

### Root Cause
대량 업데이트/배치로 WAL 급증, 리플리카 lag와 결합 시 저장공간 압박.

### Action Items
1. (즉시) 배치 중단/분할, replica lag 원인 제거.
2. (확인) long tx/replication slot 상태 확인.
3. (재발방지) 배치 chunking + WAL/replication 모니터링.

---

## 23. PostgreSQL Replication Slot Bloat
---
service: rds-postgresql
error_message: replication slot preventing WAL recycle
---
### Incident Summary
[ERROR] 2024-03-15T11:22:00.000Z rds-postgresql/15 [pg-023]: replication slot preventing WAL recycle | Context: {Slot="debezium", RetainedWAL="120Gi", Consumer="down"}

### Root Cause
CDC/스트리밍 소비자가 다운되어 슬롯이 WAL 재활용을 막음.

### Action Items
1. (즉시) 소비자 복구 또는 슬롯 비활성/삭제(데이터 손실 영향 고려).
2. (재발방지) CDC 헬스체크/알람 + 슬롯 보존 한도 정책.

---

## 24. PostgreSQL Checkpoint Too Frequent
---
service: rds-postgresql
error_message: checkpoints are occurring too frequently
---
### Incident Summary
[WARN] 2024-03-15T11:23:00.000Z rds-postgresql/15 [pg-024]: checkpoints are occurring too frequently | Context: {WriteSpike="true", IOWait="high", CheckpointInterval="30s"}

### Root Cause
쓰기 폭증/설정 미스(wal_size 낮음)로 체크포인트가 잦아져 I/O 스톨 유발.

### Action Items
1. (즉시) 쓰기 스파이크 원인 차단(배치 분산).
2. (완화) checkpoint 관련 파라미터 튜닝(운영 정책에 따라).
3. (재발방지) 쓰기 패턴 최적화 + I/O 모니터링.

---

## 25. PostgreSQL Too Many Prepared Transactions
---
service: settlement-worker
error_message: too many prepared transactions
---
### Incident Summary
[ERROR] 2024-03-15T11:24:00.000Z settlement-worker/v1.9.0 [pg-025]: too many prepared transactions | Context: {TwoPhase="enabled", Prepared="1024", Limit="1024"}

### Root Cause
2PC 사용 중 prepare 상태 트랜잭션이 정리되지 않음(코디네이터 장애).

### Action Items
1. (즉시) prepared xacts 목록 확인, 안전하게 commit/rollback 처리.
2. (재발방지) 2PC 최소화 + 장애 복구 절차/모니터링.

---

## 26. Aurora Failover Detected
---
service: rds-aurora
error_message: Aurora failover in progress
---
### Incident Summary
[WARN] 2024-03-15T11:25:00.000Z rds-aurora/pg [au-026]: Aurora failover in progress | Context: {Cluster="payments-aurora", Writer="changing", Errors="connection reset"}

### Root Cause
Writer 노드 장애/유지보수로 failover 발생 → 짧은 쓰기 중단.

### Action Items
1. (즉시) 앱 재시도(backoff) 및 커넥션 재수립 확인.
2. (재발방지) 드라이버 failover 설정/멀티 AZ 테스트.

---

## 27. RDS CPU Saturation
---
service: rds-postgresql
error_message: CPU utilization high
---
### Incident Summary
[CRITICAL] 2024-03-15T11:26:00.000Z rds-postgresql/15 [pg-027]: CPU utilization high | Context: {CPU="98%", TopQuery="SELECT ...", Connections="180"}

### Root Cause
슬로우쿼리/풀 과다/캐시 미스 등으로 DB CPU 포화.

### Action Items
1. (즉시) Top 쿼리 식별(Performance Insights/slowlog) 후 차단/튜닝.
2. (완화) 읽기 분산(리플리카), 캐시 강화, 커넥션 제한.
3. (재발방지) 쿼리/인덱스 리뷰, 부하테스트, 캐시 전략.

---

## 28. RDS IOPS Saturation
---
service: rds-postgresql
error_message: storage iops burst balance low
---
### Incident Summary
[WARN] 2024-03-15T11:27:00.000Z rds-postgresql/15 [pg-028]: storage iops burst balance low | Context: {BurstBalance="2%", ReadIOPS="16000", WriteIOPS="9000"}

### Root Cause
랜덤 I/O 폭증(대량 인덱스 작업/풀스캔)으로 IOPS 한계 도달.

### Action Items
1. (즉시) 비용 큰 작업 중단(리빌드/배치) 또는 오프피크로 이동.
2. (완화) 스토리지 타입/IOPS 상향.
3. (재발방지) 인덱스/쿼리 최적화 + I/O 알람.

---

## 29. RDS Memory Pressure (Cache Hit Drop)
---
service: rds-postgresql
error_message: buffer cache hit ratio dropped
---
### Incident Summary
[WARN] 2024-03-15T11:28:00.000Z rds-postgresql/15 [pg-029]: buffer cache hit ratio dropped | Context: {HitRatio="72%", Baseline="98%", WorkingSet="increased"}

### Root Cause
워크로드 변화/데이터 증가로 캐시 효율 저하 → 디스크 I/O 증가.

### Action Items
1. (즉시) 캐시 미스 유발 쿼리/테이블 확인.
2. (완화) 인스턴스 메모리 상향 또는 캐시/파티셔닝 전략 개선.
3. (재발방지) 데이터 핫/콜드 분리, 접근 패턴 최적화.

---

## 30. Postgres TLS Handshake Failure
---
service: order-service
error_message: SSL error: certificate verify failed
---
### Incident Summary
[ERROR] 2024-03-15T11:29:00.000Z order-service/v3.2.1 [pg-030]: SSL error: certificate verify failed | Context: {DBHost="orders-db", CA="missing", Client="new image"}

### Root Cause
DB CA 번들 누락/교체 또는 클라이언트 이미지 업데이트로 인증서 검증 실패.

### Action Items
1. (즉시) 최신 CA 번들 반영 및 연결 테스트.
2. (재발방지) 베이스 이미지 업데이트 시 TLS 검증 체크리스트 포함.

---

## 31. Redis AUTH Failed
---
service: cache-common
error_message: NOAUTH Authentication required
---
### Incident Summary
[ERROR] 2024-03-15T11:30:00.000Z cache-common/v6.2 [rd-031]: NOAUTH Authentication required | Context: {Client="wallet-service", Endpoint="redis://cache:6379", Secret="rotated?"}

### Root Cause
패스워드/ACL 변경(로테이션) 후 앱 시크릿 미반영.

### Action Items
1. (즉시) 최신 Redis 자격증명/ACL 적용 여부 확인.
2. (완화) 시크릿 업데이트 후 롤링 재시작.
3. (재발방지) 시크릿 로테이션 자동화 + 적용 검증.

---

## 32. Redis ACL Deny
---
service: cache-common
error_message: NOPERM this user has no permissions
---
### Incident Summary
[ERROR] 2024-03-15T11:31:00.000Z cache-common/v6.2 [rd-032]: NOPERM this user has no permissions | Context: {User="app", Cmd="FLUSHALL", Policy="restricted"}

### Root Cause
ACL이 명령을 거부(의도된 제한). 앱이 금지 명령을 호출.

### Action Items
1. (즉시) 앱 코드에서 금지 명령 제거(FLUSHALL/KEYS 등).
2. (재발방지) Redis 명령 허용 목록 기반 개발 가이드.

---

## 33. Redis Cluster MOVED Errors Spike
---
service: cache-common
error_message: MOVED redirection
---
### Incident Summary
[WARN] 2024-03-15T11:32:00.000Z cache-common/v6.2 [rd-033]: MOVED redirection spike | Context: {Rate="20k/s", Client="old driver", Resharding="true"}

### Root Cause
클라이언트가 슬롯 캐시를 업데이트 못하거나 리샤딩 중 리다이렉션 증가.

### Action Items
1. (즉시) 클러스터 지원 드라이버/설정(cluster mode) 확인.
2. (완화) 리샤딩 시 트래픽 제한.
3. (재발방지) 드라이버 표준화 + 리샤딩 절차.

---

## 34. Redis CROSSSLOT Error
---
service: cache-common
error_message: CROSSSLOT Keys in request don't hash to the same slot
---
### Incident Summary
[ERROR] 2024-03-15T11:33:00.000Z cache-common/v6.2 [rd-034]: CROSSSLOT error | Context: {Cmd="MGET", Keys="user:1, user:2", HashTag="missing"}

### Root Cause
클러스터 모드에서 멀티키 연산이 다른 슬롯에 걸려 실패(해시태그 미사용).

### Action Items
1. (즉시) 관련 키에 hash tag 적용(예: user:{id}:profile).
2. (재발방지) 멀티키 연산 설계 가이드/테스트.

---

## 35. Redis ReadOnly Error (Replica)
---
service: cache-common
error_message: READONLY You can't write against a read only replica
---
### Incident Summary
[ERROR] 2024-03-15T11:34:00.000Z cache-common/v6.2 [rd-035]: READONLY error | Context: {Client="payment-api", Endpoint="replica", Write="SET"}

### Root Cause
쓰기 트래픽이 replica 엔드포인트로 라우팅됨(설정/서비스 디스커버리 오류).

### Action Items
1. (즉시) 엔드포인트 설정 확인(primary/replica 구분).
2. (재발방지) 클라 라우팅 정책/테스트 + 서비스 이름 분리.

---

## 36. Redis Connection Reset
---
service: cache-common
error_message: Connection reset by peer
---
### Incident Summary
[ERROR] 2024-03-15T11:35:00.000Z cache-common/v6.2 [rd-036]: Connection reset by peer | Context: {Connections="reconnect storm", Node="cache-2", CPU="high"}

### Root Cause
노드 재시작/네트워크/CPU 포화로 커넥션이 리셋.

### Action Items
1. (즉시) 노드 상태/리소스 확인, 재시작 이벤트 확인.
2. (완화) 클라 reconnect backoff 설정.
3. (재발방지) 커넥션 풀 튜닝 + 노드 안정화.

---

## 37. Redis Client Output Buffer Limit Reached
---
service: cache-common
error_message: client-output-buffer-limit reached
---
### Incident Summary
[WARN] 2024-03-15T11:36:00.000Z cache-common/v6.2 [rd-037]: client output buffer limit reached | Context: {Client="pubsub-subscriber", Buffer="256MB", Disconnect="true"}

### Root Cause
Pub/Sub 구독자가 느려서 출력 버퍼가 한도 초과 → 연결 강제 종료.

### Action Items
1. (즉시) 구독자 소비 속도/병렬성 개선.
2. (완화) 메시지 크기/빈도 제한, 스트림으로 전환 검토.
3. (재발방지) backpressure 설계 + 버퍼/알람.

---

## 38. Redis Keyspace Notifications Flood
---
service: cache-common
error_message: notification rate high
---
### Incident Summary
[WARN] 2024-03-15T11:37:00.000Z cache-common/v6.2 [rd-038]: keyspace notifications flood | Context: {Events="1M/min", CPU="90%", Feature="enabled"}

### Root Cause
키스페이스 이벤트가 과도하게 발생해 Redis CPU를 잡아먹음.

### Action Items
1. (즉시) 필요하지 않으면 notifications 비활성/범위 축소.
2. (재발방지) 이벤트 사용 시 제한/샘플링/알람.

---

## 39. Redis Lua Script Timeout
---
service: cache-common
error_message: BUSY Redis is busy running a script
---
### Incident Summary
[ERROR] 2024-03-15T11:38:00.000Z cache-common/v6.2 [rd-039]: BUSY running a script | Context: {Script="settlement.lua", Duration="8s", ClientsBlocked="true"}

### Root Cause
긴 Lua 스크립트가 단일 스레드 Redis를 블로킹.

### Action Items
1. (즉시) 스크립트 최적화/분할 또는 백그라운드 처리로 전환.
2. (완화) 스크립트 kill(주의) 및 영향 평가.
3. (재발방지) Lua 스크립트 성능 가이드/테스트.

---

## 40. Redis RDB/AOF Rewrite Blocking
---
service: cache-common
error_message: background save in progress
---
### Incident Summary
[WARN] 2024-03-15T11:39:00.000Z cache-common/v6.2 [rd-040]: persistence causing latency | Context: {Mode="AOF rewrite", LatencyP99="60ms"}

### Root Cause
AOF rewrite/RDB 저장 시 디스크 I/O로 지연 증가.

### Action Items
1. (즉시) persistence 설정 확인(AOF fsync 정책).
2. (완화) 디스크 성능 상향 또는 오프피크 수행.
3. (재발방지) 캐시/퍼시스턴스 요구사항 재정의(정말 필요한지).

---

## 41. DynamoDB Provisioned Throughput Exceeded
---
service: fraud-service
error_message: ProvisionedThroughputExceededException
---
### Incident Summary
[ERROR] 2024-03-15T11:40:00.000Z fraud-service/v4.0.0 [dy-041]: ProvisionedThroughputExceededException | Context: {Table="fraud_signals", Mode="provisioned", RCU="1000", WCU="1000", Spike="3x"}

### Root Cause
트래픽 급증으로 RCU/WCU 초과, 재시도 폭주.

### Action Items
1. (즉시) exponential backoff+jitter 적용(이미 있더라도 확인).
2. (완화) auto-scaling/온디맨드 전환 검토.
3. (재발방지) 핫 파티션 방지(키 설계) + 용량 알람.

---

## 42. DynamoDB Hot Partition
---
service: fraud-service
error_message: hot partition suspected
---
### Incident Summary
[WARN] 2024-03-15T11:41:00.000Z fraud-service/v4.0.0 [dy-042]: hot partition suspected | Context: {PartitionKey="merchant#123", Requests="80k/min", Throttle="true"}

### Root Cause
파티션키 쏠림으로 특정 파티션이 과부하.

### Action Items
1. (즉시) 파티션키에 랜덤/버킷 접두를 추가해 분산.
2. (재발방지) 키 설계 가이드 + 핫키 알람.

---

## 43. DynamoDB Conditional Check Failed
---
service: wallet-service
error_message: ConditionalCheckFailedException
---
### Incident Summary
[INFO] 2024-03-15T11:42:00.000Z wallet-service/v2.8.0 [dy-043]: ConditionalCheckFailedException | Context: {Op="update balance", Condition="version match", UserId="u-9912"}

### Root Cause
낙관적 락(버전) 조건이 맞지 않아 업데이트가 거절됨(정상 동시성 제어).

### Action Items
1. (즉시) 최신 버전 재조회 후 재시도(한정 횟수).
2. (재발방지) 충돌률 높으면 샤딩/큐 기반으로 갱신 전략 개선.

---

## 44. DynamoDB Transaction Canceled
---
service: payment-api
error_message: TransactionCanceledException
---
### Incident Summary
[ERROR] 2024-03-15T11:43:00.000Z payment-api/v5.1.2 [dy-044]: TransactionCanceledException | Context: {Reason="ConditionalCheckFailed", Items="2", Tx="capture+ledger"}

### Root Cause
트랜잭션 내 조건 실패/동시성 충돌/한도 초과.

### Action Items
1. (즉시) cancellation reasons를 파싱해 어떤 조건이 실패했는지 확인.
2. (완화) 재시도(backoff) 및 트랜잭션 범위 축소.
3. (재발방지) 설계상 충돌 지점 분산(아이템/키).

---

## 45. DynamoDB TTL Not Expiring
---
service: cache-common
error_message: ttl backlog suspected
---
### Incident Summary
[WARN] 2024-03-15T11:44:00.000Z cache-common/v1.0 [dy-045]: TTL backlog suspected | Context: {Table="session_cache", ExpiredItems="high", Storage="growing"}

### Root Cause
DynamoDB TTL은 즉시 삭제가 아니라 지연될 수 있음 → 스토리지 증가로 오해/비용 증가.

### Action Items
1. (즉시) TTL 특성(지연 삭제) 인지, 만료 설계를 앱에서 보완(읽기 시 필터).
2. (재발방지) TTL 기반 비용 모니터링 + 필요 시 별도 정리 잡.

---

## 46. PostgreSQL Index Corruption Suspected
---
service: rds-postgresql
error_message: could not read block
---
### Incident Summary
[CRITICAL] 2024-03-15T11:45:00.000Z rds-postgresql/15 [pg-046]: could not read block | Context: {Relation="orders_idx", Block="12345", Symptom="IO error"}

### Root Cause
스토리지/파일 손상 가능성(드물지만). 즉시 복구 절차 필요.

### Action Items
1. (즉시) 영향 범위 확인, 읽기/쓰기 제한 및 장애 대응 프로세스 가동.
2. (완화) 복제본 승격/스냅샷 복구 검토.
3. (재발방지) 백업/복구 리허설 + 스토리지 지표 알람.

---

## 47. Postgres Vacuum Freeze Age High
---
service: rds-postgresql
error_message: vacuum freeze required
---
### Incident Summary
[WARN] 2024-03-15T11:46:00.000Z rds-postgresql/15 [pg-047]: vacuum freeze required | Context: {Database="orders", Age="1.8B", Limit="2B"}

### Root Cause
트랜잭션 ID wraparound 위험. vacuum freeze가 제때 수행되지 않음.

### Action Items
1. (즉시) vacuum freeze 실행(운영 절차 준수).
2. (재발방지) autovacuum 튜닝 + wraparound 알람.

---

## 48. Postgres Long Running Transaction
---
service: rds-postgresql
error_message: long running transaction detected
---
### Incident Summary
[WARN] 2024-03-15T11:47:00.000Z rds-postgresql/15 [pg-048]: long running transaction detected | Context: {Pid="8831", Duration="45m", App="reporting", Impact="vacuum blocked"}

### Root Cause
리포팅/배치가 트랜잭션을 오래 유지해 vacuum/replication에 악영향.

### Action Items
1. (즉시) 해당 세션 종료 또는 read-only 트랜잭션으로 변경.
2. (재발방지) 리포팅은 리플리카/별도 DB로 분리, 트랜잭션 최소화.

---

## 49. Postgres Temp File Explosion
---
service: rds-postgresql
error_message: temporary file size exceeds threshold
---
### Incident Summary
[WARN] 2024-03-15T11:48:00.000Z rds-postgresql/15 [pg-049]: temp file explosion | Context: {Query="ORDER BY large", Temp="80Gi", WorkMem="4Mi"}

### Root Cause
정렬/해시가 work_mem을 초과해 temp file을 대량 생성 → I/O 폭증.

### Action Items
1. (즉시) 해당 쿼리 최적화(인덱스/limit) 또는 work_mem 조정(주의).
2. (재발방지) 쿼리 리뷰/리포팅 분리 + temp file 알람.

---

## 50. Postgres Extension Missing After Upgrade
---
service: rds-postgresql
error_message: could not open extension control file
---
### Incident Summary
[ERROR] 2024-03-15T11:49:00.000Z rds-postgresql/15 [pg-050]: could not open extension control file | Context: {Extension="uuid-ossp", After="minor upgrade"}

### Root Cause
업그레이드/파라미터 그룹 변경 후 확장 설정 불일치.

### Action Items
1. (즉시) 확장 설치/권한 확인.
2. (재발방지) 업그레이드 체크리스트에 확장 검증 포함.

---

# 51–100: DB/Cache 후반 (요청 구간)

## 51. Redis Cluster State CLUSTERDOWN
---
service: cache-common
error_message: CLUSTERDOWN The cluster is down
---
### Incident Summary
[CRITICAL] 2024-03-15T11:50:00.000Z cache-common/v6.2 [rd-051]: CLUSTERDOWN The cluster is down | Context: {NodesDown="3/6", SlotsFail="true", ClientErrors="spike"}

### Root Cause
다수 노드 다운/네트워크 분리로 클러스터가 슬롯을 제공하지 못함.

### Action Items
1. (즉시) 다운 노드/네트워크 상태 확인 및 복구(재시작/교체).
2. (완화) 클라 재시도 backoff 강화, 트래픽 감산.
3. (재발방지) 멀티 AZ/오토리커버리 + 클러스터 헬스 알람.

---

## 52. Redis Master Link Down
---
service: cache-common
error_message: MASTERDOWN Link with MASTER is down
---
### Incident Summary
[ERROR] 2024-03-15T11:51:00.000Z cache-common/v6.2 [rd-052]: MASTERDOWN Link with MASTER is down | Context: {Replica="cache-3", Master="cache-1", Lag="infinite"}

### Root Cause
마스터 장애 또는 네트워크 분리로 레플리카가 동기화 불가.

### Action Items
1. (즉시) 마스터 노드 상태 확인 및 failover 상태 점검.
2. (완화) 읽기/쓰기 라우팅 정책 재확인.
3. (재발방지) 네트워크 안정화 + 장애 테스트.

---

## 53. Redis Loading Dataset Into Memory
---
service: cache-common
error_message: LOADING Redis is loading the dataset in memory
---
### Incident Summary
[WARN] 2024-03-15T11:52:00.000Z cache-common/v6.2 [rd-053]: LOADING Redis is loading dataset | Context: {Restart="true", RDB="large", Duration="90s"}

### Root Cause
Redis 재시작 후 대용량 RDB/AOF 로딩 중 요청 처리 불가.

### Action Items
1. (즉시) 로딩 시간 동안 트래픽 우회(리드 레플리카/폴백).
2. (완화) 데이터셋 축소(키 정리), persistence 전략 재검토.
3. (재발방지) 롤링 재시작/프리워밍 + 용량 계획.

---

## 54. Redis MISCONF AOF Write Error
---
service: cache-common
error_message: MISCONF Redis is configured to save RDB snapshots, but is currently not able to persist on disk
---
### Incident Summary
[ERROR] 2024-03-15T11:53:00.000Z cache-common/v6.2 [rd-054]: MISCONF persist error | Context: {Disk="full or read-only", AOF="enabled", Writes="blocked"}

### Root Cause
디스크 full/권한 문제로 AOF/RDB 쓰기 실패 → 보호 설정으로 쓰기 차단 가능.

### Action Items
1. (즉시) 디스크 사용량/권한 확인 및 복구(확장/정리).
2. (완화) persistence 정책(appendonly/no-appendfsync-on-rewrite) 점검.
3. (재발방지) 디스크 알람 + persistence 운영 가이드.

---

## 55. Redis Big Key Detected
---
service: cache-common
error_message: big key detected
---
### Incident Summary
[WARN] 2024-03-15T11:54:00.000Z cache-common/v6.2 [rd-055]: big key detected | Context: {Key="session:bulk", Type="hash", Size="180MB", Impact="latency"}

### Root Cause
단일 키가 과도하게 커서 메모리/지연/복제 부하를 유발.

### Action Items
1. (즉시) 키 분할(샤딩) 또는 구조 변경(리스트/페이지).
2. (완화) big key 삭제는 점진적으로(UNLINK) 진행.
3. (재발방지) 키 사이즈 제한/검증 + bigkey 알람.

---

## 56. Redis KEYS Command Detected
---
service: cache-common
error_message: dangerous command KEYS detected
---
### Incident Summary
[WARN] 2024-03-15T11:55:00.000Z cache-common/v6.2 [rd-056]: dangerous command KEYS detected | Context: {Client="admin-tool", Pattern="*", CPU="95%"}

### Root Cause
KEYS는 O(N)으로 전체 스캔하여 Redis를 멈추게 할 수 있음.

### Action Items
1. (즉시) KEYS 사용 중단, SCAN으로 대체.
2. (재발방지) ACL로 KEYS 금지 + 운영 도구 가이드.

---

## 57. Redis Pipeline Overload
---
service: cache-common
error_message: pipeline backlog high
---
### Incident Summary
[WARN] 2024-03-15T11:56:00.000Z cache-common/v6.2 [rd-057]: pipeline backlog high | Context: {Client="payment-api", PendingCommands="120k", Latency="increasing"}

### Root Cause
클라이언트가 과도한 파이프라인을 보내 Redis 처리 지연/네트워크 버퍼 포화.

### Action Items
1. (즉시) 파이프라인 배치 크기 제한 및 backpressure 적용.
2. (재발방지) QPS 제한 + 배치 크기 표준화.

---

## 58. Redis PubSub Fanout Spike
---
service: cache-common
error_message: pubsub fanout spike
---
### Incident Summary
[WARN] 2024-03-15T11:57:00.000Z cache-common/v6.2 [rd-058]: pubsub fanout spike | Context: {Channels="1000", Subscribers="50k", CPU="92%"}

### Root Cause
과도한 Pub/Sub fanout으로 CPU/네트워크 포화.

### Action Items
1. (즉시) 구독 범위 축소/샤딩 채널 설계.
2. (재발방지) 스트리밍(Kafka/Kinesis) 전환 검토 + 제한 정책.

---

## 59. Redis Lua Non-Deterministic (Replication Error)
---
service: cache-common
error_message: Write command 'EVAL' was not replicated
---
### Incident Summary
[ERROR] 2024-03-15T11:58:00.000Z cache-common/v6.2 [rd-059]: EVAL replication issue | Context: {Script="uses TIME/RAND", Replica="inconsistent"}

### Root Cause
비결정적 Lua 스크립트(시간/랜덤)로 복제 일관성이 깨질 수 있음.

### Action Items
1. (즉시) 스크립트를 결정적 방식으로 수정(입력으로 시간 전달).
2. (재발방지) Lua 스크립트 리뷰/테스트 + 제한 정책.

---

## 60. Redis Timeout (Client Side)
---
service: cache-common
error_message: i/o timeout
---
### Incident Summary
[ERROR] 2024-03-15T11:59:00.000Z cache-common/v6.2 [rd-060]: i/o timeout | Context: {Client="order-api", Timeout="50ms", P99="120ms"}

### Root Cause
Redis 지연 증가 또는 클라 타임아웃이 과도하게 짧음.

### Action Items
1. (즉시) Redis P99 지연 원인(빅키/IO/CPU) 확인.
2. (완화) 타임아웃/재시도 정책 재조정(백오프 필수).
3. (재발방지) SLO 기반 타임아웃 표준 + 지연 알람.

---

## 61. Postgres Connection Reset by Peer
---
service: order-service
error_message: server closed the connection unexpectedly
---
### Incident Summary
[ERROR] 2024-03-15T12:00:00.000Z order-service/v3.2.1 [pg-061]: server closed the connection unexpectedly | Context: {DB="orders", During="query", RDS="failover?"}

### Root Cause
DB failover/재시작 또는 네트워크 문제로 커넥션이 끊김.

### Action Items
1. (즉시) RDS 이벤트/Failover 여부 확인.
2. (완화) 드라이버 재연결 및 재시도(backoff) 적용.
3. (재발방지) 커넥션 keepalive/Failover 대응 설정 검증.

---

## 62. Postgres DNS Resolve Failure (DB Endpoint)
---
service: wallet-service
error_message: could not translate host name "wallet-db" to address
---
### Incident Summary
[ERROR] 2024-03-15T12:01:00.000Z wallet-service/v2.8.0 [pg-062]: could not translate host name to address | Context: {Host="wallet-db", Resolver="CoreDNS", Timeout="2s"}

### Root Cause
클러스터 DNS 문제 또는 엔드포인트 변경/오타.

### Action Items
1. (즉시) DNS 상태(CoreDNS) 및 엔드포인트 확인.
2. (재발방지) DB 엔드포인트 변경 시 배포 파이프라인 검증.

---

## 63. Postgres FATAL: role does not exist
---
service: payment-api
error_message: FATAL: role "payment_user" does not exist
---
### Incident Summary
[ERROR] 2024-03-15T12:02:00.000Z payment-api/v5.1.2 [pg-063]: FATAL: role does not exist | Context: {User="payment_user", Secret="rotated", Env="prod"}

### Root Cause
자격증명 로테이션/환경 변수 설정 오류로 존재하지 않는 유저로 접속.

### Action Items
1. (즉시) Secret/Env 값 확인, 올바른 계정으로 수정.
2. (재발방지) 로테이션 시 검증(로그인 테스트) 자동화.

---

## 64. Postgres FATAL: password authentication failed
---
service: payment-api
error_message: password authentication failed for user
---
### Incident Summary
[ERROR] 2024-03-15T12:03:00.000Z payment-api/v5.1.2 [pg-064]: password authentication failed for user | Context: {User="payment_user", SourceIP="10.0.3.9", Attempts="300/min"}

### Root Cause
패스워드 변경 후 앱 미반영 또는 잘못된 Secret 참조.

### Action Items
1. (즉시) Secrets Manager/쿠버네티스 secret 최신값 확인 및 재배포.
2. (완화) 로그인 실패 폭주 시 백오프/레이트리밋.
3. (재발방지) 시크릿 변경 자동 배포 + 적용 검증.

---

## 65. Postgres Permission Denied for Relation
---
service: analytics-api
error_message: permission denied for relation
---
### Incident Summary
[ERROR] 2024-03-15T12:04:00.000Z analytics-api/v2.4.3 [pg-065]: permission denied for relation "ledger_entries" | Context: {Role="analytics_ro", Operation="SELECT", Schema="finance"}

### Root Cause
권한 부여 누락 또는 스키마 변경 후 권한 상속 깨짐.

### Action Items
1. (즉시) 필요한 권한(GRANT) 확인 및 최소권한으로 부여.
2. (재발방지) 마이그레이션 시 권한/롤 검증 포함.

---

## 66. Postgres Relation Does Not Exist
---
service: settlement-worker
error_message: relation "settlement_jobs" does not exist
---
### Incident Summary
[ERROR] 2024-03-15T12:05:00.000Z settlement-worker/v1.9.0 [pg-066]: relation does not exist | Context: {Migration="pending", Deploy="new version"}

### Root Cause
마이그레이션 미적용 상태에서 신규 코드가 테이블을 참조.

### Action Items
1. (즉시) 마이그레이션 적용 여부 확인 후 실행/롤백.
2. (재발방지) 배포 파이프라인에 migrate step + 호환성(Backward compatible) 전략.

---

## 67. Postgres Duplicate Column During Migration
---
service: migration
error_message: column "status" of relation "orders" already exists
---
### Incident Summary
[ERROR] 2024-03-15T12:06:00.000Z migration/v1.0.0 [pg-067]: column already exists | Context: {MigrationId="20240315_add_status", Env="prod"}

### Root Cause
마이그레이션이 중복 실행되었거나 상태 관리가 꼬임.

### Action Items
1. (즉시) migration history 테이블 확인, idempotent 처리(IF NOT EXISTS) 적용.
2. (재발방지) 마이그레이션 락/단일 실행 보장 + 검증.

---

## 68. Postgres Dead Tuples Causing Table Bloat
---
service: rds-postgresql
error_message: table bloat high
---
### Incident Summary
[WARN] 2024-03-15T12:07:00.000Z rds-postgresql/15 [pg-068]: table bloat high | Context: {Table="ledger_entries", Bloat="45%", DeadTuples="9M"}

### Root Cause
업데이트/삭제 패턴으로 bloat 증가, vacuum 부족.

### Action Items
1. (즉시) vacuum/analyze 수행(운영 절차), autovacuum 튜닝.
2. (재발방지) 파티셔닝/아카이빙, 업데이트 패턴 개선.

---

## 69. Postgres Index Bloat / Reindex Needed
---
service: rds-postgresql
error_message: index bloat high
---
### Incident Summary
[WARN] 2024-03-15T12:08:00.000Z rds-postgresql/15 [pg-069]: index bloat high | Context: {Index="orders_created_at_idx", Bloat="55%", Queries="slow"}

### Root Cause
인덱스가 비대해져 캐시 효율/성능 저하.

### Action Items
1. (즉시) REINDEX CONCURRENTLY 검토(가능 시) 또는 신규 인덱스 생성 후 교체.
2. (재발방지) 정기 점검/관리 작업.

---

## 70. Postgres High Commit Latency
---
service: rds-postgresql
error_message: commit latency high
---
### Incident Summary
[WARN] 2024-03-15T12:09:00.000Z rds-postgresql/15 [pg-070]: commit latency high | Context: {CommitP95="120ms", Baseline="5ms", WALSync="slow"}

### Root Cause
WAL fsync 지연(스토리지/IOPS/네트워크), 체크포인트/쓰기 폭증.

### Action Items
1. (즉시) IOPS/스토리지 지표 확인, 배치 쓰기 분산.
2. (재발방지) 스토리지 성능/파라미터 튜닝, 쓰기 패턴 개선.

---

## 71. Postgres Query Plan Regression (After Deploy)
---
service: order-service
error_message: query plan changed unexpectedly
---
### Incident Summary
[WARN] 2024-03-15T12:10:00.000Z order-service/v3.2.1 [pg-071]: plan regression suspected | Context: {Query="SELECT ...", Old="Index Scan", New="Seq Scan", After="ANALYZE missing"}

### Root Cause
통계 갱신/파라미터 변화로 플랜이 악화.

### Action Items
1. (즉시) ANALYZE 실행 또는 통계 타겟 조정.
2. (완화) 인덱스/쿼리 힌트(가능한 경우) 또는 쿼리 재작성.
3. (재발방지) 배포 후 성능 회귀 감시.

---

## 72. Postgres Too Many Open Files (DB Side)
---
service: rds-postgresql
error_message: too many open files
---
### Incident Summary
[CRITICAL] 2024-03-15T12:11:00.000Z rds-postgresql/15 [pg-072]: too many open files | Context: {Connections="high", TempFiles="many", OS="limit"}

### Root Cause
커넥션 과다/임시파일 폭주로 파일 핸들 고갈.

### Action Items
1. (즉시) 커넥션 감산(풀 제한) 및 temp file 유발 쿼리 차단.
2. (재발방지) pgbouncer + 쿼리 최적화 + 지표 알람.

---

## 73. Redis Memory Fragmentation High
---
service: cache-common
error_message: memory fragmentation ratio high
---
### Incident Summary
[WARN] 2024-03-15T12:12:00.000Z cache-common/v6.2 [rd-073]: memory fragmentation high | Context: {FragRatio="2.1", Used="10Gi", RSS="21Gi"}

### Root Cause
메모리 파편화로 RSS가 비대해져 OOM 위험.

### Action Items
1. (즉시) 큰 키/빈번한 realloc 패턴 제거.
2. (완화) safe restart/rehash 전략(주의) 검토.
3. (재발방지) 키 구조 개선 + 메모리 지표 알람.

---

## 74. Redis Fork Failure (RDB Save)
---
service: cache-common
error_message: Can't save in background: fork: Cannot allocate memory
---
### Incident Summary
[ERROR] 2024-03-15T12:13:00.000Z cache-common/v6.2 [rd-074]: fork failed | Context: {RDB="bgsave", MemFree="low", CopyOnWrite="heavy"}

### Root Cause
RDB 저장 시 fork가 메모리를 추가로 필요로 하여 실패.

### Action Items
1. (즉시) 메모리 여유 확보(키 정리/스케일업).
2. (완화) persistence 전략(AOF only 등) 재검토.
3. (재발방지) 스냅샷 정책/메모리 계획.

---

## 75. Redis Snapshot Corruption Suspected
---
service: cache-common
error_message: Short read or OOM loading DB
---
### Incident Summary
[CRITICAL] 2024-03-15T12:14:00.000Z cache-common/v6.2 [rd-075]: snapshot corruption suspected | Context: {RDB="dump.rdb", Load="failed", RestartLoop="true"}

### Root Cause
RDB 파일 손상 또는 저장 실패로 복구 불가.

### Action Items
1. (즉시) 백업/레플리카로 복구, 손상 파일 격리.
2. (재발방지) 백업/복구 절차 점검 + 스냅샷 검증.

---

## 76. Redis Client Name Flood (Connection Storm)
---
service: cache-common
error_message: connection storm detected
---
### Incident Summary
[WARN] 2024-03-15T12:15:00.000Z cache-common/v6.2 [rd-076]: connection storm detected | Context: {NewConns="50k/min", Client="api-gateway", Reason="pod restart"}

### Root Cause
앱 재시작/스케일링 시 커넥션이 급증해 Redis 과부하.

### Action Items
1. (즉시) 클라 풀/keepalive 사용, reconnect backoff 강화.
2. (재발방지) 롤링 배포/스케일링 완화 + 커넥션 상한.

---

## 77. Redis Read Timeout (Proxy Layer)
---
service: cache-proxy
error_message: upstream redis read timeout
---
### Incident Summary
[ERROR] 2024-03-15T12:16:00.000Z cache-proxy/v1.3.0 [rd-077]: upstream redis read timeout | Context: {Proxy="twemproxy", Timeout="20ms", BackendP99="60ms"}

### Root Cause
프록시 타임아웃이 과도하게 짧거나 백엔드 지연 증가.

### Action Items
1. (즉시) 백엔드 지연 원인 해결(빅키/IO/CPU).
2. (완화) 프록시 타임아웃/리트라이 조정.
3. (재발방지) 프록시/백엔드 SLO 정렬.

---

## 78. MySQL Replica Lag High
---
service: reporting-api
error_message: replica lag too high
---
### Incident Summary
[WARN] 2024-03-15T12:17:00.000Z reporting-api/v1.1.0 [my-078]: replica lag too high | Context: {Lag="25s", Threshold="3s", Writes="batch"}

### Root Cause
배치 쓰기/IO 병목으로 리플리카 적용 지연.

### Action Items
1. (즉시) 배치 분산, 읽기 라우팅 조정.
2. (재발방지) 리플리카 성능/설정 튜닝 + 알람.

---

## 79. MySQL Deadlock Detected
---
service: merchant-service
error_message: Deadlock found when trying to get lock
---
### Incident Summary
[ERROR] 2024-03-15T12:18:00.000Z merchant-service/v1.7.2 [my-079]: Deadlock found when trying to get lock | Context: {Table="merchant_payout", Tx="update", Concurrency="high"}

### Root Cause
락 순서 불일치/인덱스 미스 등으로 데드락.

### Action Items
1. (즉시) 데드락 로그에서 테이블/쿼리 확인.
2. (완화) 락 순서 고정 + retry(backoff).
3. (재발방지) 인덱스/쿼리 최적화, 트랜잭션 축소.

---

## 80. MySQL Too Many Connections
---
service: merchant-service
error_message: Too many connections
---
### Incident Summary
[CRITICAL] 2024-03-15T12:19:00.000Z merchant-service/v1.7.2 [my-080]: Too many connections | Context: {MaxConn="500", Active="500", Pool="misconfigured", Retries="storm"}

### Root Cause
풀 미사용/풀 과대/재시도 폭주로 커넥션 고갈.

### Action Items
1. (즉시) 풀 적용/풀 크기 감산, 재시도 백오프.
2. (재발방지) pgbouncer(또는 mysql proxy) + 커넥션 알람.

---

## 81. DynamoDB AccessDenied
---
service: fraud-service
error_message: AccessDeniedException
---
### Incident Summary
[ERROR] 2024-03-15T12:20:00.000Z fraud-service/v4.0.0 [dy-081]: AccessDeniedException | Context: {Table="fraud_signals", Role="fraud-role", Action="UpdateItem"}

### Root Cause
IAM 정책 변경/IRSA 설정 오류로 접근 거부.

### Action Items
1. (즉시) 역할/정책 변경 이력 확인 후 복구.
2. (재발방지) IAM 변경 승인/검증 절차 + 최소권한 템플릿.

---

## 82. DynamoDB Request Timeout
---
service: fraud-service
error_message: RequestTimeout
---
### Incident Summary
[WARN] 2024-03-15T12:21:00.000Z fraud-service/v4.0.0 [dy-082]: RequestTimeout | Context: {Region="ap-northeast-2", LatencyP99="1.2s", Retries="high"}

### Root Cause
네트워크/리전 이슈 또는 재시도 폭주로 지연 증가.

### Action Items
1. (즉시) AWS 상태/네트워크 확인, 재시도 백오프 강화.
2. (재발방지) 타임아웃/재시도 표준화 + 멀티리전 대비.

---

## 83. DynamoDB ValidationException (Key Schema)
---
service: fraud-service
error_message: ValidationException: The provided key element does not match the schema
---
### Incident Summary
[ERROR] 2024-03-15T12:22:00.000Z fraud-service/v4.0.0 [dy-083]: key schema mismatch | Context: {PK="merchant_id", Provided="merchantId", Deploy="new version"}

### Root Cause
코드/모델 변경으로 키 이름/타입이 스키마와 불일치.

### Action Items
1. (즉시) 테이블 키 스키마와 코드 매핑 확인 후 수정.
2. (재발방지) 스키마 계약 테스트 + 배포 게이트.

---

## 84. DynamoDB Item Size Exceeded
---
service: fraud-service
error_message: ValidationException: Item size has exceeded the maximum allowed size
---
### Incident Summary
[ERROR] 2024-03-15T12:23:00.000Z fraud-service/v4.0.0 [dy-084]: item too large | Context: {Size="520KB", Limit="400KB", Field="raw_payload"}

### Root Cause
원본 페이로드를 그대로 저장해 아이템 크기 제한 초과.

### Action Items
1. (즉시) 원본은 S3로 분리 저장, DynamoDB에는 포인터만 저장.
2. (재발방지) 데이터 모델 검증(사이즈 체크) + 압축/요약.

---

## 85. DynamoDB GSI Backfilling Slow
---
service: fraud-service
error_message: GSI backfilling slow
---
### Incident Summary
[WARN] 2024-03-15T12:24:00.000Z fraud-service/v4.0.0 [dy-085]: GSI backfilling slow | Context: {Index="by_status", Backfill="in progress", Latency="up"}

### Root Cause
GSI 생성/백필 중 테이블에 추가 부하. 읽기/쓰기 지연 증가.

### Action Items
1. (즉시) 백필 기간 동안 트래픽 감산 또는 오프피크 수행.
2. (재발방지) 인덱스 변경은 계획/점진 수행 + 알람.

---

## 86. Postgres Parameter Group Drift
---
service: rds-postgresql
error_message: parameter drift detected
---
### Incident Summary
[WARN] 2024-03-15T12:25:00.000Z rds-postgresql/15 [pg-086]: parameter drift detected | Context: {Param="work_mem", Expected="4Mi", Actual="64Mi", Change="manual"}

### Root Cause
수동 변경으로 파라미터 드리프트 → 성능/안정성 예측 불가.

### Action Items
1. (즉시) 변경 이력 확인, 표준 값으로 복구(검증 후).
2. (재발방지) IaC로 파라미터 관리 + 변경 승인 절차.

---

## 87. Postgres Max WAL Senders Reached
---
service: rds-postgresql
error_message: number of requested standby connections exceeds max_wal_senders
---
### Incident Summary
[ERROR] 2024-03-15T12:26:00.000Z rds-postgresql/15 [pg-087]: max_wal_senders reached | Context: {Standbys="5", Limit="5", NewReplica="adding"}

### Root Cause
리플리카/논리복제 연결이 max_wal_senders 한도 초과.

### Action Items
1. (즉시) 불필요한 복제 연결 정리 또는 파라미터 상향.
2. (재발방지) 복제 토폴로지/한도 계획.

---

## 88. Postgres Logical Replication Subscription Disabled
---
service: rds-postgresql
error_message: subscription disabled
---
### Incident Summary
[WARN] 2024-03-15T12:27:00.000Z rds-postgresql/15 [pg-088]: subscription disabled | Context: {Subscription="cdc_orders", Reason="apply error", Lag="growing"}

### Root Cause
apply 에러로 구독이 비활성화되며 CDC 지연.

### Action Items
1. (즉시) apply 에러 원인(스키마 불일치 등) 해결 후 재활성화.
2. (재발방지) 스키마 변경 시 CDC 호환성 절차.

---

## 89. Redis Key TTL Misconfigured (Never Expires)
---
service: cache-common
error_message: ttl misconfigured - no expiry
---
### Incident Summary
[WARN] 2024-03-15T12:28:00.000Z cache-common/v6.2 [rd-089]: ttl misconfigured | Context: {KeyPattern="session:*", TTL="=-1", Growth="fast"}

### Root Cause
세션/캐시 키에 TTL이 누락되어 메모리 누수처럼 증가.

### Action Items
1. (즉시) TTL 누락 키 식별 및 TTL 부여/정리.
2. (재발방지) 캐시 API wrapper로 TTL 강제.

---

## 90. Redis TTL Too Short (Churn)
---
service: cache-common
error_message: ttl too short causing churn
---
### Incident Summary
[WARN] 2024-03-15T12:29:00.000Z cache-common/v6.2 [rd-090]: ttl churn | Context: {TTL="5s", MissRate="80%", DBLoad="high"}

### Root Cause
TTL이 너무 짧아 캐시 재생성이 과도 → DB 부하 증가.

### Action Items
1. (즉시) TTL 재조정 + jitter 추가.
2. (재발방지) TTL 정책(데이터별) 표준화.

---

## 91. Redis Cluster Too Few Masters
---
service: cache-common
error_message: ERR not enough masters
---
### Incident Summary
[CRITICAL] 2024-03-15T12:30:00.000Z cache-common/v6.2 [rd-091]: not enough masters | Context: {MastersUp="2", Required="3", Slots="partial"}

### Root Cause
마스터 노드 다수 다운으로 클러스터가 정상 운영 불가.

### Action Items
1. (즉시) 다운 노드 복구/교체, 네트워크 확인.
2. (재발방지) 자동 복구/노드 헬스체크 + 용량/내구성 강화.

---

## 92. Redis Read Amplification (Large Range Queries)
---
service: cache-common
error_message: heavy range query detected
---
### Incident Summary
[WARN] 2024-03-15T12:31:00.000Z cache-common/v6.2 [rd-092]: heavy range query detected | Context: {Cmd="ZRANGE 0 -1", Members="5M", Latency="200ms"}

### Root Cause
대량 range 조회로 CPU/네트워크 폭증.

### Action Items
1. (즉시) 페이지네이션/커서 기반 조회로 변경.
2. (재발방지) 대량 조회 금지 정책 + 데이터 모델 개선.

---

## 93. Postgres Archive Command Failed
---
service: rds-postgresql
error_message: archive command failed
---
### Incident Summary
[ERROR] 2024-03-15T12:32:00.000Z rds-postgresql/15 [pg-093]: archive command failed | Context: {Archive="S3", Error="AccessDenied", WAL="000000..."}

### Root Cause
WAL 아카이브(S3) 권한/네트워크 문제로 실패 → 복구 지점 위험.

### Action Items
1. (즉시) IAM/네트워크 확인 후 복구.
2. (재발방지) 아카이브 성공률 모니터링 + 알람.

---

## 94. Postgres Backup Failed
---
service: backup
error_message: snapshot/backup failed
---
### Incident Summary
[CRITICAL] 2024-03-15T12:33:00.000Z backup/v1.0.0 [pg-094]: backup failed | Context: {DB="payments", Reason="timeout", Window="peak"}

### Root Cause
피크 시간대 백업으로 I/O/락 영향 또는 네트워크/권한 문제.

### Action Items
1. (즉시) 백업 재시도(오프피크) 및 영향 평가.
2. (재발방지) 백업 윈도우 재조정 + 백업 성공률 알람.

---

## 95. Postgres Restore Validation Failed
---
service: dr-test
error_message: restore validation failed
---
### Incident Summary
[ERROR] 2024-03-15T12:34:00.000Z dr-test/v1.0.0 [pg-095]: restore validation failed | Context: {Test="weekly", Missing="extension/role", RTO="risk"}

### Root Cause
복구 테스트 시 역할/확장/시크릿 등 부수 구성 누락.

### Action Items
1. (즉시) 복구 체크리스트 보완(roles, extensions, secrets).
2. (재발방지) 정기 DR 리허설 + 자동 검증 스크립트.

---

## 96. Data Consistency Drift (Cache vs DB)
---
service: order-service
error_message: cache-db inconsistency detected
---
### Incident Summary
[WARN] 2024-03-15T12:35:00.000Z order-service/v3.2.1 [mix-096]: cache-db inconsistency detected | Context: {Key="order:o-7712", Cache="PAID", DB="PENDING", TTL="stale"}

### Root Cause
캐시 갱신 순서/이벤트 유실로 캐시가 stale.

### Action Items
1. (즉시) 캐시 무효화/리빌드(해당 키) 및 읽기 시 DB 우선 정책 적용(임시).
2. (재발방지) write-through/write-behind 정책 정리 + 이벤트 신뢰성 강화.

---

## 97. Outbox Table Growing (CDC Delay)
---
service: settlement-worker
error_message: outbox backlog growing
---
### Incident Summary
[WARN] 2024-03-15T12:36:00.000Z settlement-worker/v1.9.0 [mix-097]: outbox backlog growing | Context: {Outbox="ledger_outbox", Backlog="2.3M", Consumer="slow"}

### Root Cause
CDC/이벤트 컨슈머 지연으로 outbox가 적체 → 스토리지/지연 증가.

### Action Items
1. (즉시) 컨슈머 스케일아웃/복구, 처리량 병목 제거.
2. (재발방지) outbox 파티셔닝/보존 정책 + 컨슈머 SLO 알람.

---

## 98. Duplicate Event Insert (Exactly-Once Failure)
---
service: settlement-worker
error_message: duplicate key value violates unique constraint "outbox_event_id_key"
---
### Incident Summary
[WARN] 2024-03-15T12:37:00.000Z settlement-worker/v1.9.0 [mix-098]: duplicate outbox event | Context: {EventId="evt-9912", Retries="worker restart", Dedup="working"}

### Root Cause
워커 재시작/재처리로 이벤트가 중복 생성되었으나 유니크 제약으로 차단(정상 dedup).

### Action Items
1. (즉시) 중복은 성공으로 처리하고 동일 결과 반환(멱등).
2. (재발방지) 이벤트 생성/처리 멱등성 표준화.

---

## 99. DB Failover + Cache Failover (Cascading)
---
service: payment-api
error_message: cascading failover detected
---
### Incident Summary
[CRITICAL] 2024-03-15T12:38:00.000Z payment-api/v5.1.2 [mix-099]: cascading failover detected | Context: {DB="failover", Redis="failover", Errors="timeouts", Retries="storm"}

### Root Cause
DB/캐시 동시 장애로 재시도 폭주 → 스레드 고갈/장애 증폭(캐스케이드).

### Action Items
1. (즉시) 재시도 억제(서킷브레이커), 타임아웃 축소/백오프 강화.
2. (즉시) 핵심 기능 우선 순위로 degrade(필수 결제/조회만).
3. (재발방지) 장애 시나리오 기반 로드 테스트 + fallback 설계.

---

## 100. Critical Data Layer Incident – DB Unreachable
---
service: rds-postgresql
error_message: could not connect to server: Connection timed out
---
### Incident Summary
[CRITICAL] 2024-03-15T12:39:00.000Z rds-postgresql/15 [pg-100]: could not connect to server: Connection timed out | Context: {Endpoint="payments-db", AZ="multi", Network="suspected", AppErrors="spike"}

### Root Cause
DB 네트워크 단절/보안그룹/서브넷/NAT 문제 또는 DB 다운/장애로 연결 불가.

### Action Items
1. (즉시) 네트워크 경로(SG/NACL/라우팅)와 RDS 상태 이벤트를 동시에 확인해 원인 분리.
2. (즉시) 앱 측 타임아웃/재시도 억제, 큐잉(결제/정산)으로 유실 방지.
3. (완화) 리드/라이트 분리(가능 시), 대체 경로(리플리카/DR) 전환.
4. (재발방지) 네트워크 변경 관리 + DB SLO 알람 + DR 리허설.

---
