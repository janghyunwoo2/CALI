# CALI Knowledge Base – Fintech Business Logic & Microservices (01–100)

---

## 01. Inventory Negative Stock Error
---
service: inventory-service
error_message: Stock count cannot be negative
---
### Incident Summary
재고 차감 시 수량이 0 미만으로 내려가며 요청 실패.
### Root Cause
동시성 처리 미흡으로 Race Condition 발생.
### Action Items
1. SELECT FOR UPDATE 또는 낙관적 락 적용.
2. 재고 보정 배치 실행.

---

## 02. Duplicate Order Created
---
service: order-service
error_message: duplicate order detected
---
### Incident Summary
동일 요청으로 주문이 중복 생성됨.
### Root Cause
클라이언트 재시도에 대한 멱등성 미보장.
### Action Items
1. 주문 생성 Idempotency Key 적용.
2. 주문 생성 전 중복 검사 추가.

---

## 03. Order Status Invalid Transition
---
service: order-service
error_message: invalid order state transition
---
### Incident Summary
주문 상태가 허용되지 않은 단계로 전이됨.
### Root Cause
비동기 이벤트 순서 뒤바뀜.
### Action Items
1. 상태 전이 가드 조건 강화.
2. 이벤트 시퀀스 기반 정렬/중복 제거.

---

## 04. Payment-Order Saga Compensation Failed
---
service: orchestrator
error_message: compensation failed
---
### Incident Summary
결제 실패 후 보상 트랜잭션이 누락되어 주문이 미정상 상태로 남음.
### Root Cause
보상 단계 재시도/내구성 부족.
### Action Items
1. 보상 트랜잭션 큐 기반 재시도.
2. 사가 상태 저장 및 재처리 워커 추가.

---

## 05. Event Consumer Duplicate Processing
---
service: order-consumer
error_message: duplicate event processed
---
### Incident Summary
이벤트가 중복 처리되어 중복 상태 변경이 발생.
### Root Cause
At-least-once 전달 특성 대비 멱등 처리 누락.
### Action Items
1. event_id 기반 처리 이력 저장.
2. 멱등 핸들러 적용.

---

## 06. Outbox Table Growing Unbounded
---
service: order-service
error_message: outbox backlog increasing
---
### Incident Summary
Outbox 적체로 이벤트 발행 지연 발생.
### Root Cause
퍼블리셔 워커 장애 또는 처리량 부족.
### Action Items
1. 워커 스케일 아웃.
2. Outbox 정리 정책 및 모니터링 추가.

---

## 07. Message Broker Partition Hotspot
---
service: event-bus
error_message: partition hotspot detected
---
### Incident Summary
특정 파티션으로 이벤트가 몰려 지연 발생.
### Root Cause
파티션 키 설계가 단조로움(예: 고정 tenant).
### Action Items
1. 파티션 키 분산 설계.
2. 파티션 수 확장.

---

## 08. User Balance Double Deduction
---
service: wallet-service
error_message: balance deducted twice
---
### Incident Summary
지갑 잔액이 중복 차감됨.
### Root Cause
중복 이벤트 처리 또는 트랜잭션 경계 불명확.
### Action Items
1. 지갑 차감 멱등성 키 적용.
2. 원장 기반 정합성 검증 배치 추가.

---

## 09. Ledger Write Succeeded But Response Lost
---
service: wallet-service
error_message: ledger write ambiguous
---
### Incident Summary
원장 기록은 성공했으나 응답 유실로 재시도가 발생.
### Root Cause
네트워크 단절/타임아웃.
### Action Items
1. 원장 기록 조회 기반 재처리.
2. 클라이언트 재시도 가이드 제공.

---

## 10. Coupon Applied Beyond Limit
---
service: promotion-service
error_message: coupon usage exceeds limit
---
### Incident Summary
쿠폰 사용 제한을 초과해 적용됨.
### Root Cause
동시 요청에서 제한 카운트 레이스.
### Action Items
1. 사용 카운트 원자적 증가(락/원자 연산).
2. 사용 제한 검증을 서버 단일 진실로 적용.

---

## 11. Coupon Expired But Still Redeemed
---
service: promotion-service
error_message: coupon expired
---
### Incident Summary
만료 쿠폰이 적용되어 할인 발생.
### Root Cause
캐시된 쿠폰 정보가 갱신되지 않음.
### Action Items
1. 쿠폰 만료 시 캐시 무효화.
2. 적용 시점에 DB 기반 재검증.

