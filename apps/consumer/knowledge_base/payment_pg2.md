# payment_pg.md
# PG / 결제 / 웹훅 / 멱등성 100선 Dummy Dataset

---

## 01. Payment - PG Response Timeout
---
service: payment-gateway
error_message: Upstream PG response timeout
---
### Incident Summary
[ERROR] 2024-03-20T09:01:12.321Z payment-gateway/v2.6.0 [pg001]: PG Timeout - No response from PG within 3000ms. | Context: {OrderID="ORD-1001", Amount="89000", Currency="KRW"}

### Root Cause
외부 PG사의 네트워크 지연 또는 일시적 장애로 인해 응답이 제한 시간 내 도착하지 않음.

### Action Items
1. PG 상태 페이지 및 장애 공지 확인
2. Circuit Breaker 임시 Open 여부 검토
3. 사용자에게 결제 지연 안내 및 중복 시도 방지

---

## 02. Payment - Duplicate Approval Request
---
service: payment-gateway
error_message: Duplicate transaction request detected
---
### Incident Summary
[ERROR] 2024-03-20T09:02:44.812Z payment-gateway/v2.6.0 [pg002]: Duplicate Charge Attempt | Context: {OrderID="ORD-1002", IdempotencyKey="idem-abc-001"}

### Root Cause
클라이언트 네트워크 재시도로 동일 주문에 대한 승인 요청이 중복 전송됨.

### Action Items
1. Idempotency Key 기반 중복 차단 여부 확인
2. 이미 승인된 거래인지 PG 승인 이력 조회
3. 프론트엔드 결제 버튼 Disable 처리 점검

---

## 03. Payment - Idempotency Key Missing
---
service: payment-gateway
error_message: Missing idempotency key
---
### Incident Summary
[WARN] 2024-03-20T09:04:10.044Z payment-gateway/v2.6.0 [pg003]: Missing Idempotency Key | Context: {OrderID="ORD-1003"}

### Root Cause
결제 API 요청에 멱등성 키가 포함되지 않아 중복 처리 위험 발생.

### Action Items
1. 결제 API에서 Idempotency Key 필수화
2. 키 미존재 시 요청 거절 정책 적용
3. API 가이드 문서 수정 및 공유

---

## 04. Payment - Webhook Signature Verification Failed
---
service: payment-webhook
error_message: Invalid webhook signature
---
### Incident Summary
[ERROR] 2024-03-20T09:06:55.221Z payment-webhook/v1.9.0 [wh004]: Webhook Signature Invalid | Context: {PG="KCP", EventID="evt-7781"}

### Root Cause
Webhook 요청의 서명이 서버에 저장된 Secret과 일치하지 않음.

### Action Items
1. Webhook Secret Key 재동기화
2. 중간 프록시에서 Body 변조 여부 점검
3. 실패 Webhook 이벤트 재처리 큐 적재

---

## 05. Payment - Webhook Duplicate Event
---
service: payment-webhook
error_message: Duplicate webhook event received
---
### Incident Summary
[WARN] 2024-03-20T09:08:30.901Z payment-webhook/v1.9.0 [wh005]: Duplicate Webhook | Context: {EventID="evt-7782", OrderID="ORD-1005"}

### Root Cause
PG사가 동일 이벤트를 재전송하여 중복 Webhook 수신.

### Action Items
1. EventID 기준 멱등 처리 확인
2. 이미 처리된 이벤트는 ACK만 반환
3. Webhook 처리 로그 보관 기간 점검

---

## 06. Payment - Approval Success but DB Commit Failed
---
service: payment-gateway
error_message: Payment approved but persistence failed
---
### Incident Summary
[CRITICAL] 2024-03-20T09:10:11.500Z payment-gateway/v2.6.0 [pg006]: Approved but DB error | Context: {OrderID="ORD-1006", TxID="TX99881"}

### Root Cause
PG 승인 이후 내부 DB 트랜잭션 커밋 실패로 상태 불일치 발생.

### Action Items
1. 승인된 거래 PG 측 조회
2. 내부 상태 보정 배치 실행
3. Saga 기반 보상 트랜잭션 설계 검토

---

## 07. Payment - Refund Webhook Delay
---
service: payment-webhook
error_message: Refund webhook delayed
---
### Incident Summary
[WARN] 2024-03-20T09:12:42.777Z payment-webhook/v1.9.0 [wh007]: Refund Webhook Delay | Context: {RefundID="RF-1122", Delay="15m"}

### Root Cause
PG 내부 큐 지연으로 환불 Webhook 전달이 지연됨.

### Action Items
1. 환불 상태 Polling API 병행 사용
2. 지연 허용 시간 SLA 재정의
3. 사용자 환불 지연 안내 문구 추가

---

## 08. Payment - Amount Mismatch Detected
---
service: payment-gateway
error_message: Amount mismatch between request and PG response
---
### Incident Summary
[ERROR] 2024-03-20T09:15:19.311Z payment-gateway/v2.6.0 [pg008]: Amount Mismatch | Context: {Request="100000", Approved="99000"}

### Root Cause
PG 할인 정책 또는 통화 변환 과정에서 금액 불일치 발생.

### Action Items
1. PG 승인 응답 금액 기준으로 주문 상태 갱신
2. 금액 검증 로직 강화
3. 할인/수수료 정책 문서화

---

