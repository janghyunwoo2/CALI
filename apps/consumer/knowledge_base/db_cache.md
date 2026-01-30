# CALI Knowledge Base – Fintech Database & Cache (01–50)

---

## 01. PostgreSQL Transaction Deadlock
---
service: order-db
error_message: deadlock detected
---
### Incident Summary
동시 트랜잭션 처리 중 교착 상태 발생.
### Root Cause
동일 레코드에 대한 업데이트 순서 불일치.
### Action Items
1. 트랜잭션 내 업데이트 순서 통일.
2. 애플리케이션 레벨 재시도 로직 추가.

---

## 02. PostgreSQL Connection Pool Exhausted
---
service: common-db
error_message: remaining connection slots are reserved
---
### Incident Summary
DB 커넥션 풀 고갈로 신규 요청 실패.
### Root Cause
커넥션 반환 누락.
### Action Items
1. 커넥션 풀 크기 조정.
2. 커넥션 close 로직 점검.

---

## 03. Slow Query Spike
---
service: settlement-db
error_message: query execution time exceeded
---
### Incident Summary
특정 쿼리 지연으로 전체 응답 속도 저하.
### Root Cause
인덱스 미적용.
### Action Items
1. 실행 계획 분석.
2. 인덱스 추가.

---

## 04. Read Replica Lag
---
service: reporting-db
error_message: replication delay detected
---
### Incident Summary
읽기 복제본 지연으로 데이터 불일치 발생.
### Root Cause
대량 쓰기 트래픽 유입.
### Action Items
1. 쓰기 배치 처리.
2. Replica 스펙 상향.

---

## 05. PostgreSQL Autovacuum Lag
---
service: order-db
error_message: autovacuum not keeping up
---
### Incident Summary
테이블 팽창으로 성능 저하.
### Root Cause
Autovacuum 튜닝 미흡.
### Action Items
1. Autovacuum 파라미터 조정.
2. 수동 Vacuum 실행.

---

## 06. DB Disk Space Full
---
service: common-db
error_message: no space left on device
---
### Incident Summary
DB 디스크 용량 초과.
### Root Cause
로그 및 테이블 비대화.
### Action Items
1. 오래된 데이터 정리.
2. 스토리지 증설.

---

## 07. Long Running Transaction
---
service: order-db
error_message: transaction duration exceeded
---
### Incident Summary
장기 트랜잭션으로 락 유지.
### Root Cause
외부 API 호출 포함된 트랜잭션.
### Action Items
1. 트랜잭션 범위 축소.
2. 비동기 처리 전환.

---

## 08. PostgreSQL Checkpoint Spike
---
service: settlement-db
error_message: checkpoint duration high
---
### Incident Summary
Checkpoint 지연으로 I/O 급증.
### Root Cause
Checkpoint 설정 과도.
### Action Items
1. checkpoint_timeout 조정.
2. IOPS 상향.

---

## 09. Table Lock Contention
---
service: inventory-db
error_message: relation lock contention
---
### Incident Summary
테이블 락 경합으로 처리 지연.
### Root Cause
DDL 작업과 DML 동시 수행.
### Action Items
1. DDL 오프피크 수행.
2. 락 모니터링 강화.

---

## 10. PostgreSQL WAL Disk Full
---
service: common-db
error_message: could not write to WAL
---
### Incident Summary
WAL 디스크 부족으로 쓰기 실패.
### Root Cause
백업 실패로 WAL 누적.
### Action Items
1. 백업 파이프라인 점검.
2. WAL 보관 정책 수정.

---

## 11. Redis Max Memory Reached
---
service: cache-common
error_message: OOM command not allowed
---
### Incident Summary
Redis 메모리 한도 초과.
### Root Cause
TTL 미설정 키 누적.
### Action Items
1. Eviction Policy 설정.
2. TTL 정책 강제.

---

## 12. Redis Eviction Storm
---
service: cache-common
error_message: evicted keys spike
---
### Incident Summary
대량 키 삭제로 캐시 효율 급락.
### Root Cause
메모리 부족 상태 지속.
### Action Items
1. 메모리 증설.
2. 캐시 키 크기 점검.

---

## 13. Redis Hot Key Issue
---
service: cache-session
error_message: high latency on GET
---
### Incident Summary
특정 키 접근 집중으로 지연 발생.
### Root Cause
세션 키 단일화.
### Action Items
1. 키 분산 설계.
2. 샤딩 적용.