---

## 12. Pricing Rule Mismatch
---
service: pricing-service
error_message: price mismatch
---
### Incident Summary
주문 금액과 결제 금액 계산이 불일치.
### Root Cause
가격 계산 버전 불일치(프론트/백엔드).
### Action Items
1. 서버 계산 금액만 사용.
2. 가격 규칙 버전 고정 및 배포 동기화.

---

## 13. Tax Calculation Drift
---
service: pricing-service
error_message: tax calculation mismatch
---
### Incident Summary
세금 계산 결과가 환경별로 다르게 산출됨.
### Root Cause
세율/반올림 규칙 변경 미반영.
### Action Items
1. 세율 테이블 업데이트.
2. 통화/세금 정밀도 규칙 표준화.

---

## 14. Shipment Created Without Payment Confirmation
---
service: fulfillment-service
error_message: shipment created before payment confirmed
---
### Incident Summary
결제 확정 전 배송이 생성됨.
### Root Cause
이벤트 순서 보장 실패.
### Action Items
1. 결제 확정 이벤트 기반 생성만 허용.
2. 상태 전이 가드 강화.

---

## 15. Order Cancellation Race
---
service: order-service
error_message: cancel race detected
---
### Incident Summary
결제 승인과 취소 요청이 동시에 들어와 상태가 꼬임.
### Root Cause
동시 업데이트 처리 미흡.
### Action Items
1. 상태 버전(optimistic concurrency) 적용.
2. 취소/승인 상호 배타 처리.

---

## 16. Refund Issued Without Inventory Restore
---
service: refund-service
error_message: refund issued but inventory not restored
---
### Incident Summary
환불은 완료됐지만 재고 복원이 누락됨.
### Root Cause
사가 단계 일부 실패 후 보상 누락.
### Action Items
1. 환불-재고 보상 트랜잭션 추가.
2. 상태 기반 재처리 워커 운영.

---

## 17. Notification Sent Twice
---
service: notification-service
error_message: duplicate notification
---
### Incident Summary
결제/배송 알림이 중복 발송됨.
### Root Cause
중복 이벤트 처리.
### Action Items
1. event_id 기반 멱등 처리.
2. 알림 발송 이력 저장.

---

## 18. Notification Not Sent
---
service: notification-service
error_message: notification missing
---
### Incident Summary
중요 알림이 발송되지 않음.
### Root Cause
큐 적체 또는 컨슈머 다운.
### Action Items
1. DLQ 모니터링 및 재처리.
2. 컨슈머 오토스케일 구성.

---

## 19. User Profile Cache Stale
---
service: user-service
error_message: stale profile data
---
### Incident Summary
사용자 프로필 변경이 반영되지 않음.
### Root Cause
캐시 무효화 누락.
### Action Items
1. 업데이트 이벤트로 캐시 무효화.
2. TTL 단축 및 강제 갱신 경로 제공.

---

## 20. Customer Tier Misapplied
---
service: loyalty-service
error_message: tier mismatch
---
### Incident Summary
등급 혜택이 잘못 적용됨.
### Root Cause
등급 산정 배치 지연 또는 데이터 누락.
### Action Items
1. 등급 산정 배치 모니터링 강화.
2. 실시간 보정 로직 추가.

---

## 21. Order Line Item Missing
---
service: order-service
error_message: line item missing
---
### Incident Summary
주문 생성 후 일부 품목이 누락됨.
### Root Cause
부분 실패 시 롤백 처리 미흡.
### Action Items
1. 트랜잭션 경계 명확화.
2. 생성 후 무결성 검증 추가.

---

## 22. Cart Merge Conflict
---
service: cart-service
error_message: cart merge conflict
---
### Incident Summary
로그인 시 장바구니 병합이 잘못됨.
### Root Cause
동시 병합 요청에서 최신 상태 덮어쓰기.
### Action Items
1. 버전 기반 병합 적용.
2. 병합 작업을 단일 큐로 직렬화.

---

## 23. Promotion Stack Rules Violated
---
service: promotion-service
error_message: promotion stacking not allowed
---
### Incident Summary
중복 프로모션이 허용되어 과할인이 발생.
### Root Cause
스택 규칙 검증 누락.
### Action Items
1. 프로모션 조합 검증 강화.
2. 규칙 엔진 테스트 추가.

