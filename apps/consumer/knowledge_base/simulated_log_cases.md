# CALI Simulated Log Cases for RAG Augmentation
# 이 파일은 main.py가 생성하는 구체적인 로그 패턴을 RAG 지식으로 학습시키기 위해 사용됩니다.

---

## 01. Auth - JWT Validation Failure High Rate
---
service: auth-security-svc
error_message: High rate of JWT validation failures
---
### Incident Summary
[ERROR] 2024-03-15T10:00:00.123Z auth-security-svc/v4.2.1 [a1b2c3d4]: Security Alert - [FIN-ABC12] High rate of JWT validation failures. | Context: {ClientIP="45.12.34.56", FailCount="150/s", AuthMethod="Bearer"}

### Root Cause
특정 IP(45.12.34.56)에서 유효하지 않은 JWT 토큰을 사용하여 초당 150회 이상의 인증 시도 발생. 이는 전형적인 토큰 기반 무차별 대입(Credential Stuffing) 또는 리플레이 공격 징후임.

### Action Items
1. 해당 ClientIP(45.12.34.56)를 WAF 또는 Security Group에서 즉시 차단. (Blacklist 등록)
2. Fail2Ban 설정이 정상 동작하는지 확인하고 임계값(Threshold)을 하향 조정 검토.
3. 해당 IP 대역의 최근 접속 로그를 전수 조사하여 성공한 케이스가 있는지 확인.

---

## 02. Auth - Brute Force Attack Detected
---
service: auth-security-svc
error_message: Brute Force protection triggered
---
### Incident Summary
[WARN] 2024-03-15T10:05:00.123Z auth-security-svc/v4.2.1 [x9y8z7w6]: Login Failed - Brute Force protection triggered for user admin. | Context: {ClientIP="103.20.10.5", Action="BruteForce", TargetUser="admin"}

### Root Cause
'admin' 계정에 대해 단시간 내 다수의 로그인 실패가 발생하여 Brute Force 보호 트리거가 발동됨. 공격자는 딕셔너리 공격을 수행 중일 가능성이 높음.

### Action Items
1. 'admin' 계정을 즉시 잠금 조치(Lock)하고 관리자에게 알림 발송.
2. 공격자 IP(103.20.10.5) 차단.
3. 관리자 계정에 대한 MFA(다중 인증) 강제 적용 여부 점검.
4. 관리자 페이지 접근이 외부망에 노출되어 있는지 확인 (인트라넷 전용으로 변경 권장).

---

## 03. Payment - External PG Timeout
---
service: payment-gateway
error_message: Upstream provider response timed out
---
### Incident Summary
[ERROR] 2024-03-15T10:10:00.123Z payment-gateway/v2.5.0 [p1o2i3u4]: PG Timeout - Upstream provider response timed out after 3000ms. | Context: {Amount="125000", Currency="KRW", MerchantID="M-1234"}

### Root Cause
상위 PG사(Provider)의 응답이 3초(3000ms) 내에 오지 않아 타임아웃 발생. PG사 측 장애 또는 네트워크 지연이 원인일 수 있음.

### Action Items
1. PG사 상태 페이지(Status Page)를 확인하여 공지된 장애가 있는지 확인.
2. 타임아웃 발생 빈도가 높다면, 잠시 Circuit Breaker를 수동으로 개방(Open)하여 트래픽 차단.
3. 사용자에게 "결제 지연" 안내 메시지 노출 및 재시도 자제 요청.

---

## 04. Payment - Double Charge Detected
---
service: payment-gateway
error_message: Duplicate transaction detected
---
### Incident Summary
[ERROR] 2024-03-15T10:15:00.123Z payment-gateway/v2.5.0 [q1w2e3r4]: Double Charge - Duplicate transaction detected for OrderID ORD-998877. | Context: {Amount="50000", CardType="Visa", MerchantID="M-5678"}

### Root Cause
주문번호(OrderID: ORD-998877)에 대해 이미 결제 성공 이력이 존재함에도 불구하고 중복 승인 요청이 인입됨. 클라이언트의 중복 클릭이나 네트워크 불안정으로 인한 재전송이 원인.