---

## 14. Redis Replication Lag
---
service: cache-common
error_message: replication delay
---
### Incident Summary
Replica 지연으로 데이터 불일치.
### Root Cause
쓰기 트래픽 급증.
### Action Items
1. Replica 증설.
2. 쓰기 분산.

---

## 15. Redis Snapshot Save Failed
---
service: cache-common
error_message: RDB save failed
---
### Incident Summary
스냅샷 저장 실패.
### Root Cause
디스크 공간 부족.
### Action Items
1. 디스크 확보.
2. 백업 주기 조정.

---

## 16. Cache Penetration Detected
---
service: cache-common
error_message: cache miss spike
---
### Incident Summary
캐시 미스 증가로 DB 부하 증가.
### Root Cause
존재하지 않는 키 반복 조회.
### Action Items
1. Null 캐시 적용.
2. 요청 검증 강화.

---

## 17. Cache Avalanche
---
service: cache-common
error_message: mass cache expiration
---
### Incident Summary
동시 만료로 캐시 무력화.
### Root Cause
TTL 동일 설정.
### Action Items
1. TTL 랜덤화.
2. 만료 분산 전략 적용.

---

## 18. Cache Invalidation Delay
---
service: cache-common
error_message: stale cache detected
---
### Incident Summary
캐시 무효화 지연으로 오래된 데이터 제공.
### Root Cause
이벤트 기반 무효화 실패.
### Action Items
1. 이벤트 파이프라인 점검.
2. TTL 단축.

---

## 19. PostgreSQL Index Bloat
---
service: order-db
error_message: index size increased
---
### Incident Summary
인덱스 비대화로 성능 저하.
### Root Cause
잦은 업데이트.
### Action Items
1. REINDEX 수행.
2. 인덱스 구조 재검토.

---

## 20. Connection Leak Detected
---
service: settlement-db
error_message: too many connections
---
### Incident Summary
커넥션 누수로 DB 접근 불가.
### Root Cause
예외 처리 시 close 누락.
### Action Items
1. finally 블록 점검.
2. 커넥션 모니터링 추가.

---

## 21. PostgreSQL Failover Timeout
---
service: common-db
error_message: failover timeout
---
### Incident Summary
Failover 지연으로 서비스 중단.
### Root Cause
헬스체크 감지 지연.
### Action Items
1. 헬스체크 주기 조정.
2. Failover 테스트 정기 수행.

---

## 22. Replica Read After Write Inconsistency
---
service: reporting-db
error_message: stale read detected
---
### Incident Summary
쓰기 직후 읽기 시 데이터 불일치.
### Root Cause
Replica 지연.
### Action Items
1. Strong Consistency 경로 제공.
2. Read 전략 분리.

---

## 23. PostgreSQL Sequence Exhausted
---
service: order-db
error_message: nextval overflow
---
### Incident Summary
시퀀스 최대값 도달.
### Root Cause
시퀀스 증가 폭 과소.
### Action Items
1. 시퀀스 재설정.
2. bigint 전환.

---

## 24. Redis Connection Timeout
---
service: cache-common
error_message: connection timeout
---
### Incident Summary
Redis 연결 실패.
### Root Cause
네트워크 지연 또는 서버 부하.
### Action Items
1. 타임아웃 조정.
2. 커넥션 풀 점검.

---

## 25. DB CPU Saturation
---
service: settlement-db
error_message: cpu utilization high
---
### Incident Summary
DB CPU 포화로 응답 지연.
### Root Cause
비효율 쿼리 다수.
### Action Items
1. 쿼리 튜닝.
2. 리소스 스케일 업.

---

## 26. PostgreSQL Temp File Explosion
---
service: analytics-db
error_message: temporary file size exceeded
---
### Incident Summary
임시 파일 과다 생성.
### Root Cause
정렬/조인 쿼리 과다.
### Action Items
1. work_mem 조정.
2. 쿼리 구조 개선.

---

## 27. Redis Keyspace Fragmentation
---
service: cache-common
error_message: memory fragmentation high
---
### Incident Summary
메모리 단편화로 효율 저하.
### Root Cause
키 크기 다양성.
### Action Items
1. Redis 재시작.
2. 키 구조 단순화.

---