---

## 24. Settlement Aggregation Duplicate
---
service: settlement-service
error_message: duplicate aggregation
---
### Incident Summary
정산 집계가 중복 반영됨.
### Root Cause
집계 배치 재실행 시 멱등성 미보장.
### Action Items
1. 집계 키 기반 멱등 처리.
2. 배치 재실행 가드 추가.

---

## 25. Settlement Cutoff Misapplied
---
service: settlement-service
error_message: cutoff rule mismatch
---
### Incident Summary
정산 컷오프 기준이 잘못 적용됨.
### Root Cause
시간대/기준일 정의 불일치.
### Action Items
1. 컷오프 규칙 문서화 및 코드 고정.
2. 표준 시간대 사용.

---

## 26. Exchange Rate Cache Missing
---
service: fx-service
error_message: exchange rate not available
---
### Incident Summary
환율 조회 실패로 결제/정산 중단.
### Root Cause
환율 소스 장애 및 캐시 미구축.
### Action Items
1. 캐시 환율 fallback 적용.
2. 다중 환율 소스 구성.

---

## 27. FX Rate Stale Applied
---
service: fx-service
error_message: stale exchange rate used
---
### Incident Summary
오래된 환율이 적용됨.
### Root Cause
캐시 갱신 실패.
### Action Items
1. 갱신 실패 알림.
2. 갱신 시점 강제 검증.

---

## 28. Idempotency Key Collides Across Tenants
---
service: payment-orchestrator
error_message: idempotency key collision
---
### Incident Summary
서로 다른 테넌트 간 멱등성 키 충돌.
### Root Cause
테넌트 네임스페이스 미포함.
### Action Items
1. tenant_id 포함한 키 구성.
2. 키 생성 규칙 표준화.

---

## 29. Distributed Transaction Timeout
---
service: orchestrator
error_message: distributed transaction timeout
---
### Incident Summary
마이크로서비스 간 트랜잭션이 타임아웃.
### Root Cause
외부 의존 호출 지연.
### Action Items
1. 타임아웃/서킷브레이커 설정.
2. 사가 기반으로 전환.

---

## 30. Circuit Breaker Open Too Long
---
service: gateway
error_message: circuit breaker open
---
### Incident Summary
서킷브레이커가 장시간 열려 서비스가 복구되지 않음.
### Root Cause
헬스체크 조건 과도.
### Action Items
1. half-open 테스트 조정.
2. 복구 임계값 재설정.

---

## 31. Retry Storm Between Services
---
service: gateway
error_message: retry storm detected
---
### Incident Summary
재시도 폭증으로 전체 시스템 부하 증가.
### Root Cause
지수 백오프 미적용.
### Action Items
1. 지수 백오프 + jitter 적용.
2. 재시도 횟수 제한.

---

## 32. API Contract Breaking Change
---
service: user-service
error_message: request schema invalid
---
### Incident Summary
배포 후 API 스키마 변경으로 클라이언트/다른 서비스 장애.
### Root Cause
호환성 없는 변경 배포.
### Action Items
1. 버저닝 적용.
2. 계약 테스트(Contract Test) 도입.

---

## 33. gRPC Deadline Exceeded
---
service: order-service
error_message: DEADLINE_EXCEEDED
---
### Incident Summary
서비스 간 gRPC 호출 타임아웃.
### Root Cause
다운스트림 지연.
### Action Items
1. 타임아웃 조정.
2. 다운스트림 성능 개선.

---

## 34. Schema Registry Incompatible
---
service: event-bus
error_message: schema incompatible
---
### Incident Summary
이벤트 스키마 호환성 오류로 생산/소비 실패.
### Root Cause
스키마 호환 규칙 위반.
### Action Items
1. 호환성 정책 enforced.
2. 스키마 린트/테스트 추가.

---

## 35. Event Payload Too Large
---
service: event-bus
error_message: message size exceeds limit
---
### Incident Summary
이벤트 메시지 크기 제한 초과.
### Root Cause
대용량 데이터 포함.
### Action Items
1. 본문은 저장소에 두고 참조만 전송.
2. 필드 최소화.

---