### Action Items
1. 멱등성(Idempotency) 로직에 의해 해당 요청은 자동 거절되었는지 확인.
2. 만약 실제 승인까지 이루어졌다면, 즉시 망취소(Void) 또는 부분 환불 수행.
3. 클라이언트(Front-end) 측에서 결제 버튼 클릭 후 비활성화(Disable) 처리가 잘 되어 있는지 점검.

---

## 05. Payment - Circuit Breaker Open
---
service: payment-gateway
error_message: Circuit Breaker Open
---
### Incident Summary
[CRITICAL] 2024-03-15T10:20:00.123Z payment-gateway/v2.5.0 [l1k2j3h4]: Circuit Breaker Open - Failure rate threshold exceeded. | Context: {CircuitState="Open", FailRate="85%", LastSuccess="20s ago"}

### Root Cause
최근 결제 실패율이 임계치(예: 50% 이상)를 초과하여 서킷 브레이커가 발동(Open)됨. 현재 모든 결제 요청을 차단 중인 상태. 주로 PG사 전면 장애 시 발생.

### Action Items
1. PG사 장애 여부 확인 및 비상 연락망 가동.
2. 예비(Backup) PG사가 연동되어 있다면 트래픽 스위칭(Failover) 수행.
3. 서비스 메인 화면에 "결제 서비스 점검 중" 공지 게시.
4. 일정 시간 후 Half-Open 상태에서 테스트 결제가 성공하는지 모니터링.

---

## 06. BizLogic - Inventory Negative Stock
---
service: biz-logic-engine
error_message: Stock count cannot be negative
---
### Incident Summary
[ERROR] 2024-03-15T10:25:00.123Z biz-logic-engine/v1.12.0 [zxcv1234]: Inventory Error - Stock count cannot be negative for ItemID ITEM-555. | Context: {ItemID="ITEM-555", StockLevel="-2", CartID="a1b2c3d4"}

### Root Cause
상품(ITEM-555)의 재고를 차감하는 과정에서 재고가 음수(-2)가 되는 정합성 오류 발생. 동시성 이슈(Race Condition)로 인해 여러 주문이 동시에 재고를 선점했을 가능성 높음.

### Action Items
1. 해당 ItemID에 대한 주문 접수 일시 중단.
2. DB의 재고 데이터를 실제 창고 데이터와 대조하여 보정(Correction) 쿼리 실행.
3. 재고 차감 로직에 비관적 락(Pessimistic Lock, `SELECT FOR UPDATE`) 또는 Redis 기반 분산 락 적용 검토.

---

## 07. BizLogic - Coupon Usage Limit Exceeded
---
service: biz-logic-engine
error_message: Coupon usage limit exceeded
---
### Incident Summary
[ERROR] 2024-03-15T10:30:00.123Z biz-logic-engine/v1.12.0 [asdf5678]: Coupon Error - Coupon usage limit exceeded. | Context: {CouponCode="SALE-2024-XXXX", CurrentUsage="1001", MaxLimit="1000"}

### Root Cause
선착순 쿠폰(SALE-2024-XXXX)의 최대 사용 한도(1000장)를 초과하여 사용 요청이 들어옴. 캐시(Redis)와 DB 간의 카운트 동기화 지연이나 락 미적용이 원인일 수 있음.

### Action Items
1. 사용자에게 "쿠폰 소진" 메시지 안내.
2. 초과 발행된 쿠폰에 대해 취소 처리 또는 고객 보상 정책(포인트 지급 등) 수립.
3. 쿠폰 발급 로직을 Lua Script 등을 활용한 원자적(Atomic) 연산으로 개선.

---

## 08. DB - Connection Pool Exhausted
---
service: db-cache-cluster
error_message: HikariPool-1 connection is not available
---
### Incident Summary
[ERROR] 2024-03-15T10:35:00.123Z db-cache-cluster/v8.0.32 [db123456]: Connection Pool - HikariPool-1 connection is not available, timed out. | Context: {WaitTime="30000ms", ActiveConnections="50/50", QueueSize="200"}