## 28. DB Backup Failed
---
service: common-db
error_message: backup job failed
---
### Incident Summary
정기 백업 실패.
### Root Cause
권한 또는 스토리지 오류.
### Action Items
1. IAM 권한 점검.
2. 백업 로그 분석.

---

## 29. Redis AUTH Failed
---
service: cache-common
error_message: NOAUTH Authentication required
---
### Incident Summary
Redis 인증 실패.
### Root Cause
비밀번호 변경 미반영.
### Action Items
1. Secret 업데이트.
2. 애플리케이션 재시작.

---

## 30. PostgreSQL Extension Missing
---
service: analytics-db
error_message: extension does not exist
---
### Incident Summary
확장 모듈 미설치로 쿼리 실패.
### Root Cause
환경 간 설정 불일치.
### Action Items
1. 확장 설치.
2. 환경 표준화.

---

## 31. DB Lock Timeout
---
service: inventory-db
error_message: lock timeout exceeded
---
### Incident Summary
락 대기로 요청 실패.
### Root Cause
트랜잭션 경합.
### Action Items
1. 트랜잭션 분리.
2. 락 대기 시간 조정.

---

## 32. Redis Pub/Sub Message Loss
---
service: cache-event
error_message: message dropped
---
### Incident Summary
이벤트 메시지 유실.
### Root Cause
Subscriber 부재.
### Action Items
1. Consumer 상태 점검.
2. 스트림 기반 전환 검토.

---

## 33. PostgreSQL Vacuum Freeze Age High
---
service: common-db
error_message: vacuum freeze age exceeded
---
### Incident Summary
트랜잭션 ID 랩어라운드 위험.
### Root Cause
Vacuum 지연.
### Action Items
1. Vacuum 우선 수행.
2. Freeze 설정 조정.

---

## 34. Redis Latency Spike
---
service: cache-common
error_message: latency spike detected
---
### Incident Summary
Redis 응답 지연 급증.
### Root Cause
백그라운드 작업 수행.
### Action Items
1. 백업 시간 분산.
2. 리소스 증설.

---

## 35. DB Parameter Drift
---
service: common-db
error_message: parameter mismatch
---
### Incident Summary
파라미터 불일치로 성능 저하.
### Root Cause
수동 설정 변경.
### Action Items
1. 파라미터 관리 자동화.
2. Drift 감지 도입.

---

## 36. Redis Cluster Slot Imbalance
---
service: cache-common
error_message: slot imbalance
---
### Incident Summary
특정 노드에 슬롯 집중.
### Root Cause
리밸런싱 미수행.
### Action Items
1. 슬롯 재분배.
2. 클러스터 상태 점검.

---

## 37. PostgreSQL WAL Archiving Delay
---
service: common-db
error_message: WAL archive lag
---
### Incident Summary
아카이빙 지연으로 복구 위험 증가.
### Root Cause
아카이브 대상 스토리지 지연.
### Action Items
1. 스토리지 성능 개선.
2. 아카이빙 모니터링 강화.

---

## 38. Redis Key Expiration Drift
---
service: cache-common
error_message: expiration drift detected
---
### Incident Summary
키 만료 시점 불균등.
### Root Cause
대량 만료 스케줄 집중.
### Action Items
1. TTL 분산 설정.
2. 만료 정책 재검토.

---

## 39. DB Schema Migration Failed
---
service: common-db
error_message: migration failed
---
### Incident Summary
스키마 마이그레이션 중단.
### Root Cause
기존 데이터 제약 조건 충돌.
### Action Items
1. 사전 데이터 검증.
2. 롤백 전략 마련.

---

## 40. Redis Client Buffer Overflow
---
service: cache-common
error_message: client buffer limit reached
---
### Incident Summary
클라이언트 버퍼 초과.
### Root Cause
대량 응답 전송.
### Action Items
1. 응답 크기 제한.
2. 버퍼 설정 조정.

---

## 41. PostgreSQL Timezone Mismatch
---
service: settlement-db
error_message: invalid timestamp
---
### Incident Summary
타임존 불일치로 데이터 오류.
### Root Cause
DB/애플리케이션 설정 불일치.
### Action Items
1. 타임존 통일.
2. 설정 표준화.

---