## 36. DLQ Growth Unnoticed
---
service: order-consumer
error_message: dlq backlog increasing
---
### Incident Summary
DLQ 적체로 이벤트 유실 위험 증가.
### Root Cause
재처리 파이프라인 부재.
### Action Items
1. DLQ 알림/대시보드 구성.
2. 재처리 워커 구현.

---

## 37. Duplicate Ledger Entries
---
service: ledger-service
error_message: duplicate ledger entry
---
### Incident Summary
원장에 중복 레코드 발생.
### Root Cause
중복 이벤트 처리 또는 키 설계 미흡.
### Action Items
1. (account_id, ref_id) 유니크 제약.
2. 멱등 처리 강화.

---

## 38. Ledger Out of Balance
---
service: ledger-service
error_message: ledger out of balance
---
### Incident Summary
차변/대변 합이 맞지 않아 원장 불일치.
### Root Cause
부분 실패 시 보정 누락.
### Action Items
1. 트랜잭션 원자성 보장.
2. 정합성 검증 배치 및 보정 스크립트.

---

## 39. Wallet Balance Negative
---
service: wallet-service
error_message: balance cannot be negative
---
### Incident Summary
지갑 잔액이 음수로 내려감.
### Root Cause
동시 차감 경쟁 조건.
### Action Items
1. 조건부 업데이트(잔액>=차감액) 적용.
2. 충돌 시 재시도/대기 처리.

---

## 40. Wallet Snapshot Drift
---
service: wallet-service
error_message: snapshot drift detected
---
### Incident Summary
스냅샷 잔액과 원장 합산 잔액 불일치.
### Root Cause
스냅샷 갱신 누락 또는 지연.
### Action Items
1. 스냅샷 갱신 배치 모니터링.
2. 원장 재계산 보정 수행.

---

## 41. Loyalty Points Double Earned
---
service: loyalty-service
error_message: points credited twice
---
### Incident Summary
포인트 적립이 중복 반영됨.
### Root Cause
이벤트 중복 소비.
### Action Items
1. 이벤트 멱등 처리.
2. 포인트 적립 유니크 키 적용.

---

## 42. Loyalty Points Expired Incorrectly
---
service: loyalty-service
error_message: points expired incorrectly
---
### Incident Summary
정상 포인트가 만료 처리됨.
### Root Cause
만료 기준일 계산 오류.
### Action Items
1. 만료 규칙 단위 테스트 추가.
2. 표준 시간대/기준일 고정.

---

## 43. KYC Status Not Updated
---
service: kyc-service
error_message: kyc status not updated
---
### Incident Summary
KYC 결과가 계정에 반영되지 않음.
### Root Cause
외부 KYC 콜백 처리 실패.
### Action Items
1. 콜백 재처리 큐 도입.
2. 상태 조회 배치 추가.

---

## 44. AML Rule Engine Delay
---
service: aml-service
error_message: aml evaluation delayed
---
### Incident Summary
AML 평가 지연으로 거래 승인 지체.
### Root Cause
룰 평가 처리량 부족.
### Action Items
1. 워커 증설.
2. 룰 최적화 및 캐시 적용.

---

## 45. Risk Score Missing
---
service: risk-service
error_message: risk score missing
---
### Incident Summary
거래 승인에 필요한 리스크 점수 누락.
### Root Cause
피처 생성 파이프라인 장애.
### Action Items
1. 피처 계산 상태 모니터링.
2. fallback 점수 정책 정의.

---

## 46. Risk Decision Inconsistent
---
service: risk-service
error_message: inconsistent decision
---
### Incident Summary
동일 거래가 서로 다른 결과로 판정됨.
### Root Cause
룰/모델 버전 혼용.
### Action Items
1. 모델/룰 버전 고정.
2. 결정 로깅 및 재현성 확보.

---

## 47. Limit Check Bypassed
---
service: limit-service
error_message: limit check bypassed
---
### Incident Summary
이체/결제 한도 검증이 우회됨.
### Root Cause
경로별 검증 로직 누락.
### Action Items
1. 공통 한도 검증 미들웨어 적용.
2. 경로 커버리지 테스트 추가.

---

## 48. Daily Limit Reset Wrong Timezone
---
service: limit-service
error_message: daily limit reset mismatch
---
### Incident Summary
일일 한도 리셋 시간이 잘못 적용됨.
### Root Cause
시간대 처리 오류.
### Action Items
1. KST 기준 고정 또는 UTC 기준 표준화.
2. 리셋 로직 테스트 추가.