## 09. Payment - Merchant Status Inactive
---
service: payment-gateway
error_message: Merchant account inactive
---
### Incident Summary
[ERROR] 2024-03-20T09:17:02.100Z payment-gateway/v2.6.0 [pg009]: Merchant Inactive | Context: {MerchantID="M-8899"}

### Root Cause
가맹점 계정이 PG사에서 비활성 상태로 전환됨.

### Action Items
1. PG 관리자 콘솔에서 계정 상태 확인
2. 계약 만료 여부 점검
3. 비활성 시 결제 차단 및 공지

---

## 10. Payment - Retry Storm Detected
---
service: payment-gateway
error_message: Excessive retry attempts detected
---
### Incident Summary
[WARN] 2024-03-20T09:18:45.654Z payment-gateway/v2.6.0 [pg010]: Retry Storm | Context: {OrderID="ORD-1010", RetryCount="12"}

### Root Cause
클라이언트 재시도 로직에 Backoff 미적용으로 과도한 재요청 발생.

### Action Items
1. Exponential Backoff 적용
2. 서버단 Retry 제한 추가
3. 동일 OrderID 재요청 차단

---
## 11. Payment - Approval Response Lost
---
service: payment-gateway
error_message: PG approval response lost
---
### Incident Summary
[ERROR] 2024-03-20T09:20:11.231Z payment-gateway/v2.6.0 [pg011]: Approval response lost | Context: {OrderID="ORD-1011", TxID="TX-111"}

### Root Cause
PG 승인 처리 후 네트워크 단절로 응답이 유실됨.

### Action Items
1. PG 승인 조회 API로 실제 승인 여부 확인
2. 승인 성공 시 내부 주문 상태 수동 보정
3. 승인-응답 분리 설계 검토

---

## 12. Payment - Approval Delayed
---
service: payment-gateway
error_message: Approval delayed beyond SLA
---
### Incident Summary
[WARN] 2024-03-20T09:22:45.554Z payment-gateway/v2.6.0 [pg012]: Approval delay | Context: {OrderID="ORD-1012", Delay="8s"}

### Root Cause
PG 내부 큐 적체로 승인 처리 지연 발생.

### Action Items
1. SLA 초과 승인 건 모니터링
2. 지연 시 사용자 대기 메시지 표시
3. Backup PG 전환 기준 재검토

---

## 13. Payment - Card BIN Blocked
---
service: payment-gateway
error_message: Card BIN blocked
---
### Incident Summary
[ERROR] 2024-03-20T09:25:12.882Z payment-gateway/v2.6.0 [pg013]: BIN blocked | Context: {BIN="457912", CardType="Visa"}

### Root Cause
특정 카드 BIN이 부정 사용 이슈로 PG 차단됨.

### Action Items
1. 카드사 차단 정책 확인
2. 사용자에게 다른 결제 수단 안내
3. 차단 BIN 리스트 주기적 동기화

---

## 14. Payment - Currency Not Supported
---
service: payment-gateway
error_message: Unsupported currency
---
### Incident Summary
[ERROR] 2024-03-20T09:27:40.114Z payment-gateway/v2.6.0 [pg014]: Currency not supported | Context: {Currency="JPY"}

### Root Cause
PG 계약 통화에 포함되지 않은 화폐 요청.

### Action Items
1. 허용 통화 리스트 서버단 검증
2. 프론트엔드 통화 선택 제한
3. 다중 통화 계약 검토

---

## 15. Payment - Partial Approval
---
service: payment-gateway
error_message: Partial approval issued
---
### Incident Summary
[WARN] 2024-03-20T09:30:01.229Z payment-gateway/v2.6.0 [pg015]: Partial approval | Context: {Requested="100000", Approved="70000"}

### Root Cause
카드 한도 부족으로 부분 승인 발생.

### Action Items
1. 부분 승인 허용 여부 정책 확인
2. 사용자에게 차액 결제 안내
3. 부분 승인 시 주문 분리 처리 검토

---

## 16. Payment - Refund Requested but Not Found
---
service: payment-gateway
error_message: Original transaction not found
---
### Incident Summary
[ERROR] 2024-03-20T09:32:18.330Z payment-gateway/v2.6.0 [pg016]: Refund failed | Context: {OrderID="ORD-1016"}

### Root Cause
환불 요청 시 참조 승인 거래가 PG에 존재하지 않음.

### Action Items
1. 승인 TxID 정확성 검증
2. 중복 환불 요청 여부 확인
3. PG 관리자 콘솔 조회

---

## 17. Payment - Refund Amount Exceeded
---
service: payment-gateway
error_message: Refund amount exceeds approval
---
### Incident Summary
[ERROR] 2024-03-20T09:34:55.998Z payment-gateway/v2.6.0 [pg017]: Refund exceeds | Context: {Approved="50000", Refund="60000"}

### Root Cause
승인 금액을 초과한 환불 요청.

### Action Items
1. 환불 가능 잔액 서버단 검증 강화
2. 환불 요청 UI 제한
3. 로그 기반 이상 요청 알림

---

## 18. Payment - Duplicate Refund Request
---
service: payment-gateway
error_message: Duplicate refund request
---
### Incident Summary
[WARN] 2024-03-20T09:37:41.554Z payment-gateway/v2.6.0 [pg018]: Duplicate refund | Context: {RefundKey="rf-dup-001"}

### Root Cause
동일 환불 요청이 중복 전송됨.