## 42. Redis Lua Script Timeout
---
service: cache-common
error_message: lua script timeout
---
### Incident Summary
Lua 스크립트 실행 지연.
### Root Cause
복잡한 스크립트 로직.
### Action Items
1. 스크립트 단순화.
2. 실행 분리.

---

## 43. DB Network Packet Loss
---
service: common-db
error_message: packet loss detected
---
### Incident Summary
DB 네트워크 불안정.
### Root Cause
네트워크 장애.
### Action Items
1. 네트워크 경로 점검.
2. 재시도 로직 강화.

---

## 44. Redis Replica Promotion Failed
---
service: cache-common
error_message: failover aborted
---
### Incident Summary
Replica 승격 실패.
### Root Cause
상태 불일치.
### Action Items
1. 클러스터 점검.
2. 수동 복구.

---

## 45. PostgreSQL SSL Handshake Failed
---
service: common-db
error_message: SSL handshake failed
---
### Incident Summary
SSL 연결 실패.
### Root Cause
인증서 만료.
### Action Items
1. 인증서 갱신.
2. SSL 설정 점검.

---

## 46. Redis Key Serialization Error
---
service: cache-common
error_message: serialization error
---
### Incident Summary
직렬화 오류로 캐시 실패.
### Root Cause
버전 불일치.
### Action Items
1. 직렬화 포맷 통일.
2. 배포 순서 조정.

---

## 47. DB Query Plan Regression
---
service: analytics-db
error_message: plan regression detected
---
### Incident Summary
쿼리 플랜 변경으로 성능 저하.
### Root Cause
통계 정보 변경.
### Action Items
1. ANALYZE 수행.
2. 힌트 적용 검토.

---

## 48. Redis Failover Split Brain
---
service: cache-common
error_message: split brain detected
---
### Incident Summary
클러스터 분기 발생.
### Root Cause
네트워크 분리.
### Action Items
1. Quorum 설정 강화.
2. 네트워크 안정화.

---

## 49. PostgreSQL Temp Table Bloat
---
service: analytics-db
error_message: temp table bloat
---
### Incident Summary
임시 테이블 비대화.
### Root Cause
정리 작업 누락.
### Action Items
1. 주기적 정리.
2. 쿼리 개선.

---

## 50. Cache Data Inconsistency
---
service: cache-common
error_message: cache data mismatch
---
### Incident Summary
캐시와 DB 데이터 불일치.
### Root Cause
캐시 무효화 누락.
### Action Items
1. 캐시 갱신 로직 점검.
2. 쓰기 후 무효화 보장.

---
## 51. PostgreSQL Idle in Transaction
---
service: order-db
error_message: idle in transaction
---
### Incident Summary
트랜잭션이 열린 채로 장시간 대기.
### Root Cause
트랜잭션 종료 누락.
### Action Items
1. 트랜잭션 범위 축소.
2. idle 트랜잭션 모니터링 추가.

---

## 52. DB Read Only Mode Triggered
---
service: common-db
error_message: cannot execute write in read-only transaction
---
### Incident Summary
DB가 읽기 전용 모드로 전환됨.
### Root Cause
스토리지 장애 감지.
### Action Items
1. 스토리지 상태 점검.
2. Read/Write 전환 정책 확인.

---

## 53. PostgreSQL Lock Queue Overflow
---
service: inventory-db
error_message: lock queue overflow
---
### Incident Summary
락 대기 큐 초과로 요청 실패.
### Root Cause
동시 트랜잭션 폭증.
### Action Items
1. 트랜잭션 분산.
2. 락 전략 재설계.

---

## 54. Redis Slowlog Spike
---
service: cache-common
error_message: slowlog length exceeded
---
### Incident Summary
Redis 명령 처리 지연 증가.
### Root Cause
복잡한 연산 명령 사용.
### Action Items
1. 명령 최적화.
2. 자료구조 단순화.

---

## 55. PostgreSQL Table Scan Explosion
---
service: analytics-db
error_message: seq scan detected
---
### Incident Summary
테이블 풀 스캔 급증.
### Root Cause
조건절 인덱스 미적용.
### Action Items
1. 인덱스 추가.
2. 쿼리 조건 개선.

---

## 56. Redis Cluster Node Timeout
---
service: cache-common
error_message: node timeout
---
### Incident Summary
Redis 노드 응답 지연.
### Root Cause
노드 과부하.
### Action Items
1. 노드 증설.
2. 트래픽 재분배.