---

## 49. Transfer Idempotency Missing
---
service: transfer-service
error_message: duplicate transfer executed
---
### Incident Summary
이체가 중복 실행됨.
### Root Cause
이체 요청 멱등성 미보장.
### Action Items
1. transfer_idempotency_key 적용.
2. 중복 실행 방지 유니크 키 적용.

---

## 50. Transfer Fee Miscalculated
---
service: transfer-service
error_message: fee mismatch
---
### Incident Summary
이체 수수료 계산 오류.
### Root Cause
수수료 테이블/규칙 변경 미반영.
### Action Items
1. 수수료 규칙 버전 관리.
2. 서버 단일 계산 적용.

---

## 51. Batch Job Reprocessed Same Window
---
service: batch-orchestrator
error_message: window reprocessed
---
### Incident Summary
동일 시간 구간 배치가 중복 실행됨.
### Root Cause
체크포인트 저장 실패.
### Action Items
1. 체크포인트 내구성 강화.
2. 배치 멱등성 키 적용.

---

## 52. Batch Checkpoint Corrupted
---
service: batch-orchestrator
error_message: checkpoint corrupted
---
### Incident Summary
배치 체크포인트 손상으로 재처리 오류.
### Root Cause
부분 쓰기/동시 업데이트.
### Action Items
1. 원자적 업데이트 적용.
2. 백업 체크포인트 운영.

---

## 53. Notification Template Rendering Failed
---
service: notification-service
error_message: template render failed
---
### Incident Summary
알림 템플릿 렌더링 실패로 발송 중단.
### Root Cause
필수 변수 누락.
### Action Items
1. 템플릿 스키마 검증.
2. 기본값 처리 추가.

---

## 54. SMS Provider Downstream Error
---
service: notification-service
error_message: sms provider error
---
### Incident Summary
SMS 발송 실패 증가.
### Root Cause
외부 SMS 사업자 장애.
### Action Items
1. 재시도 + 큐잉 적용.
2. 멀티 벤더 전환 검토.

---

## 55. Email Bounce Storm
---
service: notification-service
error_message: bounce rate high
---
### Incident Summary
이메일 바운스 급증으로 발송 차단 위험.
### Root Cause
수신 거부/잘못된 주소 누적.
### Action Items
1. 바운스 처리로 주소 비활성화.
2. 발송 리스트 정리.

---

## 56. Customer Support Ticket Misrouted
---
service: support-service
error_message: ticket routed incorrectly
---
### Incident Summary
CS 티켓이 잘못된 큐로 라우팅됨.
### Root Cause
라우팅 규칙 충돌.
### Action Items
1. 규칙 우선순위 재정의.
2. 라우팅 테스트 추가.

---

## 57. Subscription Renewed Twice
---
service: subscription-service
error_message: duplicate renewal
---
### Incident Summary
구독 갱신이 중복 처리됨.
### Root Cause
스케줄러 중복 실행.
### Action Items
1. 분산 락 적용.
2. 갱신 멱등성 키 적용.

---

## 58. Subscription Cancel Not Propagated
---
service: subscription-service
error_message: cancel not propagated
---
### Incident Summary
구독 해지가 하위 서비스로 전파되지 않음.
### Root Cause
이벤트 발행 실패.
### Action Items
1. Outbox 적용.
2. 재발행/재처리 워커 추가.

---

## 59. Feature Flag Drift Across Services
---
service: config-service
error_message: feature flag drift
---
### Incident Summary
서비스별 기능 플래그 상태가 불일치.
### Root Cause
캐시 갱신 지연.
### Action Items
1. 플래그 변경 이벤트로 강제 갱신.
2. TTL 단축 및 버전 체크.

---

## 60. Feature Flag Causes Partial Rollout Bug
---
service: config-service
error_message: partial rollout inconsistency
---
### Incident Summary
부분 롤아웃 중 기능 불일치로 오류 발생.
### Root Cause
사용자 할당 로직 비결정적.
### Action Items
1. 해시 기반 결정적 할당 적용.
2. 롤아웃 버킷 고정.

---

## 61. Duplicate User Created
---
service: user-service
error_message: duplicate user
---
### Incident Summary
동일 사용자 정보로 중복 계정 생성.
### Root Cause
중복 검증 레이스.
### Action Items
1. 이메일/휴대폰 유니크 제약 적용.
2. 생성 멱등성 키 적용.