### Action Items
1. Refund Idempotency Key 적용
2. 이미 처리된 환불은 상태 반환만 수행
3. 환불 이력 로그 보관

---

## 19. Payment - Webhook Order Reversed
---
service: payment-webhook
error_message: Webhook event order reversed
---
### Incident Summary
[WARN] 2024-03-20T09:40:05.102Z payment-webhook/v1.9.0 [wh019]: Webhook order reversed | Context: {Events="REFUND→APPROVAL"}

### Root Cause
PG Webhook 전송 순서 보장 실패.

### Action Items
1. 이벤트 타입별 상태 머신 처리
2. 타임스탬프 기반 정렬 로직 추가
3. 순서 비의존 처리 설계

---

## 20. Payment - Webhook Retry Exhausted
---
service: payment-webhook
error_message: Webhook retry exhausted
---
### Incident Summary
[ERROR] 2024-03-20T09:42:39.901Z payment-webhook/v1.9.0 [wh020]: Webhook retry exhausted | Context: {Retry="10"}

### Root Cause
Webhook 엔드포인트 장애로 재시도 한계 초과.

### Action Items
1. DLQ에 이벤트 적재
2. Webhook 엔드포인트 상태 점검
3. 수동 재처리 도구 제공

---

## 21. Payment - Settlement File Missing
---
service: payment-settlement
error_message: Settlement file not received
---
### Incident Summary
[ERROR] 2024-03-20T09:45:10.441Z payment-settlement/v1.3.0 [st021]: Settlement file missing | Context: {Date="2024-03-19"}

### Root Cause
PG 정산 파일(SFTP)이 수신되지 않음.

### Action Items
1. SFTP 연결 상태 확인
2. PG 정산 담당자 문의
3. 수동 파일 재요청

---

## 22. Payment - Settlement Amount Mismatch
---
service: payment-settlement
error_message: Settlement amount mismatch
---
### Incident Summary
[ERROR] 2024-03-20T09:47:58.992Z payment-settlement/v1.3.0 [st022]: Settlement mismatch | Context: {Expected="12000000", Actual="11950000"}

### Root Cause
정산 수수료 또는 환불 반영 누락.

### Action Items
1. 환불 내역 대조
2. 수수료 계산 로직 검증
3. 차액 리포트 생성

---

## 23. Payment - Chargeback Received
---
service: payment-gateway
error_message: Chargeback notification received
---
### Incident Summary
[WARN] 2024-03-20T09:50:44.221Z payment-gateway/v2.6.0 [pg023]: Chargeback | Context: {OrderID="ORD-1023"}

### Root Cause
카드사 차지백 요청 접수.

### Action Items
1. 거래 증빙 자료 수집
2. 카드사 대응 프로세스 진행
3. 차지백 통계 반영

---

## 24. Payment - Fraud Rule Triggered
---
service: payment-gateway
error_message: FDS rule triggered
---
### Incident Summary
[WARN] 2024-03-20T09:53:11.772Z payment-gateway/v2.6.0 [pg024]: Fraud detected | Context: {Score="91"}

### Root Cause
이상 거래 패턴으로 FDS 차단.

### Action Items
1. 사용자 실거래 여부 확인
2. 오탐 시 룰 완화
3. 보안팀 공유

---

## 25. Payment - Payment Window Expired
---
service: payment-gateway
error_message: Payment window expired
---
### Incident Summary
[INFO] 2024-03-20T09:55:49.331Z payment-gateway/v2.6.0 [pg025]: Window expired | Context: {OrderID="ORD-1025"}

### Root Cause
결제 대기 시간 초과.

### Action Items
1. 결제 유효 시간 안내 강화
2. 재결제 버튼 제공
3. 자동 주문 취소 처리

---
## 26. Payment - Approval Success but Webhook Missing
---
service: payment-gateway
error_message: Approval succeeded but webhook not received
---
### Incident Summary
[ERROR] payment-gateway [pg026]: Approval success, webhook missing | Context: {OrderID="ORD-1026", TxID="TX-1026"}

### Root Cause
PG 승인 처리 후 Webhook 전송 실패 또는 네트워크 유실.

### Action Items
1. 승인 조회 API로 상태 확인
2. Webhook 미수신 건 보정 배치 실행
3. Webhook 재전송 요청

---

## 27. Payment - Webhook Delivered but ACK Timeout
---
service: payment-webhook
error_message: Webhook ACK timeout
---
### Incident Summary
[WARN] payment-webhook [wh027]: ACK timeout | Context: {EventID="EVT-2027"}

### Root Cause
Webhook 수신 후 ACK 응답 지연으로 PG 재시도 발생.

### Action Items
1. ACK 응답 로직 경량화
2. DB 처리 비동기화
3. 중복 이벤트 멱등 처리 강화

---

## 28. Payment - Idempotency Key Collision
---
service: payment-gateway
error_message: Idempotency key collision detected
---
### Incident Summary
[ERROR] payment-gateway [pg028]: Idempotency collision | Context: {Key="idem-028"}

### Root Cause
서로 다른 주문에서 동일 멱등 키 사용.

### Action Items
1. Key 생성 규칙 수정
2. 주문 단위 Key 강제
3. 충돌 알림 추가

---

## 29. Payment - Idempotency Record Expired
---
service: payment-gateway
error_message: Idempotency record expired
---
### Incident Summary
[WARN] payment-gateway [pg029]: Idempotency expired | Context: {OrderID="ORD-1029"}