### Root Cause
DB 커넥션 풀(최대 50개)이 모두 소진되었으며, 대기 큐에도 200개의 요청이 쌓여있음. 특정 쿼리의 수행 시간이 길어지거나(Slow Query), 트래픽 폭주로 인한 현상.

### Action Items
1. 현재 실행 중인 쿼리(`SHOW PROCESSLIST`)를 확인하여 Long Running Query를 강제 종료(Kill).
2. DB 인스턴스 사양(CPU/Memory) 모니터링 및 필요 시 스케일 업.
3. HikariCP의 `maximumPoolSize` 증설 검토 (단, DB 스펙 고려 필요).
4. 애플리케이션 측 트랜잭션 점유 시간을 줄이는 리팩토링 필요.

---

## 09. DB - Deadlock Detected
---
service: db-cache-cluster
error_message: Transaction rolled back due to deadlock
---
### Incident Summary
[ERROR] 2024-03-15T10:40:00.123Z db-cache-cluster/v8.0.32 [db654321]: Deadlock Detected - Transaction rolled back due to deadlock. | Context: {Table="Orders", SQLState="40001", LockWait="1200ms"}

### Root Cause
Orders 테이블에 대해 서로 다른 트랜잭션이 상호 교차 잠금(Lock)을 시도하다가 데드락 발생. 주로 부모-자식 테이블 간 FK 업데이트 순서나 인덱스 미비로 인해 발생.

### Action Items
1. 데드락 그래프(Deadlock Graph)를 분석하여 충돌하는 쿼리 패턴 파악.
2. 트랜잭션 내 테이블 접근 순서를 모든 로직에서 동일하게(예: A -> B) 맞추도록 수정.
3. 불필요한 락 범위를 줄이기 위해 인덱스 최적화.

---

## 10. Infra - Pod OOMKilled
---
service: infra-eks-core
error_message: Pod memory limit exceeded
---
### Incident Summary
[ERROR] 2024-03-15T10:45:00.123Z infra-eks-core/v1.28.4 [k8s12345]: OOMKilled - Pod memory limit exceeded. | Context: {PodName="biz-logic-engine-5-abcde", Mem_Usage="100%", NodeIP="10.0.1.50"}

### Root Cause
`biz-logic-engine` 파드가 할당된 메모리 한도(Limit)를 초과하여 커널에 의해 강제 종료(OOMKilled)됨. 메모리 누수(Leak) 또는 대용량 데이터 처리 로직이 원인.

### Action Items
1. 파드 리소스 Limit을 상향 조정 (예: 512Mi -> 1Gi).
2. 힙 덤프(Heap Dump)를 분석하여 메모리 누수 지점 파악.
3. HPA(Horizontal Pod Autoscaler) 설정을 확인하여 부하 시 파드가 충분히 스케일 아웃되고 있는지 점검.

---

## 11. Infra - HPA Scaling Failure
---
service: infra-eks-core
error_message: Failed to get cpu utilization for scaling
---
### Incident Summary
[ERROR] 2024-03-15T10:50:00.123Z infra-eks-core/v1.28.4 [k8s54321]: HPA Fail - Failed to get cpu utilization for scaling. | Context: {PodName="metrics-server-xx", Error="MetricsAPIUnavailable"}

### Root Cause
HPA 컨트롤러가 메트릭 서버(Metrics Server)로부터 CPU 사용률 데이터를 가져오지 못해 오토스케일링이 동작하지 않음. Metrics Server 장애 가능성 높음.

### Action Items
1. `kubectl get apiservices`로 메트릭 API 상태 확인.
2. `metrics-server` 파드 로그 확인 및 재시작.
3. 오토스케일링이 멈춘 동안 수동으로 `kubectl scale` 명령어를 사용해 레플리카 수 조정.

---

## 12. Infra - Image Pull BackOff
---
service: infra-eks-core
error_message: Failed to pull image from ECR
---
### Incident Summary
[ERROR] 2024-03-15T10:55:00.123Z infra-eks-core/v1.28.4 [k8s99999]: ImagePullBackOff - Failed to pull image from ECR. | Context: {PodName="new-deploy-xx", Image="cali/payment:v2.5.1", Error="AccessDenied"}