---

## 62. User KYC Required But Bypassed
---
service: user-service
error_message: kyc bypass detected
---
### Incident Summary
KYC 미완료 사용자가 거래 가능 상태로 남음.
### Root Cause
체크 로직 일부 경로 누락.
### Action Items
1. 거래 전 KYC 게이트 공통화.
2. 경로 커버리지 테스트 추가.

---

## 63. Device Binding Not Enforced
---
service: security-service
error_message: device binding missing
---
### Incident Summary
기기 바인딩 정책이 적용되지 않음.
### Root Cause
정책 플래그 미반영.
### Action Items
1. 인증 단계에서 강제 적용.
2. 정책 설정 감사.

---

## 64. Push Approval Stuck Pending
---
service: auth-approval
error_message: approval pending too long
---
### Incident Summary
푸시 승인 요청이 장시간 대기 상태.
### Root Cause
푸시 전송/수신 지연.
### Action Items
1. 타임아웃 및 재시도.
2. 대체 인증 수단 제공.

---

## 65. Statement Generation Failed
---
service: statement-service
error_message: statement generation failed
---
### Incident Summary
거래 내역서 생성 실패.
### Root Cause
템플릿/데이터 누락.
### Action Items
1. 데이터 스키마 검증.
2. 재생성 워크플로우 제공.

---

## 66. Statement Data Mismatch
---
service: statement-service
error_message: statement mismatch
---
### Incident Summary
내역서 금액/건수 불일치.
### Root Cause
집계 기준 차이.
### Action Items
1. 집계 기준 단일화.
2. 검증 리포트 생성.

---

## 67. Cashback Credited Late
---
service: cashback-service
error_message: cashback delayed
---
### Incident Summary
캐시백 적립이 지연됨.
### Root Cause
배치 적체.
### Action Items
1. 워커 확장.
2. 우선순위 큐 적용.

---

## 68. Cashback Credited Wrong User
---
service: cashback-service
error_message: cashback user mismatch
---
### Incident Summary
캐시백이 다른 사용자에게 적립됨.
### Root Cause
참조 키 매핑 오류.
### Action Items
1. 참조키 검증 강화.
2. 롤백/보정 프로세스 실행.

---

## 69. Merchant Onboarding Incomplete
---
service: merchant-service
error_message: merchant onboarding incomplete
---
### Incident Summary
가맹점 등록이 일부 단계에서 멈춤.
### Root Cause
외부 서류 검증 지연.
### Action Items
1. 상태 머신 기반 재시도.
2. 누락 단계 알림.

---

## 70. Merchant Settlement Account Missing
---
service: merchant-service
error_message: settlement account missing
---
### Incident Summary
가맹점 정산 계좌 정보 누락으로 정산 실패.
### Root Cause
등록 단계 검증 누락.
### Action Items
1. 필수 필드 검증 강화.
2. 정산 전 사전 검증 배치.

---

## 71. Chargeback Workflow Not Triggered
---
service: dispute-service
error_message: chargeback workflow missing
---
### Incident Summary
차지백 이벤트 수신 후 워크플로우가 시작되지 않음.
### Root Cause
라우팅/필터 규칙 오류.
### Action Items
1. 이벤트 라우팅 규칙 점검.
2. 재처리 큐 추가.

---

## 72. Dispute Status Stuck
---
service: dispute-service
error_message: dispute stuck
---
### Incident Summary
분쟁 상태가 진행되지 않음.
### Root Cause
후속 이벤트 유실.
### Action Items
1. 상태 복구 배치.
2. 이벤트 소스 재동기화.

---

## 73. AML Case Created Duplicately
---
service: aml-service
error_message: duplicate aml case
---
### Incident Summary
동일 거래로 AML 케이스가 중복 생성됨.
### Root Cause
케이스 생성 멱등성 미보장.
### Action Items
1. (txn_id, rule_id) 유니크 제약.
2. 케이스 생성 멱등 처리.

---

## 74. Risk Rule Applied Wrong Segment
---
service: risk-service
error_message: rule segment mismatch
---
### Incident Summary
리스크 룰이 잘못된 고객군에 적용됨.
### Root Cause
세그먼트 분류 오류.
### Action Items
1. 세그먼트 정의 재검증.
2. 룰 적용 전 검증 로직 추가.

---