### Root Cause
멱등 테이블 TTL 만료 후 재요청 발생.

### Action Items
1. TTL 정책 재조정
2. 장기 요청 재처리 전략 수립
3. 사용자 재결제 안내

---

## 30. Payment - Duplicate Approval After Timeout
---
service: payment-gateway
error_message: Duplicate approval after timeout
---
### Incident Summary
[ERROR] payment-gateway [pg030]: Duplicate approval | Context: {OrderID="ORD-1030"}

### Root Cause
타임아웃 후 클라이언트 재요청으로 이중 승인 발생.

### Action Items
1. 승인 조회 기반 재시도 처리
2. 자동 망취소 로직 점검
3. 재시도 정책 제한

---

## 31. Payment - Manual Cancel Requested
---
service: payment-gateway
error_message: Manual cancel requested by operator
---
### Incident Summary
[INFO] payment-gateway [pg031]: Manual cancel | Context: {OrderID="ORD-1031"}

### Root Cause
운영자 판단으로 수동 승인 취소 수행.

### Action Items
1. 취소 사유 로그 기록
2. 사용자 알림 발송
3. 감사 로그 보관

---

## 32. Payment - Cancel Failed at PG
---
service: payment-gateway
error_message: Cancel request rejected by PG
---
### Incident Summary
[ERROR] payment-gateway [pg032]: Cancel rejected | Context: {OrderID="ORD-1032"}

### Root Cause
취소 가능 시간 초과 또는 PG 정책 제한.

### Action Items
1. 환불 프로세스로 전환
2. 취소 가능 시간 명시
3. 정책 문서 공유

---

## 33. Payment - Refund Success but Webhook Delayed
---
service: payment-webhook
error_message: Refund webhook delayed
---
### Incident Summary
[WARN] payment-webhook [wh033]: Refund webhook delayed | Context: {RefundID="RF-1033"}

### Root Cause
PG 내부 큐 지연.

### Action Items
1. Polling 병행
2. SLA 초과 모니터링
3. 사용자 지연 안내

---

## 34. Payment - Refund Webhook Order Reversed
---
service: payment-webhook
error_message: Refund webhook before approval webhook
---
### Incident Summary
[WARN] payment-webhook [wh034]: Order reversed | Context: {Seq="REFUND→APPROVAL"}

### Root Cause
PG 이벤트 순서 보장 실패.

### Action Items
1. 상태 머신 처리
2. 순서 비의존 로직 적용
3. 타임스탬프 기준 정렬

---

## 35. Payment - Partial Refund Repeated
---
service: payment-gateway
error_message: Repeated partial refund
---
### Incident Summary
[ERROR] payment-gateway [pg035]: Partial refund repeated | Context: {OrderID="ORD-1035"}

### Root Cause
환불 잔액 검증 미흡.

### Action Items
1. 잔액 체크 강화
2. 환불 한도 서버 검증
3. 중복 환불 차단

---

## 36. Payment - Refund After Settlement
---
service: payment-gateway
error_message: Refund requested after settlement
---
### Incident Summary
[WARN] payment-gateway [pg036]: Refund after settlement | Context: {OrderID="ORD-1036"}

### Root Cause
정산 완료 이후 환불 요청.

### Action Items
1. 정산 후 환불 정책 분리
2. 회계팀 연계 처리
3. 사용자 안내 강화

---

## 37. Payment - Settlement File Corrupted
---
service: payment-settlement
error_message: Settlement file corrupted
---
### Incident Summary
[ERROR] payment-settlement [st037]: File corrupted | Context: {File="SETTLE_20240319.csv"}

### Root Cause
파일 전송 중 손상 발생.

### Action Items
1. 체크섬 검증
2. 재전송 요청
3. 파일 무결성 검사 추가

---

## 38. Payment - Settlement File Duplicate
---
service: payment-settlement
error_message: Duplicate settlement file received
---
### Incident Summary
[WARN] payment-settlement [st038]: Duplicate file | Context: {Date="2024-03-19"}

### Root Cause
PG 재전송으로 동일 파일 중복 수신.

### Action Items
1. 파일 해시 비교
2. 중복 처리 방지
3. 처리 이력 로그

---

## 39. Payment - Settlement Date Shifted
---
service: payment-settlement
error_message: Settlement date mismatch
---
### Incident Summary
[ERROR] payment-settlement [st039]: Date mismatch | Context: {Expected="03-19", Actual="03-20"}

### Root Cause
PG 기준일 변경 또는 공휴일 영향.

### Action Items
1. 정산 캘린더 반영
2. 날짜 유연 처리
3. 회계 공유

---

## 40. Payment - Chargeback Deadline Missed
---
service: payment-gateway
error_message: Chargeback response deadline missed
---
### Incident Summary
[CRITICAL] payment-gateway [pg040]: Chargeback deadline missed | Context: {OrderID="ORD-1040"}

### Root Cause
대응 기한 초과.

### Action Items
1. 차지백 SLA 알람
2. 전담 담당자 지정
3. 자동 증빙 수집

---

## 41. Payment - Fraud Score Spike
---
service: payment-gateway
error_message: Fraud score spike detected
---
### Incident Summary
[WARN] payment-gateway [pg041]: Fraud spike | Context: {Score="98"}

### Root Cause
단시간 고액 결제 집중.