### Root Cause
ECR에서 이미지를 가져오려 했으나 실패함. 이미지 태그(v2.5.1) 오타, ECR 인증 토큰 만료, 또는 IAM Role 권한 부족이 원인일 수 있음.

### Action Items
1. ECR 리포지토리에 해당 태그(v2.5.1)가 실제로 존재하는지 확인.
2. 워커 노드의 IAM Role에 ECR 읽기 권한(AmazonEC2ContainerRegistryReadOnly)이 있는지 점검.
3. `imagePullSecrets` 설정이 필요한지 확인 (Cross-account 접근 시).

---

## 13. BizLogic - Saga Compensation Failed
---
service: biz-logic-engine
error_message: Refund issued but inventory restore failed
---
### Incident Summary
[ERROR] 2024-03-15T11:00:00.123Z biz-logic-engine/v1.12.0 [saga1234]: Saga Compensation - Refund issued but inventory restore failed. | Context: {OrderID="ORD-555", CompensationStep="RestoreStock", Error="RemoteServiceUnavailable"}

### Root Cause
주문 취소 프로세스(Saga Pattern) 중, 결제 환불은 성공했으나 재고 복구(Restore Stock) 단계가 실패하여 데이터 불일치 발생. 재고 서비스 장애가 원인일 수 있음.

### Action Items
1. 재고 복구 실패 건을 별도 DLQ(Dead Letter Queue)나 DB 테이블에 기록했는지 확인.
2. 실패한 재고 복구 요청을 수동으로 재시도하거나 배치 작업으로 일괄 처리.
3. Saga 오케스트레이터의 보상 트랜잭션 재시도(Retry) 정책 강화.

---

## 14. Payment - Fraud Detected
---
service: payment-gateway
error_message: Transaction blocked by FDS rules
---
### Incident Summary
[WARN] 2024-03-15T11:05:00.123Z payment-gateway/v2.5.0 [fds12345]: Fraud Detected - Transaction blocked by FDS rules. | Context: {RiskScore="92", RuleID="FDS-RULE-05", Amount="10000000"}

### Root Cause
이상금융거래탐지시스템(FDS) 룰(FDS-RULE-05)에 의해 고위험 거래로 분류되어 차단됨. 고액 결제이거나 평소 사용 패턴과 상이한 경우 발생.

### Action Items
1. 해당 거래가 실제 부정 거래인지 사용자 확인(전화/SMS 인증).
2. 오탐(False Positive)으로 확인될 경우 FDS 룰 임계값 조정 또는 해당 사용자 예외 처리.
3. 보안 팀에 해당 패턴 리포트.

---

## 15. DB - Redis OOM
---
service: db-cache-cluster
error_message: OOM command not allowed
---
### Incident Summary
[ERROR] 2024-03-15T11:10:00.123Z db-cache-cluster/v8.0.32 [redis123]: Redis Error - OOM command not allowed, maxmemory reached. | Context: {UsedMemory="4.0GB", MaxMemory="4.0GB", EvictionPolicy="noeviction"}

### Root Cause
Redis 메모리가 가득 찼으며, Eviction Policy가 `noeviction`으로 설정되어 있어 더 이상 데이터를 쓸 수 없음. 캐시 용량 부족 또는 TTL 미설정 키 누적이 원인.

### Action Items
1. 긴급 조치로 Redis 인스턴스 스케일 업(메모리 증설).
2. 사용되지 않는 키 분석 후 삭제 (`SCAN` 명령 활용).
3. Eviction Policy를 `allkeys-lru` 또는 `volatile-lru`로 변경하여 오래된 키 자동 삭제 유도.
4. 모든 캐시 키에 적절한 TTL(Time To Live)이 설정되어 있는지 코드 점검.

---

## 16. Auth - MFA Verification Failed
---
service: auth-security-svc
error_message: Multi-factor authentication verification failed
---
### Incident Summary
[WARN] 2024-03-15T11:15:00.123Z auth-security-svc/v4.2.1 [auth1234]: MFA Failed - Multi-factor authentication verification failed. | Context: {User="john_doe", AuthMethod="OTP", Attempt="3"}