## 75. Transaction Categorization Wrong
---
service: analytics-service
error_message: category mismatch
---
### Incident Summary
거래 카테고리 분류가 잘못됨.
### Root Cause
분류 룰/모델 버전 드리프트.
### Action Items
1. 모델/룰 버전 고정.
2. 샘플링 검증 배치.

---

## 76. Duplicate Scheduled Transfer
---
service: transfer-service
error_message: duplicate scheduled transfer
---
### Incident Summary
예약 이체가 중복 실행됨.
### Root Cause
스케줄러 중복 트리거.
### Action Items
1. 분산 락 적용.
2. 실행 키 기반 멱등 처리.

---

## 77. Scheduled Transfer Missed
---
service: transfer-service
error_message: scheduled transfer missed
---
### Incident Summary
예약 이체가 실행되지 않음.
### Root Cause
스케줄러 다운 또는 큐 유실.
### Action Items
1. 스케줄러 HA 구성.
2. 누락 탐지 및 재실행 배치.

---

## 78. Reconciliation Job Skips Records
---
service: settlement-service
error_message: reconciliation skipped records
---
### Incident Summary
대사 작업에서 일부 레코드가 누락됨.
### Root Cause
페이징/커서 처리 오류.
### Action Items
1. 커서 기반 안정적 페이징 적용.
2. 누락 검증 리포트 생성.

---

## 79. Duplicate Invoice Generated
---
service: invoice-service
error_message: duplicate invoice
---
### Incident Summary
청구서가 중복 생성됨.
### Root Cause
중복 이벤트 소비.
### Action Items
1. invoice_id 유니크 제약.
2. 멱등 처리 적용.

---

## 80. Invoice Number Sequence Gap
---
service: invoice-service
error_message: invoice sequence gap
---
### Incident Summary
청구서 번호가 비연속으로 발생.
### Root Cause
시퀀스 롤백/재시도.
### Action Items
1. 번호 정책(연속성 필요 여부) 정의.
2. 감사 로그로 추적 가능하게 설계.

---

## 81. Transaction Duplicate Detected Late
---
service: fraud-service
error_message: duplicate transaction detected late
---
### Incident Summary
중복 거래 탐지가 늦어 피해 확산.
### Root Cause
실시간 탐지 지연.
### Action Items
1. 실시간 스트림 처리 강화.
2. 고위험 룰 우선 처리.

---

## 82. Fraud Rule Engine False Positive Spike
---
service: fraud-service
error_message: false positive spike
---
### Incident Summary
오탐 증가로 정상 거래 차단.
### Root Cause
룰 임계값 과도.
### Action Items
1. 임계값 튜닝.
2. 단계적 인증으로 전환.

---

## 83. Customer Support Refund Approval Missing
---
service: refund-service
error_message: approval missing
---
### Incident Summary
환불 승인 절차 누락으로 처리 실패.
### Root Cause
워크플로우 분기 누락.
### Action Items
1. 승인 단계 강제.
2. 상태 머신 검증 추가.

---

## 84. Refund Created Without Original Transaction
---
service: refund-service
error_message: original transaction not found
---
### Incident Summary
원거래 없는 환불 생성 시도.
### Root Cause
참조키 변조/오류.
### Action Items
1. 원거래 참조 검증 강화.
2. 감사 로그 기록.

---

## 85. Duplicate Cashback Reversal
---
service: cashback-service
error_message: duplicate reversal
---
### Incident Summary
캐시백 회수가 중복 반영됨.
### Root Cause
중복 이벤트 처리.
### Action Items
1. reversal_id 멱등 처리.
2. 회수 이력 유니크 제약.

---

## 86. Account Freeze Not Enforced Immediately
---
service: risk-service
error_message: freeze enforcement delayed
---
### Incident Summary
계정 동결이 즉시 반영되지 않음.
### Root Cause
캐시/전파 지연.
### Action Items
1. 강제 차단 경로 제공.
2. 전파 이벤트 우선순위 상향.

---

## 87. Limit Service Cache Corrupted
---
service: limit-service
error_message: limit cache corrupted
---
### Incident Summary
한도 캐시 손상으로 검증 오류.
### Root Cause
동시 업데이트 경쟁 조건.
### Action Items
1. 원자적 업데이트 적용.
2. 캐시 재구축 배치.

---