### Action Items
1. 룰 임계치 조정
2. 사용자 추가 인증
3. 보안팀 공유

---

## 42. Payment - Test Key Used in Production
---
service: payment-gateway
error_message: Test API key used in production
---
### Incident Summary
[CRITICAL] payment-gateway [pg042]: Test key detected | Context: {Key="sk_test_xxx"}

### Root Cause
환경 변수 설정 오류.

### Action Items
1. 키 검증 로직 추가
2. 배포 전 체크 강화
3. 키 로테이션

---

## 43. Payment - API Version Deprecated
---
service: payment-gateway
error_message: Deprecated API version
---
### Incident Summary
[WARN] payment-gateway [pg043]: Deprecated API | Context: {Version="v1"}

### Root Cause
PG API 버전 미업데이트.

### Action Items
1. 최신 버전 마이그레이션
2. 호환성 테스트
3. 문서 업데이트

---

## 44. Payment - Signature Algorithm Changed
---
service: payment-webhook
error_message: Signature algorithm mismatch
---
### Incident Summary
[ERROR] payment-webhook [wh044]: Signature mismatch

### Root Cause
PG 서명 알고리즘 변경 미반영.

### Action Items
1. 알고리즘 업데이트
2. 이중 검증 기간 운영
3. 변경 공지 모니터링

---

## 45. Payment - Network Partition Detected
---
service: payment-gateway
error_message: Network partition detected
---
### Incident Summary
[CRITICAL] payment-gateway [pg045]: Network partition

### Root Cause
IDC 간 네트워크 단절.

### Action Items
1. 트래픽 우회
2. 장애 공지
3. 복구 후 정합성 점검

---

## 46. Payment - Retry Storm Detected
---
service: payment-gateway
error_message: Excessive retry detected
---
### Incident Summary
[WARN] payment-gateway [pg046]: Retry storm | Context: {Retry="15"}

### Root Cause
Backoff 미적용.

### Action Items
1. Exponential Backoff
2. 서버 Rate Limit
3. 클라이언트 가이드

---

## 47. Payment - Saga Compensation Failed
---
service: payment-gateway
error_message: Saga compensation failed
---
### Incident Summary
[ERROR] payment-gateway [pg047]: Compensation failed | Context: {OrderID="ORD-1047"}

### Root Cause
환불 성공 후 내부 롤백 실패.

### Action Items
1. DLQ 적재
2. 수동 보정
3. 재시도 정책 강화

---

## 48. Payment - State Desync Detected
---
service: payment-gateway
error_message: Payment state desynchronized
---
### Incident Summary
[ERROR] payment-gateway [pg048]: State desync | Context: {Internal="PAID", PG="CANCELED"}

### Root Cause
비동기 처리 순서 문제.

### Action Items
1. PG 기준 동기화
2. 상태 보정 배치
3. 불변 이벤트 저장

---

## 49. Payment - Operator Force Complete
---
service: payment-gateway
error_message: Operator forced completion
---
### Incident Summary
[INFO] payment-gateway [pg049]: Force complete | Context: {OrderID="ORD-1049"}

### Root Cause
운영자 판단 처리.

### Action Items
1. 사유 기록
2. 감사 로그
3. 사용자 고지

---

## 50. Payment - Historical Reconciliation Mismatch
---
service: payment-settlement
error_message: Historical reconciliation mismatch
---
### Incident Summary
[ERROR] payment-settlement [st050]: Reconciliation mismatch

### Root Cause
과거 데이터 정합성 누락.

### Action Items
1. 전체 재정산
2. 리포트 생성
3. 재발 방지 체크

---

## 51. Payment - Settlement Record Missing
---
service: payment-settlement
error_message: Settlement record missing
---
### Incident Summary
[ERROR] payment-settlement [st051]: Settlement record missing | Context: {OrderID="ORD-1051"}

### Root Cause
정산 집계 배치에서 특정 주문 레코드 누락.

### Action Items
1. 원천 승인 로그 재조회
2. 수동 정산 레코드 생성
3. 배치 로직 누락 조건 점검

---

## 52. Payment - Settlement Duplicate Record
---
service: payment-settlement
error_message: Duplicate settlement record
---
### Incident Summary
[WARN] payment-settlement [st052]: Duplicate settlement | Context: {OrderID="ORD-1052"}

### Root Cause
정산 배치 재실행으로 중복 적재 발생.

### Action Items
1. 유니크 키 제약 추가
2. 배치 멱등 처리 강화
3. 중복 데이터 제거

---

## 53. Payment - Settlement Delay Beyond SLA
---
service: payment-settlement
error_message: Settlement delayed
---
### Incident Summary
[WARN] payment-settlement [st053]: Settlement delayed | Context: {Delay="6h"}

### Root Cause
PG 정산 파일 지연 수신.

### Action Items
1. SLA 초과 알림
2. 임시 추정 정산 처리
3. PG 커뮤니케이션

---

## 54. Payment - Reconciliation Amount Drift
---
service: payment-settlement
error_message: Reconciliation drift detected
---
### Incident Summary
[ERROR] payment-settlement [st054]: Amount drift | Context: {Diff="120000"}

### Root Cause
환불/취소 반영 시점 차이.

### Action Items
1. 기간 기준 재정렬
2. 차액 리포트 생성
3. 회계팀 공유

---