### Root Cause
사용자가 MFA(OTP 등) 인증 번호를 3회 이상 잘못 입력함. 입력 실수 또는 계정 탈취 시도일 수 있음.

### Action Items
1. 추가 실패 시 계정 임시 잠금 처리.
2. 사용자에게 "인증 번호 재발송" 또는 "비밀번호 찾기" 옵션 안내.
3. OTP 서버 시간 동기화(NTP) 상태 점검 (시간이 어긋나면 OTP 불일치 발생).

---

## 17. Infra - DNS Resolution Failure
---
service: infra-eks-core
error_message: Temporary failure in name resolution
---
### Incident Summary
[ERROR] 2024-03-15T11:20:00.123Z infra-eks-core/v1.28.4 [net12345]: DNS Error - Temporary failure in name resolution. | Context: {TargetHost="db-cache-cluster.local", Error="NXDOMAIN"}

### Root Cause
Kubernetes 내부 DNS(CoreDNS)가 서비스 도메인(`db-cache-cluster.local`)을 해석하지 못함. CoreDNS 파드 부하 또는 네트워크 정책 차단 가능성.

### Action Items
1. `kubectl get pods -n kube-system -l k8s-app=kube-dns`로 CoreDNS 파드 상태 확인.
2. CoreDNS 로그(`kubectl logs`)에 에러가 있는지 확인.
3. 해당 파드에서 `nslookup` 명령어로 직접 조회 테스트.

---

## 18. BizLogic - Order Price Mismatch
---
service: biz-logic-engine
error_message: Price mismatch between cart and checkout
---
### Incident Summary
[ERROR] 2024-03-15T11:25:00.123Z biz-logic-engine/v1.12.0 [prc12345]: Order Failed - Price mismatch between cart and checkout. | Context: {CartTotal="50000", CheckoutTotal="45000", Diff="-5000"}

### Root Cause
장바구니 담을 당시의 가격과 결제 시점의 가격이 달라서 주문이 거절됨. 그 사이에 할인이 종료되었거나 가격 데이터가 변경된 경우 발생.

### Action Items
1. 사용자에게 "상품 가격이 변경되었습니다" 알림 노출 후 장바구니 갱신 유도.
2. 가격 정보 캐싱 시간(TTL)을 단축하여 데이터 불일치 최소화.
3. 가격 변경 이력 로그 확인.

---

## 19. Payment - Merchant ID Invalid
---
service: payment-gateway
error_message: Invalid Merchant ID
---
### Incident Summary
[ERROR] 2024-03-15T11:30:00.123Z payment-gateway/v2.5.0 [mer12345]: Payment Declined - Invalid Merchant ID. | Context: {MerchantID="M-0000", Error="AccountNotFound"}

### Root Cause
결제 요청에 포함된 가맹점 ID(MerchantID)가 유효하지 않거나 계약이 만료된 계정임. 설정 파일(Config) 오타 가능성.

### Action Items
1. `main.py` 또는 설정 파일(`config.yaml`)에 올바른 Merchant ID가 설정되어 있는지 확인.
2. PG사 관리자 콘솔에서 해당 가맹점 계정 상태(Active/Inactive) 확인.

---

## 20. Infra - Liveness Probe Failed
---
service: infra-eks-core
error_message: Pod is unhealthy, restarting
---
### Incident Summary
[WARN] 2024-03-15T11:35:00.123Z infra-eks-core/v1.28.4 [liv12345]: Liveness Probe Failed - Pod is unhealthy, restarting... | Context: {PodName="auth-security-svc-x", FailCount="3", LastCheck="500 Error"}

### Root Cause
kubelet이 파드의 `/healthz` 엔드포인트를 호출했으나 실패(예: 500 응답, 타임아웃)하여 파드를 재시작하는 중. 애플리케이션 데드락 또는 과부하 상태.

### Action Items
1. 재시작 전 파드 로그를 확보하여 행(Hang) 걸린 원인 분석.
2. Liveness Probe의 타임아웃 및 실패 임계값(FailureThreshold)을 너무 타이트하지 않게 조정.
3. 애플리케이션의 헬스 체크 로직이 너무 무거운 작업(DB 조회 등)을 포함하고 있는지 점검.