## 88. Wallet Top-up Posted Twice
---
service: wallet-service
error_message: topup posted twice
---
### Incident Summary
충전이 중복 반영됨.
### Root Cause
콜백 중복 처리.
### Action Items
1. topup_ref 멱등 처리.
2. 유니크 제약 적용.

---

## 89. Wallet Top-up Posted But Not Visible
---
service: wallet-service
error_message: topup not visible
---
### Incident Summary
충전은 기록됐지만 사용자 화면에 반영되지 않음.
### Root Cause
조회용 읽기 모델 지연.
### Action Items
1. 읽기 모델 리빌드.
2. eventual consistency 안내.

---

## 90. Order Search Index Stale
---
service: search-service
error_message: stale index
---
### Incident Summary
주문 검색 결과가 최신과 불일치.
### Root Cause
색인 파이프라인 지연.
### Action Items
1. 색인 워커 확장.
2. 색인 지연 알림.

---

## 91. Analytics Event Lost
---
service: analytics-service
error_message: analytics event lost
---
### Incident Summary
분석 이벤트 일부 유실.
### Root Cause
버퍼 플러시 실패.
### Action Items
1. 내구성 있는 큐로 전송.
2. 재전송 로직 추가.

---

## 92. Analytics Event Duplicated
---
service: analytics-service
error_message: analytics event duplicated
---
### Incident Summary
분석 이벤트 중복 적재.
### Root Cause
재시도 멱등성 미보장.
### Action Items
1. event_id 기반 dedupe.
2. 적재 유니크 키 적용.

---

## 93. Customer Statement Export Delayed
---
service: statement-service
error_message: export delayed
---
### Incident Summary
내역서/거래내역 다운로드 지연.
### Root Cause
대량 생성 요청 집중.
### Action Items
1. 비동기 생성 + 알림 제공.
2. 워커 스케일 아웃.

---

## 94. Compliance Report Missing Records
---
service: compliance-service
error_message: missing records in report
---
### Incident Summary
컴플라이언스 리포트에 일부 거래 누락.
### Root Cause
필터/조인 조건 오류.
### Action Items
1. 리포트 쿼리 검증.
2. 샘플링 검수 자동화.

---

## 95. KYC Document Status Outdated
---
service: kyc-service
error_message: document status outdated
---
### Incident Summary
서류 상태가 최신으로 갱신되지 않음.
### Root Cause
외부 검증 결과 반영 지연.
### Action Items
1. 상태 조회 배치 추가.
2. 콜백 재처리 큐 운영.

---

## 96. Merchant Fee Tier Misapplied
---
service: merchant-service
error_message: fee tier mismatch
---
### Incident Summary
가맹점 수수료 티어가 잘못 적용됨.
### Root Cause
티어 산정 기준 변경 미반영.
### Action Items
1. 티어 계산 버전 관리.
2. 정산 전 검증 배치.

---

## 97. Partner Integration Contract Drift
---
service: partner-integration
error_message: contract drift
---
### Incident Summary
파트너 연동 스펙 불일치로 실패 증가.
### Root Cause
스펙 변경 공유 누락.
### Action Items
1. 계약 테스트 도입.
2. 스펙 버전 관리.

---

## 98. Microservice Timeouts Cascade
---
service: gateway
error_message: cascading timeouts
---
### Incident Summary
일부 서비스 지연이 연쇄 타임아웃으로 확산.
### Root Cause
타임아웃/재시도 설정 불균형.
### Action Items
1. 타임아웃 계층 설계.
2. 재시도 예산(retry budget) 적용.

---

## 99. Bulk Import Creates Partial Inconsistency
---
service: admin-import
error_message: partial import inconsistency
---
### Incident Summary
대량 등록 중 일부만 반영되어 데이터 불일치.
### Root Cause
부분 실패 시 롤백/보상 미흡.
### Action Items
1. 배치 단위 트랜잭션/보상 설계.
2. 검증 및 재처리 워크플로우 추가.

---

## 100. Analytics Pipeline Delay
---
service: analytics-worker
error_message: process delay exceeds 60 minutes
---
### Incident Summary
통계 집계 파이프라인이 예상보다 크게 지연됨.
### Root Cause
전일 대비 데이터량 급증으로 워커 처리 한계 초과.
### Action Items
1. 워커 리소스(CPU/Mem) 증설.
2. 데이터 파티셔닝 및 분할 처리 점검.

---