## 55. Payment - Approval Success but Order Not Created
---
service: payment-gateway
error_message: Approval success but order missing
---
### Incident Summary
[CRITICAL] payment-gateway [pg055]: Order missing | Context: {TxID="TX-1055"}

### Root Cause
승인 후 주문 생성 트랜잭션 실패.

### Action Items
1. 승인 기반 주문 재생성
2. 트랜잭션 범위 점검
3. Saga 재설계

---

## 56. Payment - Order Created but Approval Missing
---
service: payment-gateway
error_message: Order exists without approval
---
### Incident Summary
[ERROR] payment-gateway [pg056]: Approval missing | Context: {OrderID="ORD-1056"}

### Root Cause
승인 요청 실패 후 주문만 생성됨.

### Action Items
1. 주문 자동 취소
2. 승인 상태 확인
3. 생성 시점 검증 강화

---

## 57. Payment - Approval Replayed by PG
---
service: payment-gateway
error_message: Approval replay detected
---
### Incident Summary
[WARN] payment-gateway [pg057]: Approval replay | Context: {TxID="TX-1057"}

### Root Cause
PG 장애 복구 중 승인 이벤트 재전송.

### Action Items
1. TxID 멱등 처리
2. 중복 승인 차단
3. 재전송 정책 공유

---

## 58. Payment - Webhook Payload Schema Changed
---
service: payment-webhook
error_message: Webhook schema mismatch
---
### Incident Summary
[ERROR] payment-webhook [wh058]: Schema mismatch

### Root Cause
PG Webhook 필드 구조 변경.

### Action Items
1. 스키마 버전 분기 처리
2. 하위 호환 유지
3. 변경 감지 테스트 추가

---

## 59. Payment - Webhook Payload Truncated
---
service: payment-webhook
error_message: Webhook payload truncated
---
### Incident Summary
[ERROR] payment-webhook [wh059]: Payload truncated

### Root Cause
프록시/로드밸런서 Body 제한.

### Action Items
1. Body size 제한 상향
2. 전송 포맷 점검
3. 무결성 검증 추가

---

## 60. Payment - Webhook DLQ Overflow
---
service: payment-webhook
error_message: DLQ overflow
---
### Incident Summary
[CRITICAL] payment-webhook [wh060]: DLQ overflow

### Root Cause
Webhook 장애 장기화로 DLQ 적재 초과.

### Action Items
1. DLQ 처리 스케일링
2. 우선순위 재처리
3. 임시 차단 정책

---

## 61. Payment - Refund Approved but Balance Not Updated
---
service: payment-gateway
error_message: Balance not updated after refund
---
### Incident Summary
[ERROR] payment-gateway [pg061]: Balance desync | Context: {OrderID="ORD-1061"}

### Root Cause
환불 후 잔액 갱신 트랜잭션 실패.

### Action Items
1. 잔액 재계산
2. 보정 배치 실행
3. 트랜잭션 분리 검토

---

## 62. Payment - Refund Requested Multiple Times
---
service: payment-gateway
error_message: Multiple refund requests
---
### Incident Summary
[WARN] payment-gateway [pg062]: Multiple refund | Context: {OrderID="ORD-1062"}

### Root Cause
CS/운영 중복 요청.

### Action Items
1. 환불 상태 락
2. 요청 제한
3. CS 툴 개선

---

## 63. Payment - Partial Refund After Partial Refund
---
service: payment-gateway
error_message: Cascading partial refund
---
### Incident Summary
[ERROR] payment-gateway [pg063]: Cascading refund

### Root Cause
잔여 금액 계산 오류.

### Action Items
1. 잔액 단일 소스화
2. 누적 환불 검증
3. 테스트 보강

---

## 64. Payment - Approval Cancel Rejected
---
service: payment-gateway
error_message: Cancel rejected by PG
---
### Incident Summary
[ERROR] payment-gateway [pg064]: Cancel rejected

### Root Cause
취소 가능 시간 초과.

### Action Items
1. 환불 전환
2. UI 안내
3. 정책 명시

---

## 65. Payment - Approval Cancel Timeout
---
service: payment-gateway
error_message: Cancel timeout
---
### Incident Summary
[WARN] payment-gateway [pg065]: Cancel timeout

### Root Cause
PG 응답 지연.

### Action Items
1. 취소 조회 재시도
2. 상태 Polling
3. 중복 취소 차단

---

## 66. Payment - Approval Canceled but Webhook Missing
---
service: payment-webhook
error_message: Cancel webhook missing
---
### Incident Summary
[ERROR] payment-webhook [wh066]: Cancel webhook missing

### Root Cause
Webhook 유실.

### Action Items
1. 취소 상태 조회
2. 보정 배치
3. 재전송 요청

---

## 67. Payment - Approval Canceled After Settlement
---
service: payment-gateway
error_message: Cancel after settlement
---
### Incident Summary
[CRITICAL] payment-gateway [pg067]: Cancel after settlement

### Root Cause
정산 완료 후 취소 시도.

### Action Items
1. 환불 전환
2. 회계 연계
3. 정책 분리

---

## 68. Payment - Foreign Currency Rounding Issue
---
service: payment-gateway
error_message: Rounding error detected
---
### Incident Summary
[WARN] payment-gateway [pg068]: Rounding issue | Context: {Currency="USD"}

### Root Cause
환율 소수점 처리 차이.

### Action Items
1. 반올림 규칙 통일
2. 기준 통화 고정
3. 테스트 추가

---