---

## 21. DB - Slow Query Alert
---
service: db-cache-cluster
error_message: Query execution time exceeded limit
---
### Incident Summary
[WARN] 2024-03-15T11:40:00.123Z db-cache-cluster/v8.0.32 [slo12345]: Slow Query - Query execution time exceeded 2000ms. | Context: {QueryTime="2500ms", Table="Transactions", SQLFragment="SELECT * FROM Transactions WHERE..."}

### Root Cause
Transactions 테이블 조회 쿼리가 2초 이상 소요됨. 인덱스가 없거나(Full Table Scan), 데이터 양이 급증하여 성능 저하 발생.

### Action Items
1. `EXPLAIN` 명령어로 해당 쿼리의 실행 계획 분석.
2. 적절한 인덱스(Index) 추가.
3. 불필요한 조회 컬럼(`SELECT *`)을 필요한 컬럼만 조회하도록 수정.

---

## 22. Auth - API Key Limit Exceeded
---
service: auth-security-svc
error_message: API Key Rate Limit Exceeded
---
### Incident Summary
[WARN] 2024-03-15T11:45:00.123Z auth-security-svc/v4.2.1 [key12345]: Rate Limit - API Key limit exceeded. | Context: {APIKey="sk_live_...", CurrentRate="100/s", Limit="50/s"}

### Root Cause
특정 API Key의 호출량이 허용 한도(초당 50회)를 초과함. 버그로 인한 루프 호출이거나 트래픽 증가가 원인.

### Action Items
1. 해당 API Key 사용자에게 요금제 업그레이드 또는 호출 최적화 안내.
2. 일시적으로 한도를 상향 조정(Throttling 완화)하여 서비스 중단 방지 검토.
3. 클라이언트 측 재시도(Retry) 로직에 지수 백오프(Exponential Backoff)가 적용되어 있는지 확인.

---

## 23. Infra - Node Not Ready
---
service: infra-eks-core
error_message: Node is in NotReady state
---
### Incident Summary
[CRITICAL] 2024-03-15T11:50:00.123Z infra-eks-core/v1.28.4 [nod12345]: Node Failure - Node is in NotReady state. | Context: {NodeIP="10.0.5.5", Reason="KubeletStopped"}

### Root Cause
워커 노드(10.0.5.5)의 Kubelet이 응답하지 않아 NotReady 상태로 변경됨. 해당 노드의 파드들은 다른 노드로 축출(Eviction)될 예정.

### Action Items
1. 해당 노드에 SSH 접속하여 `systemctl status kubelet` 확인.
2. 디스크 용량, 메모리 부족 등으로 인한 시스템 다운인지 점검.
3. 복구가 불가능할 경우 노드를 클러스터에서 제거하고 새 노드 추가.

---

## 24. BizLogic - Invalid Promotion Code
---
service: biz-logic-engine
error_message: Promotion code is invalid or expired
---
### Incident Summary
[INFO] 2024-03-15T11:55:00.123Z biz-logic-engine/v1.12.0 [pro12345]: Coupon Error - Promotion code is invalid or expired. | Context: {Code="WELCOME2023", Reason="Expired"}

### Root Cause
사용자가 만료된 프로모션 코드(WELCOME2023)를 입력함.

### Action Items
1. 사용자에게 "만료된 코드입니다" 명확한 안내 메시지 표시.
2. 현재 진행 중인 프로모션 목록을 안내.

---

## 25. Payment - Insufficient Balance
---
service: payment-gateway
error_message: Insufficient funds
---
### Incident Summary
[ERROR] 2024-03-15T12:00:00.123Z payment-gateway/v2.5.0 [bal12345]: Payment Declined - Insufficient funds. | Context: {Amount="350000", Bank="KakaoBank"}

### Root Cause
사용자 계좌 잔액 부족으로 결제 승인 거절됨. 시스템 오류 아님.

### Action Items
1. 사용자에게 "잔액이 부족합니다" 안내.
2. 계좌 충전 페이지로 리다이렉트 또는 다른 결제 수단 선택 유도.