---

## 57. PostgreSQL Statistics Outdated
---
service: common-db
error_message: statistics outdated
---
### Incident Summary
부정확한 통계로 실행 계획 저하.
### Root Cause
ANALYZE 미수행.
### Action Items
1. ANALYZE 수행.
2. 자동 통계 설정 확인.

---

## 58. Redis Memory Swap Usage
---
service: cache-common
error_message: swap usage detected
---
### Incident Summary
Redis 메모리 스왑 발생.
### Root Cause
메모리 압박.
### Action Items
1. 메모리 증설.
2. 스왑 비활성화.

---

## 59. PostgreSQL Constraint Violation Spike
---
service: order-db
error_message: constraint violation
---
### Incident Summary
제약 조건 위반 오류 증가.
### Root Cause
중복 데이터 삽입.
### Action Items
1. 입력 검증 강화.
2. 중복 방지 로직 추가.

---

## 60. Redis Script Cache Miss
---
service: cache-common
error_message: NOSCRIPT No matching script
---
### Incident Summary
Lua 스크립트 캐시 미존재.
### Root Cause
노드 재시작.
### Action Items
1. 스크립트 재로드.
2. 초기화 로직 추가.

---

## 61. PostgreSQL Parallel Query Disabled
---
service: analytics-db
error_message: parallel query disabled
---
### Incident Summary
병렬 쿼리 미사용으로 성능 저하.
### Root Cause
설정 제한.
### Action Items
1. max_parallel_workers 조정.
2. 쿼리 구조 개선.

---

## 62. Redis Client Connection Leak
---
service: cache-common
error_message: client connection leak
---
### Incident Summary
Redis 클라이언트 연결 누수.
### Root Cause
연결 종료 누락.
### Action Items
1. 커넥션 관리 점검.
2. 풀링 적용.

---

## 63. PostgreSQL Disk IO Wait High
---
service: settlement-db
error_message: io wait high
---
### Incident Summary
디스크 I/O 대기로 지연 발생.
### Root Cause
동시 쓰기 증가.
### Action Items
1. IOPS 증설.
2. 쓰기 배치화.

---

## 64. Redis Key TTL Drift
---
service: cache-common
error_message: ttl drift
---
### Incident Summary
키 만료 시점 불균형.
### Root Cause
TTL 설정 편차.
### Action Items
1. TTL 랜덤화.
2. 정책 통일.

---

## 65. PostgreSQL Extension Version Mismatch
---
service: analytics-db
error_message: extension version mismatch
---
### Incident Summary
확장 모듈 버전 충돌.
### Root Cause
환경 간 버전 불일치.
### Action Items
1. 버전 통일.
2. 배포 표준화.

---

## 66. Redis Multi-Key Command Blocking
---
service: cache-common
error_message: blocking multi-key command
---
### Incident Summary
대량 키 명령으로 Redis 블로킹.
### Root Cause
KEYS, MGET 과다 사용.
### Action Items
1. SCAN 사용.
2. 명령 사용 제한.

---

## 67. PostgreSQL Prepared Statement Bloat
---
service: common-db
error_message: prepared statement bloat
---
### Incident Summary
Prepared Statement 누적으로 메모리 사용 증가.
### Root Cause
Statement 해제 누락.
### Action Items
1. Statement 정리.
2. 재사용 정책 수정.

---

## 68. Redis Sentinel Failover Delay
---
service: cache-common
error_message: failover delay
---
### Incident Summary
Failover 감지 지연.
### Root Cause
Sentinel 설정 과소.
### Action Items
1. Sentinel 수 증설.
2. 타임아웃 조정.

---

## 69. PostgreSQL Foreign Key Check Overhead
---
service: order-db
error_message: foreign key check slow
---
### Incident Summary
외래키 검사로 쓰기 지연.
### Root Cause
참조 테이블 인덱스 부족.
### Action Items
1. 참조 인덱스 추가.
2. FK 구조 재검토.

---

## 70. Redis Large Key Detected
---
service: cache-common
error_message: large key detected
---
### Incident Summary
대형 키로 메모리 사용 급증.
### Root Cause
리스트/해시 무제한 증가.
### Action Items
1. 키 분할.
2. 최대 크기 제한.

---