## 69. Payment - FX Rate Not Updated
---
service: payment-gateway
error_message: FX rate stale
---
### Incident Summary
[ERROR] payment-gateway [pg069]: FX stale

### Root Cause
환율 배치 실패.

### Action Items
1. 환율 재동기화
2. 실패 알림
3. 캐시 TTL 점검

---

## 70. Payment - PG Failover Triggered
---
service: payment-gateway
error_message: PG failover triggered
---
### Incident Summary
[CRITICAL] payment-gateway [pg070]: Failover triggered

### Root Cause
주 PG 장애.

### Action Items
1. 보조 PG 전환
2. 트래픽 분산
3. 장애 공지

---

## 71. Payment - Failover Approval Inconsistent
---
service: payment-gateway
error_message: Inconsistent approval after failover
---
### Incident Summary
[ERROR] payment-gateway [pg071]: Inconsistent approval

### Root Cause
PG 간 승인 상태 불일치.

### Action Items
1. 단일 기준 PG 지정
2. 상태 보정
3. 전환 절차 점검

---

## 72. Payment - PG Recovery Duplicate Events
---
service: payment-gateway
error_message: Duplicate events after recovery
---
### Incident Summary
[WARN] payment-gateway [pg072]: Duplicate events

### Root Cause
장애 복구 후 이벤트 재전송.

### Action Items
1. 이벤트 멱등 처리
2. 재전송 필터
3. 로그 비교

---

## 73. Payment - Webhook Burst After Recovery
---
service: payment-webhook
error_message: Webhook burst
---
### Incident Summary
[WARN] payment-webhook [wh073]: Burst detected

### Root Cause
지연 이벤트 일괄 전송.

### Action Items
1. 처리율 제한
2. 큐 확장
3. 순차 처리

---

## 74. Payment - Payment State Stuck
---
service: payment-gateway
error_message: Payment state stuck
---
### Incident Summary
[ERROR] payment-gateway [pg074]: State stuck | Context: {State="PENDING"}

### Root Cause
중간 상태 이벤트 누락.

### Action Items
1. 상태 타임아웃 처리
2. 재조회 배치
3. 자동 종료

---

## 75. Payment - Long Pending Cleanup Failed
---
service: payment-gateway
error_message: Pending cleanup failed
---
### Incident Summary
[WARN] payment-gateway [pg075]: Cleanup failed

### Root Cause
정리 배치 실패.

### Action Items
1. 재실행
2. 실패 알림
3. 배치 안정화

---

## 76. Payment - Idempotency Table Lock Contention
---
service: payment-gateway
error_message: Idempotency table lock contention
---
### Incident Summary
[WARN] payment-gateway [pg076]: Lock contention

### Root Cause
동시 대량 요청.

### Action Items
1. 샤딩
2. TTL 분리
3. 큐잉

---

## 77. Payment - Idempotency Cleanup Failed
---
service: payment-gateway
error_message: Idempotency cleanup failed
---
### Incident Summary
[ERROR] payment-gateway [pg077]: Cleanup failed

### Root Cause
배치 예외.

### Action Items
1. 수동 정리
2. 배치 로그 점검
3. 재발 방지

---

## 78. Payment - Operator Refund Override
---
service: payment-gateway
error_message: Operator refund override
---
### Incident Summary
[INFO] payment-gateway [pg078]: Override refund

### Root Cause
운영자 수동 처리.

### Action Items
1. 사유 기록
2. 감사 로그
3. 사용자 고지

---

## 79. Payment - Operator Approval Override
---
service: payment-gateway
error_message: Operator approval override
---
### Incident Summary
[INFO] payment-gateway [pg079]: Override approval

### Root Cause
CS 요청.

### Action Items
1. 이력 기록
2. 권한 점검
3. 승인 흐름 재검토

---

## 80. Payment - Audit Log Missing
---
service: payment-gateway
error_message: Audit log missing
---
### Incident Summary
[CRITICAL] payment-gateway [pg080]: Audit log missing

### Root Cause
로그 파이프라인 장애.

### Action Items
1. 로그 재수집
2. 파이프라인 점검
3. 이중 기록

---

## 81. Payment - Audit Log Delay
---
service: payment-gateway
error_message: Audit log delayed
---
### Incident Summary
[WARN] payment-gateway [pg081]: Audit delay

### Root Cause
로그 큐 적체.

### Action Items
1. 큐 확장
2. 소비자 스케일링
3. SLA 정의

---

## 82. Payment - Compliance Flag Raised
---
service: payment-gateway
error_message: Compliance flag raised
---
### Incident Summary
[WARN] payment-gateway [pg082]: Compliance flag

### Root Cause
규제 기준 초과 거래.

### Action Items
1. 내부 검토
2. 보고 절차
3. 정책 반영

---

## 83. Payment - PCI Scan Failed
---
service: payment-gateway
error_message: PCI scan failed
---
### Incident Summary
[CRITICAL] payment-gateway [pg083]: PCI scan failed

### Root Cause
보안 설정 미흡.

### Action Items
1. 취약점 수정
2. 재스캔
3. 보안팀 협업

---

## 84. Payment - Encryption Key Rotation Missed
---
service: payment-gateway
error_message: Key rotation missed
---
### Incident Summary
[ERROR] payment-gateway [pg084]: Key rotation missed

### Root Cause
운영 일정 누락.

### Action Items
1. 키 로테이션 수행
2. 자동화
3. 알림 추가

