---
service: payment-api
error_message: Connection pool exhausted
---

## Incident Summary
HikariPool-1 - Connection is not available, request timed out after 30000ms.

## Root Cause
DB 커넥션 풀 부족 (HikariCP Max Pool Size 초과). 트래픽 급증으로 인해 설정된 최대 연결 수(20)를 초과함.

## Action Items
1. DB Connection Max Pool Size를 20에서 50으로 증설.
2. 트랜잭션 점유 시간이 긴 슬로우 쿼리(Slow Query) 확인 및 최적화.
3. `show processlist` 명령어로 현재 점유 중인 세션 확인.