## 71. PostgreSQL Archive Cleanup Failed
---
service: common-db
error_message: archive cleanup failed
---
### Incident Summary
아카이브 로그 정리 실패.
### Root Cause
권한 오류.
### Action Items
1. 권한 수정.
2. 정리 스크립트 점검.

---

## 72. Redis AOF Rewrite Block
---
service: cache-common
error_message: aof rewrite blocked
---
### Incident Summary
AOF 재작성 중 성능 저하.
### Root Cause
디스크 I/O 병목.
### Action Items
1. I/O 성능 개선.
2. Rewrite 스케줄 조정.

---

## 73. PostgreSQL Temp Index Spill
---
service: analytics-db
error_message: temp index spill
---
### Incident Summary
인덱스 생성 중 디스크 스필 발생.
### Root Cause
work_mem 부족.
### Action Items
1. work_mem 상향.
2. 배치 작업 분리.

---

## 74. Redis Authentication Latency
---
service: cache-common
error_message: auth latency high
---
### Incident Summary
AUTH 처리 지연.
### Root Cause
연결 폭증.
### Action Items
1. 커넥션 재사용.
2. 인증 로직 단순화.

---

## 75. PostgreSQL Logical Replication Slot Bloat
---
service: common-db
error_message: replication slot bloat
---
### Incident Summary
Replication Slot으로 WAL 누적.
### Root Cause
구독자 지연.
### Action Items
1. Slot 정리.
2. 소비자 상태 점검.

---

## 76. Redis Read After Write Inconsistency
---
service: cache-common
error_message: stale value returned
---
### Incident Summary
쓰기 직후 읽기 불일치.
### Root Cause
Replica 지연.
### Action Items
1. Strong Read 경로 분리.
2. 캐시 갱신 보장.

---

## 77. PostgreSQL Function Execution Slow
---
service: analytics-db
error_message: function execution slow
---
### Incident Summary
DB 함수 실행 지연.
### Root Cause
복잡한 로직 포함.
### Action Items
1. 로직 단순화.
2. 애플리케이션 이전 검토.

---

## 78. Redis Client Output Buffer Full
---
service: cache-common
error_message: output buffer limit reached
---
### Incident Summary
출력 버퍼 초과로 연결 종료.
### Root Cause
대량 응답 전송.
### Action Items
1. 응답 크기 제한.
2. 스트리밍 처리.

---

## 79. PostgreSQL Lock Escalation
---
service: inventory-db
error_message: lock escalation
---
### Incident Summary
락 범위 확대.
### Root Cause
대량 업데이트.
### Action Items
1. 배치 분리.
2. 트랜잭션 축소.

---

## 80. Redis Data Persistence Lag
---
service: cache-common
error_message: persistence lag
---
### Incident Summary
영속화 지연으로 데이터 손실 위험.
### Root Cause
디스크 성능 저하.
### Action Items
1. 디스크 개선.
2. 영속화 설정 조정.

---

## 81. PostgreSQL Sequence Cache Miss
---
service: order-db
error_message: sequence cache miss
---
### Incident Summary
시퀀스 접근 지연.
### Root Cause
캐시 크기 과소.
### Action Items
1. CACHE 값 증가.
2. 시퀀스 튜닝.

---

## 82. Redis Cluster Rebalance Storm
---
service: cache-common
error_message: rebalance storm
---
### Incident Summary
리밸런싱 반복 발생.
### Root Cause
노드 불안정.
### Action Items
1. 노드 안정화.
2. 수동 리밸런싱.

---

## 83. PostgreSQL Query Cache Pollution
---
service: analytics-db
error_message: cache pollution detected
---
### Incident Summary
비효율 쿼리로 캐시 오염.
### Root Cause
일회성 쿼리 다수.
### Action Items
1. 쿼리 분리.
2. 캐시 대상 제한.

---

## 84. Redis Eviction Policy Misconfigured
---
service: cache-common
error_message: eviction policy mismatch
---
### Incident Summary
비효율적인 Eviction 발생.
### Root Cause
정책 설정 오류.
### Action Items
1. allkeys-lru 검토.
2. 정책 재설정.

---

## 85. PostgreSQL Background Writer Stall
---
service: common-db
error_message: bgwriter stall
---
### Incident Summary
백그라운드 쓰기 지연.
### Root Cause
쓰기 폭증.
### Action Items
1. bgwriter 파라미터 조정.
2. I/O 분산.

---