---

## 85. Payment - Decryption Failed
---
service: payment-gateway
error_message: Decryption failed
---
### Incident Summary
[ERROR] payment-gateway [pg085]: Decryption failed

### Root Cause
키 불일치.

### Action Items
1. 키 동기화
2. 실패 요청 차단
3. 로그 점검

---

## 86. Payment - Masked Data Leak Detected
---
service: payment-gateway
error_message: Masked data leak detected
---
### Incident Summary
[CRITICAL] payment-gateway [pg086]: Data leak

### Root Cause
마스킹 로직 누락.

### Action Items
1. 즉시 차단
2. 로직 수정
3. 감사 수행

---

## 87. Payment - Sensitive Field Logged
---
service: payment-gateway
error_message: Sensitive field logged
---
### Incident Summary
[ERROR] payment-gateway [pg087]: Sensitive log

### Root Cause
디버그 로그 설정 오류.

### Action Items
1. 로그 필터링
2. 로그 삭제
3. 릴리즈 점검 강화

---

## 88. Payment - Log Retention Policy Violation
---
service: payment-gateway
error_message: Log retention violation
---
### Incident Summary
[WARN] payment-gateway [pg088]: Retention violation

### Root Cause
보관 정책 미적용.

### Action Items
1. 정책 적용
2. 자동 삭제
3. 감사 대응

---

## 89. Payment - Historical Data Rebuild
---
service: payment-settlement
error_message: Historical rebuild required
---
### Incident Summary
[INFO] payment-settlement [st089]: Rebuild triggered

### Root Cause
정합성 점검 결과 오류.

### Action Items
1. 전체 재처리
2. 검증 리포트
3. 재발 방지

---

## 90. Payment - Data Migration Mismatch
---
service: payment-gateway
error_message: Data migration mismatch
---
### Incident Summary
[ERROR] payment-gateway [pg090]: Migration mismatch

### Root Cause
마이그레이션 스크립트 오류.

### Action Items
1. 롤백
2. 데이터 보정
3. 재마이그레이션

---

## 91. Payment - Legacy Transaction Imported
---
service: payment-gateway
error_message: Legacy transaction imported
---
### Incident Summary
[INFO] payment-gateway [pg091]: Legacy import

### Root Cause
구 시스템 데이터 이관.

### Action Items
1. 상태 매핑
2. 검증
3. 이력 표시

---

## 92. Payment - Legacy State Mapping Failed
---
service: payment-gateway
error_message: Legacy state mapping failed
---
### Incident Summary
[ERROR] payment-gateway [pg092]: Mapping failed

### Root Cause
상태 코드 불일치.

### Action Items
1. 매핑 테이블 수정
2. 재처리
3. 테스트 보강

---

## 93. Payment - Bulk Adjustment Executed
---
service: payment-settlement
error_message: Bulk adjustment executed
---
### Incident Summary
[INFO] payment-settlement [st093]: Bulk adjustment

### Root Cause
회계 조정 작업.

### Action Items
1. 사유 기록
2. 감사 로그
3. 영향 분석

---

## 94. Payment - Bulk Adjustment Rollback
---
service: payment-settlement
error_message: Bulk adjustment rollback
---
### Incident Summary
[WARN] payment-settlement [st094]: Rollback

### Root Cause
조정 오류 발견.

### Action Items
1. 롤백 수행
2. 데이터 재검증
3. 승인 절차 강화

---

## 95. Payment - Manual Reconciliation Performed
---
service: payment-settlement
error_message: Manual reconciliation
---
### Incident Summary
[INFO] payment-settlement [st095]: Manual reconciliation

### Root Cause
자동 정산 실패.

### Action Items
1. 결과 기록
2. 자동화 보완
3. 재발 방지

---

## 96. Payment - Monitoring Alert Missed
---
service: payment-gateway
error_message: Monitoring alert missed
---
### Incident Summary
[ERROR] payment-gateway [pg096]: Alert missed

### Root Cause
알림 설정 오류.

### Action Items
1. 알림 점검
2. 이중 채널 설정
3. 테스트 알림

---

## 97. Payment - SLA Breach Reported
---
service: payment-gateway
error_message: SLA breach
---
### Incident Summary
[CRITICAL] payment-gateway [pg097]: SLA breach

### Root Cause
장기 장애 영향.

### Action Items
1. 원인 분석
2. 개선 계획 수립
3. 보고

---

## 98. Payment - Incident Postmortem Created
---
service: payment-gateway
error_message: Postmortem created
---
### Incident Summary
[INFO] payment-gateway [pg098]: Postmortem created

### Root Cause
대규모 장애 종료 후 분석.

### Action Items
1. 문서화
2. 액션 트래킹
3. 공유

---

## 99. Payment - Preventive Rule Added
---
service: payment-gateway
error_message: Preventive rule added
---
### Incident Summary
[INFO] payment-gateway [pg099]: Preventive rule added

### Root Cause
재발 방지 조치.

### Action Items
1. 룰 배포
2. 효과 모니터링
3. 주기적 검토

---

## 100. Payment - System Stabilized
---
service: payment-gateway
error_message: System stabilized
---
### Incident Summary
[INFO] payment-gateway [pg100]: System stabilized

### Root Cause
모든 장애 조치 완료.

### Action Items
1. 정상화 공지
2. 모니터링 강화
3. 후속 개선 과제 관리