## 86. Redis Key Encoding Inefficient
---
service: cache-common
error_message: inefficient encoding
---
### Incident Summary
비효율 인코딩으로 메모리 낭비.
### Root Cause
부적절한 자료구조 선택.
### Action Items
1. 자료구조 변경.
2. 키 설계 개선.

---

## 87. PostgreSQL Plan Cache Invalidated
---
service: analytics-db
error_message: cached plan invalidated
---
### Incident Summary
플랜 캐시 무효화로 성능 저하.
### Root Cause
스키마 변경.
### Action Items
1. 배포 후 ANALYZE.
2. 배포 전략 개선.

---

## 88. Redis Replica Sync Full Resync
---
service: cache-common
error_message: full resync required
---
### Incident Summary
전체 동기화로 부하 증가.
### Root Cause
Replica 지연 과다.
### Action Items
1. 네트워크 안정화.
2. 증분 동기화 유지.

---

## 89. PostgreSQL Index Creation Blocking
---
service: common-db
error_message: index creation blocking
---
### Incident Summary
인덱스 생성 중 쓰기 차단.
### Root Cause
CONCURRENTLY 미사용.
### Action Items
1. CONCURRENTLY 사용.
2. 오프피크 수행.

---

## 90. Redis Geo Index Memory Spike
---
service: cache-common
error_message: geo index memory high
---
### Incident Summary
Geo 인덱스로 메모리 급증.
### Root Cause
데이터 누적.
### Action Items
1. 데이터 정리.
2. TTL 적용.

---

## 91. PostgreSQL Role Permission Drift
---
service: common-db
error_message: permission denied
---
### Incident Summary
권한 불일치로 접근 실패.
### Root Cause
수동 권한 변경.
### Action Items
1. Role 관리 자동화.
2. 권한 감사.

---

## 92. Redis Pipeline Overload
---
service: cache-common
error_message: pipeline overload
---
### Incident Summary
파이프라인 과부하.
### Root Cause
대량 명령 전송.
### Action Items
1. 배치 크기 제한.
2. 백프레셔 적용.

---

## 93. PostgreSQL Tablespace Full
---
service: common-db
error_message: tablespace full
---
### Incident Summary
테이블스페이스 용량 초과.
### Root Cause
데이터 증가.
### Action Items
1. 스페이스 확장.
2. 데이터 아카이빙.

---

## 94. Redis Read Timeout Under Load
---
service: cache-common
error_message: read timeout
---
### Incident Summary
부하 시 읽기 타임아웃.
### Root Cause
CPU 포화.
### Action Items
1. 리소스 증설.
2. 요청 제한.

---

## 95. PostgreSQL Logical Decoding Lag
---
service: common-db
error_message: decoding lag
---
### Incident Summary
논리 디코딩 지연.
### Root Cause
소비자 처리 지연.
### Action Items
1. 소비자 확장.
2. 배치 처리.

---

## 96. Redis Key Version Drift
---
service: cache-common
error_message: version mismatch
---
### Incident Summary
키 버전 불일치.
### Root Cause
배포 순서 문제.
### Action Items
1. 버전 네임스페이스 적용.
2. 롤링 배포.

---

## 97. PostgreSQL Foreign Table Timeout
---
service: analytics-db
error_message: foreign table timeout
---
### Incident Summary
외부 테이블 조회 실패.
### Root Cause
외부 DB 지연.
### Action Items
1. 타임아웃 조정.
2. 데이터 동기화 검토.

---

## 98. Redis Memory Defragmentation Lag
---
service: cache-common
error_message: defrag lag
---
### Incident Summary
메모리 재정렬 지연.
### Root Cause
백그라운드 작업 집중.
### Action Items
1. defrag 설정 조정.
2. 부하 분산.

---

## 99. PostgreSQL Startup Recovery Slow
---
service: common-db
error_message: recovery slow
---
### Incident Summary
DB 재시작 후 복구 지연.
### Root Cause
WAL 과다.
### Action Items
1. WAL 정리.
2. 복구 성능 튜닝.

---

## 100. Cache-DB Consistency Check Failed
---
service: cache-common
error_message: consistency check failed
---
### Incident Summary
캐시와 DB 정합성 검사 실패.
### Root Cause
동기화 누락.
### Action Items
1. 정합성 배치 실행.
2. 동기화 로직 강화.

---
