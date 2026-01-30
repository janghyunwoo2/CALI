# CALI Knowledge Base – Fintech Payment & PG (01–50)

---

## 01. PG API Key Expired
---
service: payment-api
error_message: Unauthorized - Invalid or expired API Key
---
### Incident Summary
결제 요청 시 PG 인증 실패 발생.
### Root Cause
PG 콘솔에서 API Key 갱신 누락.
### Action Items
1. Secrets Manager에 신규 API Key 반영.
2. 키 만료 알림 프로세스 구축.

---

## 02. Payment Gateway Timeout
---
service: payment-api
error_message: request timeout
---
### Incident Summary
결제 승인 요청이 타임아웃 발생.
### Root Cause
PG 서버 응답 지연.
### Action Items
1. 타임아웃 재시도 로직 적용.
2. PG SLA 모니터링 강화.

---

## 03. Duplicate Payment Request
---
service: payment-api
error_message: duplicate transaction detected
---
### Incident Summary
중복 결제 요청이 감지됨.
### Root Cause
클라이언트 중복 클릭 또는 네트워크 재시도.
### Action Items
1. Idempotency Key 검증 강화.
2. 중복 요청 차단 로직 점검.

---

## 04. Payment 승인 성공 후 응답 유실
---
service: payment-api
error_message: response not received
---
### Incident Summary
PG 승인 성공했으나 응답 수신 실패.
### Root Cause
네트워크 단절.
### Action Items
1. 승인 결과 조회 API 활용.
2. 결제 상태 재확인 배치 추가.

---

## 05. Double Charge Detected
---
service: payment-api
error_message: double charge detected
---
### Incident Summary
하나의 주문에 두 번 결제 발생.
### Root Cause
멱등성 키 미적용.
### Action Items
1. 주문 단위 멱등성 보장.
2. 사후 중복 결제 환불 프로세스 실행.

---

## 06. PG Webhook Signature Verification Failed
---
service: payment-webhook
error_message: invalid webhook signature
---
### Incident Summary
PG 웹훅 검증 실패로 결제 상태 반영 불가.
### Root Cause
시크릿 키 불일치.
### Action Items
1. Webhook Secret 재설정.
2. 서명 검증 로직 점검.

---

## 07. Payment Status Inconsistency
---
service: payment-api
error_message: payment status mismatch
---
### Incident Summary
PG와 내부 결제 상태 불일치.
### Root Cause
웹훅 처리 지연.
### Action Items
1. 주기적 상태 동기화 배치 실행.
2. 상태 전이 로그 강화.

---

## 08. PG Rate Limit Exceeded
---
service: payment-api
error_message: rate limit exceeded
---
### Incident Summary
결제 요청이 PG 제한 초과로 차단됨.
### Root Cause
대량 트래픽 유입.
### Action Items
1. 요청 큐잉 적용.
2. PG 한도 증설 요청.

---

## 09. Card BIN Validation Failed
---
service: payment-api
error_message: invalid card bin
---
### Incident Summary
카드 BIN 검증 실패로 결제 거절.
### Root Cause
BIN 데이터 최신화 누락.
### Action Items
1. BIN 데이터 업데이트.
2. fallback 검증 로직 적용.

---

## 10. Payment Amount Tampering Detected
---
service: payment-api
error_message: amount mismatch detected
---
### Incident Summary
결제 금액 위변조 감지.
### Root Cause
클라이언트 금액 신뢰.
### Action Items
1. 서버 계산 금액 기준 적용.
2. 요청 서명 검증 강화.

---

## 11. PG Certificate Expired
---
service: payment-api
error_message: SSL certificate expired
---
### Incident Summary
PG 통신 중 SSL 오류 발생.
### Root Cause
인증서 갱신 실패.
### Action Items
1. 인증서 갱신.
2. 만료 모니터링 설정.

---

## 12. Payment Authorization Declined
---
service: payment-api
error_message: authorization declined
---
### Incident Summary
결제 승인 거절 증가.
### Root Cause
카드사 정책 또는 한도 초과.
### Action Items
1. 사용자 안내 메시지 개선.
2. 대체 결제 수단 제공.

---

## 13. PG Maintenance Window Impact
---
service: payment-api
error_message: service unavailable
---
### Incident Summary
PG 점검 시간 동안 결제 불가.
### Root Cause
사전 점검 공지 미반영.
### Action Items
1. PG 점검 캘린더 반영.
2. 결제 차단/우회 처리.

---

## 14. Partial Capture Failed
---
service: payment-api
error_message: partial capture failed
---
### Incident Summary
부분 취소/캡처 실패.
### Root Cause
PG 정책 미지원.
### Action Items
1. PG 기능 지원 여부 확인.
2. 전액 취소 후 재결제 안내.

---

## 15. Payment Retry Storm
---
service: payment-api
error_message: excessive retries detected
---
### Incident Summary
결제 재시도 폭증.
### Root Cause
클라이언트 무한 재시도.
### Action Items
1. Retry 횟수 제한.
2. 지수 백오프 적용.

---

## 16. Foreign Currency Conversion Error
---
service: payment-api
error_message: currency conversion failed
---
### Incident Summary
환율 적용 실패로 결제 중단.
### Root Cause
환율 API 장애.
### Action Items
1. 캐시 환율 적용.
2. 환율 API 이중화.

---

## 17. PG Callback URL Unreachable
---
service: payment-webhook
error_message: callback url unreachable
---
### Incident Summary
PG가 콜백 전송 실패.
### Root Cause
방화벽 또는 DNS 오류.
### Action Items
1. 외부 접근 허용 확인.
2. 헬스체크 엔드포인트 제공.

---

## 18. Payment Order ID Collision
---
service: payment-api
error_message: duplicate order id
---
### Incident Summary
주문 ID 충돌 발생.
### Root Cause
ID 생성 규칙 중복.
### Action Items
1. UUID 기반 주문 ID 적용.
2. 중복 검증 로직 추가.

---

## 19. Settlement Batch Delay
---
service: settlement
error_message: settlement delay
---
### Incident Summary
정산 배치 지연 발생.
### Root Cause
결제 데이터 급증.
### Action Items
1. 배치 분산 처리.
2. 워커 확장.

---

## 20. PG Fraud Detection Triggered
---
service: payment-api
error_message: fraud suspected
---
### Incident Summary
PG 부정 결제 탐지로 차단.
### Root Cause
비정상 결제 패턴.
### Action Items
1. 사용자 추가 인증.
2. 내부 FDS 룰 검토.

---

## 21. Payment Currency Mismatch
---
service: payment-api
error_message: currency mismatch
---
### Incident Summary
통화 불일치로 결제 실패.
### Root Cause
주문 통화와 결제 통화 불일치.
### Action Items
1. 통화 검증 강화.
2. UI 통화 표시 통일.

---

## 22. PG Response Code Mapping Error
---
service: payment-api
error_message: unknown response code
---
### Incident Summary
PG 응답 코드 해석 실패.
### Root Cause
신규 코드 미반영.
### Action Items
1. 응답 코드 매핑 업데이트.
2. 기본 처리 로직 추가.

---

## 23. Payment Cancel Timeout
---
service: payment-api
error_message: cancel timeout
---
### Incident Summary
결제 취소 요청 타임아웃.
### Root Cause
PG 취소 API 지연.
### Action Items
1. 취소 상태 조회 배치.
2. 사용자 안내 강화.

---

## 24. Zero Amount Authorization Error
---
service: payment-api
error_message: invalid zero amount auth
---
### Incident Summary
0원 승인 실패.
### Root Cause
PG 정책 제한.
### Action Items
1. 최소 금액 승인 적용.
2. PG 정책 문서 확인.

---

## 25. Payment Metadata Lost
---
service: payment-api
error_message: metadata missing
---
### Incident Summary
결제 부가 정보 유실.
### Root Cause
중간 변환 과정 손실.
### Action Items
1. 메타데이터 스키마 고정.
2. 로깅 강화.

---

## 26. PG Sandbox Production Mix-up
---
service: payment-api
error_message: invalid environment
---
### Incident Summary
샌드박스/운영 환경 혼용.
### Root Cause
환경 변수 설정 오류.
### Action Items
1. 환경별 키 분리.
2. 배포 전 검증 강화.

---

## 27. Payment Webhook Duplicate Delivery
---
service: payment-webhook
error_message: duplicate webhook received
---
### Incident Summary
웹훅 중복 수신.
### Root Cause
PG 재전송 정책.
### Action Items
1. 웹훅 멱등성 처리.
2. 이벤트 ID 기반 중복 제거.

---

## 28. PG Latency Spike During Peak
---
service: payment-api
error_message: latency spike
---
### Incident Summary
피크 시간대 PG 응답 지연.
### Root Cause
PG 처리량 한계.
### Action Items
1. 결제 큐 적용.
2. 멀티 PG 전략 검토.

---

## 29. Payment State Machine Invalid Transition
---
service: payment-api
error_message: invalid state transition
---
### Incident Summary
결제 상태 전이 오류.
### Root Cause
비동기 이벤트 순서 꼬임.
### Action Items
1. 상태 전이 검증 추가.
2. 이벤트 순서 보장.

---

## 30. PG Refund Limit Exceeded
---
service: payment-api
error_message: refund limit exceeded
---
### Incident Summary
환불 한도 초과로 처리 실패.
### Root Cause
PG 정책 제한.
### Action Items
1. 분할 환불 적용.
2. 고객센터 처리 전환.

---

## 31. Payment Tokenization Failed
---
service: payment-api
error_message: tokenization failed
---
### Incident Summary
카드 토큰화 실패.
### Root Cause
PG 토큰 서비스 장애.
### Action Items
1. 재시도 로직 추가.
2. 대체 PG 사용 검토.

---

## 32. PG Network Whitelist Missing
---
service: payment-api
error_message: ip not allowed
---
### Incident Summary
PG IP 화이트리스트 누락.
### Root Cause
IP 변경 미반영.
### Action Items
1. 최신 IP 반영.
2. 자동 동기화 검토.

---

## 33. Payment Order Expired
---
service: payment-api
error_message: order expired
---
### Incident Summary
결제 대기 중 주문 만료.
### Root Cause
결제 지연.
### Action Items
1. 만료 시간 연장.
2. 사용자 재시도 유도.

---

## 34. PG Maintenance Fallback Failed
---
service: payment-api
error_message: fallback failed
---
### Incident Summary
대체 결제 경로 실패.
### Root Cause
Fallback 로직 미구현.
### Action Items
1. 멀티 PG 라우팅 구현.
2. 장애 전환 테스트.

---

## 35. Payment Capture Amount Mismatch
---
service: payment-api
error_message: capture amount mismatch
---
### Incident Summary
캡처 금액 불일치.
### Root Cause
부분 캡처 로직 오류.
### Action Items
1. 금액 검증 강화.
2. 캡처 로직 수정.

---

## 36. PG API Version Deprecated
---
service: payment-api
error_message: api version deprecated
---
### Incident Summary
구버전 PG API 호출.
### Root Cause
업데이트 미적용.
### Action Items
1. API 버전 업그레이드.
2. 변경 사항 검토.

---

## 37. Payment Reconciliation Failed
---
service: settlement
error_message: reconciliation mismatch
---
### Incident Summary
PG 정산 데이터 불일치.
### Root Cause
정산 기준 차이.
### Action Items
1. 정산 로직 검증.
2. 차이 리포트 생성.

---

## 38. PG Fraud False Positive
---
service: payment-api
error_message: false fraud detection
---
### Incident Summary
정상 결제가 부정 결제로 차단.
### Root Cause
과도한 FDS 룰.
### Action Items
1. 룰 튜닝.
2. 사용자 인증 보완.

---

## 39. Payment Callback Processing Lag
---
service: payment-webhook
error_message: callback processing delayed
---
### Incident Summary
콜백 처리 지연으로 상태 반영 늦어짐.
### Root Cause
웹훅 큐 적체.
### Action Items
1. 소비자 확장.
2. 비동기 처리 최적화.

---

## 40. PG Amount Precision Error
---
service: payment-api
error_message: amount precision error
---
### Incident Summary
소수점 처리 오류.
### Root Cause
통화별 소수점 규칙 미반영.
### Action Items
1. 통화별 정밀도 적용.
2. 금액 계산 표준화.

---

## 41. Payment Retry After Success
---
service: payment-api
error_message: retry after success
---
### Incident Summary
성공 후 재시도 발생.
### Root Cause
클라이언트 응답 미수신.
### Action Items
1. 상태 조회 기반 처리.
2. 중복 차단 강화.

---

## 42. PG Webhook Order Not Found
---
service: payment-webhook
error_message: order not found
---
### Incident Summary
웹훅 수신 시 주문 미존재.
### Root Cause
주문 생성 지연.
### Action Items
1. 재시도 큐잉.
2. 순서 보장 처리.

---

## 43. Payment Settlement Currency Drift
---
service: settlement
error_message: settlement currency mismatch
---
### Incident Summary
정산 통화 불일치.
### Root Cause
환율 기준 시점 차이.
### Action Items
1. 환율 기준 고정.
2. 정산 로직 정비.

---

## 44. PG Fraud List Sync Failed
---
service: payment-api
error_message: fraud list sync failed
---
### Incident Summary
부정 목록 동기화 실패.
### Root Cause
외부 API 장애.
### Action Items
1. 캐시 사용.
2. 재동기화 배치.

---

## 45. Payment Refund Webhook Missing
---
service: payment-webhook
error_message: refund webhook missing
---
### Incident Summary
환불 웹훅 미수신.
### Root Cause
PG 이벤트 누락.
### Action Items
1. 환불 상태 조회 배치.
2. PG 문의.

---

## 46. PG Transaction ID Format Changed
---
service: payment-api
error_message: invalid transaction id format
---
### Incident Summary
트랜잭션 ID 포맷 변경.
### Root Cause
PG 스펙 변경 미인지.
### Action Items
1. 파서 수정.
2. 스펙 변경 모니터링.

---

## 47. Payment Daily Limit Exceeded
---
service: payment-api
error_message: daily limit exceeded
---
### Incident Summary
일일 결제 한도 초과.
### Root Cause
사용자 한도 도달.
### Action Items
1. 한도 안내.
2. 한도 상향 프로세스 제공.

---

## 48. PG Callback Replay Attack Attempt
---
service: payment-webhook
error_message: replay detected
---
### Incident Summary
웹훅 재전송 공격 시도 감지.
### Root Cause
타임스탬프 검증 미흡.
### Action Items
1. 타임스탬프/Nonce 검증.
2. 서명 검증 강화.

---

## 49. Payment Order State Stuck
---
service: payment-api
error_message: order state stuck
---
### Incident Summary
결제 상태가 중간 단계에 고정됨.
### Root Cause
이벤트 유실.
### Action Items
1. 상태 복구 배치 실행.
2. 상태 전이 보정.

---

## 50. PG Service Region Outage
---
service: payment-api
error_message: regional outage
---
### Incident Summary
특정 리전 PG 장애로 결제 불가.
### Root Cause
PG 리전 장애.
### Action Items
1. 멀티 리전 라우팅.
2. 장애 공지 및 우회 처리.

---
## 51. Payment Capture Timeout
---
service: payment-api
error_message: capture timeout
---
### Incident Summary
결제 승인 후 캡처 요청이 타임아웃 발생.
### Root Cause
PG 캡처 API 응답 지연.
### Action Items
1. 캡처 재시도 로직 추가.
2. 캡처 상태 조회 배치 실행.

---

## 52. PG Settlement File Missing
---
service: settlement
error_message: settlement file not found
---
### Incident Summary
정산 파일 미수신으로 정산 지연 발생.
### Root Cause
PG 정산 파일 전송 실패.
### Action Items
1. 재전송 요청.
2. 파일 수신 모니터링 강화.

---

## 53. Payment Authorization Reversed
---
service: payment-api
error_message: authorization reversed
---
### Incident Summary
승인된 결제가 카드사에 의해 취소됨.
### Root Cause
카드사 리스크 판단.
### Action Items
1. 사용자 알림.
2. 대체 결제 수단 안내.

---

## 54. PG Callback Payload Schema Changed
---
service: payment-webhook
error_message: invalid callback payload
---
### Incident Summary
웹훅 페이로드 파싱 실패.
### Root Cause
PG 콜백 스키마 변경.
### Action Items
1. 스키마 버전 대응.
2. 하위 호환 파서 추가.

---

## 55. Payment Partial Refund Amount Mismatch
---
service: payment-api
error_message: partial refund amount mismatch
---
### Incident Summary
부분 환불 금액 불일치.
### Root Cause
환불 계산 로직 오류.
### Action Items
1. 환불 금액 검증 강화.
2. 환불 로직 수정.

---

## 56. PG Batch Approval Delay
---
service: payment-api
error_message: batch approval delayed
---
### Incident Summary
배치 승인 처리 지연.
### Root Cause
PG 배치 큐 적체.
### Action Items
1. 배치 분산 처리.
2. 처리 시간 모니터링.

---

## 57. Payment Authorization Retry After Decline
---
service: payment-api
error_message: retry after decline
---
### Incident Summary
거절된 결제에 대한 반복 승인 시도.
### Root Cause
클라이언트 재시도 정책 오류.
### Action Items
1. 거절 사유별 재시도 제한.
2. 사용자 안내 개선.

---

## 58. PG Webhook Ordering Violation
---
service: payment-webhook
error_message: webhook out of order
---
### Incident Summary
웹훅 이벤트 순서 뒤바뀜.
### Root Cause
PG 비동기 전송 특성.
### Action Items
1. 이벤트 시퀀스 검증.
2. 상태 전이 보정 로직 추가.

---

## 59. Payment Merchant ID Mismatch
---
service: payment-api
error_message: merchant id mismatch
---
### Incident Summary
상점 ID 불일치로 결제 실패.
### Root Cause
환경별 상점 ID 설정 오류.
### Action Items
1. 환경 변수 검증.
2. 배포 전 설정 체크 추가.

---

## 60. PG Fraud Score Threshold Updated
---
service: payment-api
error_message: fraud score exceeded
---
### Incident Summary
부정 점수 기준 변경으로 승인 실패 증가.
### Root Cause
PG 정책 변경.
### Action Items
1. 임계값 재조정.
2. 사용자 인증 단계 추가.

---

## 61. Payment Installment Plan Not Supported
---
service: payment-api
error_message: installment not supported
---
### Incident Summary
할부 결제 미지원으로 실패.
### Root Cause
PG/카드사 정책 제한.
### Action Items
1. 지원 카드 목록 안내.
2. 단일 결제 유도.

---

## 62. PG Settlement Amount Rounding Error
---
service: settlement
error_message: rounding error detected
---
### Incident Summary
정산 금액 반올림 오류.
### Root Cause
소수점 처리 규칙 불일치.
### Action Items
1. 반올림 규칙 통일.
2. 정산 검증 로직 추가.

---

## 63. Payment Order Locked
---
service: payment-api
error_message: order locked
---
### Incident Summary
결제 주문이 잠겨 처리 불가.
### Root Cause
이전 트랜잭션 미종료.
### Action Items
1. 락 해제 배치 실행.
2. 락 타임아웃 설정.

---

## 64. PG Token Expired
---
service: payment-api
error_message: token expired
---
### Incident Summary
PG 액세스 토큰 만료.
### Root Cause
토큰 갱신 실패.
### Action Items
1. 자동 갱신 로직 보완.
2. 토큰 만료 알림 추가.

---

## 65. Payment Chargeback Received
---
service: settlement
error_message: chargeback received
---
### Incident Summary
차지백 접수로 분쟁 발생.
### Root Cause
카드사 고객 이의 제기.
### Action Items
1. 증빙 자료 제출.
2. 차지백 대응 프로세스 실행.

---

## 66. PG Fraud Rule Sync Delay
---
service: payment-api
error_message: fraud rule sync delayed
---
### Incident Summary
부정 결제 룰 동기화 지연.
### Root Cause
외부 FDS API 지연.
### Action Items
1. 캐시 룰 적용.
2. 동기화 재시도.

---

## 67. Payment Cancel After Capture
---
service: payment-api
error_message: cancel after capture not allowed
---
### Incident Summary
캡처 이후 취소 요청 실패.
### Root Cause
PG 정책 제한.
### Action Items
1. 환불 프로세스 전환.
2. 사용자 안내 강화.

---

## 68. PG Webhook IP Changed
---
service: payment-webhook
error_message: ip not recognized
---
### Incident Summary
웹훅 송신 IP 변경으로 차단.
### Root Cause
PG IP 변경 공지 미확인.
### Action Items
1. 최신 IP 화이트리스트 반영.
2. 자동 동기화 검토.

---

## 69. Payment Duplicate Refund
---
service: payment-api
error_message: duplicate refund detected
---
### Incident Summary
중복 환불 요청 감지.
### Root Cause
환불 멱등성 미적용.
### Action Items
1. 환불 멱등성 키 적용.
2. 중복 요청 차단.

---

## 70. PG Payment Method Disabled
---
service: payment-api
error_message: payment method disabled
---
### Incident Summary
특정 결제 수단 비활성화로 실패.
### Root Cause
PG 정책 또는 점검.
### Action Items
1. 결제 수단 상태 확인.
2. 대체 수단 제공.

---

## 71. Payment Order Amount Updated Mid-Flow
---
service: payment-api
error_message: order amount changed
---
### Incident Summary
결제 진행 중 주문 금액 변경 감지.
### Root Cause
동시 수정.
### Action Items
1. 결제 중 금액 변경 제한.
2. 주문 락 적용.

---

## 72. PG Settlement Currency Rate Missing
---
service: settlement
error_message: exchange rate missing
---
### Incident Summary
정산 환율 데이터 누락.
### Root Cause
환율 소스 장애.
### Action Items
1. 환율 캐시 적용.
2. 대체 환율 소스 사용.

---

## 73. Payment Authorization Window Expired
---
service: payment-api
error_message: authorization expired
---
### Incident Summary
승인 유효 기간 만료.
### Root Cause
캡처 지연.
### Action Items
1. 캡처 SLA 단축.
2. 자동 재승인 검토.

---

## 74. PG Callback Signature Algorithm Changed
---
service: payment-webhook
error_message: unsupported signature algorithm
---
### Incident Summary
웹훅 서명 알고리즘 변경으로 검증 실패.
### Root Cause
PG 보안 스펙 변경.
### Action Items
1. 알고리즘 대응.
2. 버전별 검증 로직 추가.

---

## 75. Payment Merchant Category Code Invalid
---
service: payment-api
error_message: invalid mcc
---
### Incident Summary
MCC 오류로 결제 거절.
### Root Cause
상점 코드 설정 오류.
### Action Items
1. MCC 재설정.
2. PG 콘솔 설정 확인.

---

## 76. PG Settlement Duplicate Record
---
service: settlement
error_message: duplicate settlement record
---
### Incident Summary
정산 데이터 중복 수신.
### Root Cause
파일 재전송.
### Action Items
1. 정산 멱등성 처리.
2. 중복 제거 배치.

---

## 77. Payment Callback Processing Error
---
service: payment-webhook
error_message: callback processing error
---
### Incident Summary
웹훅 처리 중 내부 오류 발생.
### Root Cause
파싱 예외 미처리.
### Action Items
1. 예외 처리 강화.
2. 실패 이벤트 재처리 큐 추가.

---

## 78. PG Multi-Currency Settlement Delay
---
service: settlement
error_message: multi-currency settlement delayed
---
### Incident Summary
다중 통화 정산 지연.
### Root Cause
환전 처리 지연.
### Action Items
1. 통화별 배치 분리.
2. 처리 순서 최적화.

---

## 79. Payment Excessive Authorization Holds
---
service: payment-api
error_message: excessive authorization holds
---
### Incident Summary
승인 보류가 과도하게 누적됨.
### Root Cause
캡처/취소 지연.
### Action Items
1. 승인 보류 정리 배치.
2. 처리 SLA 개선.

---

## 80. PG Payment Window Redirect Failed
---
service: payment-api
error_message: redirect failed
---
### Incident Summary
결제창 리다이렉트 실패.
### Root Cause
URL 파라미터 오류.
### Action Items
1. 리다이렉트 URL 검증.
2. 인코딩 점검.

---

## 81. Payment Order Status Overwritten
---
service: payment-api
error_message: status overwritten
---
### Incident Summary
결제 상태가 덮어써짐.
### Root Cause
동시 이벤트 처리.
### Action Items
1. 상태 전이 조건 강화.
2. 버전 기반 업데이트 적용.

---

## 82. PG Reconciliation File Format Changed
---
service: settlement
error_message: invalid reconciliation format
---
### Incident Summary
대사 파일 포맷 변경으로 처리 실패.
### Root Cause
PG 포맷 변경 미대응.
### Action Items
1. 포맷 버전 분기 처리.
2. 사전 변경 감지.

---

## 83. Payment Refund SLA Breached
---
service: settlement
error_message: refund sla breached
---
### Incident Summary
환불 처리 SLA 초과.
### Root Cause
환불 큐 적체.
### Action Items
1. 환불 워커 확장.
2. 우선순위 처리.

---

## 84. PG Authorization Hold Release Failed
---
service: payment-api
error_message: hold release failed
---
### Incident Summary
승인 보류 해제 실패.
### Root Cause
PG API 오류.
### Action Items
1. 재시도 처리.
2. 수동 해제 프로세스 준비.

---

## 85. Payment Card Network Outage
---
service: payment-api
error_message: card network unavailable
---
### Incident Summary
카드 네트워크 장애로 결제 실패.
### Root Cause
외부 네트워크 장애.
### Action Items
1. 장애 공지.
2. 대체 결제 수단 안내.

---

## 86. PG Callback Retry Storm
---
service: payment-webhook
error_message: excessive callback retries
---
### Incident Summary
웹훅 재시도 폭증.
### Root Cause
엔드포인트 응답 실패.
### Action Items
1. 빠른 ACK 처리.
2. 비동기 후처리.

---

## 87. Payment Order Reference Truncated
---
service: payment-api
error_message: reference truncated
---
### Incident Summary
주문 참조값이 잘려 전달됨.
### Root Cause
필드 길이 제한.
### Action Items
1. 길이 제한 준수.
2. 참조 필드 축약 규칙 정의.

---

## 88. PG Risk Review Pending
---
service: payment-api
error_message: risk review pending
---
### Incident Summary
리스크 심사 대기 상태 장기화.
### Root Cause
수동 심사 지연.
### Action Items
1. 자동 승인 조건 확대.
2. 사용자 안내.

---

## 89. Payment Settlement Cutoff Missed
---
service: settlement
error_message: settlement cutoff missed
---
### Incident Summary
정산 컷오프 미준수.
### Root Cause
배치 지연.
### Action Items
1. 컷오프 알림 설정.
2. 배치 스케줄 조정.

---

## 90. PG Callback Payload Size Exceeded
---
service: payment-webhook
error_message: payload too large
---
### Incident Summary
웹훅 페이로드 크기 초과.
### Root Cause
과도한 메타데이터 포함.
### Action Items
1. 필드 최소화.
2. 대용량 데이터 별도 조회.

---

## 91. Payment Manual Override Error
---
service: settlement
error_message: manual override failed
---
### Incident Summary
수동 정정 처리 실패.
### Root Cause
권한 부족.
### Action Items
1. 권한 점검.
2. 승인 프로세스 정비.

---

## 92. PG Authorization Window Policy Changed
---
service: payment-api
error_message: auth window changed
---
### Incident Summary
승인 유효 기간 정책 변경.
### Root Cause
PG 정책 업데이트.
### Action Items
1. 캡처 타이밍 조정.
2. 정책 변경 모니터링.

---

## 93. Payment Settlement Data Late Arrival
---
service: settlement
error_message: late settlement data
---
### Incident Summary
정산 데이터 지연 도착.
### Root Cause
PG 배치 지연.
### Action Items
1. 지연 허용 로직 추가.
2. 재정산 배치.

---

## 94. PG Callback Duplicate Event ID
---
service: payment-webhook
error_message: duplicate event id
---
### Incident Summary
웹훅 이벤트 ID 중복.
### Root Cause
PG 재전송.
### Action Items
1. 이벤트 ID 멱등성 처리.
2. 중복 로그 기록.

---

## 95. Payment Chargeback Evidence Deadline Missed
---
service: settlement
error_message: chargeback deadline missed
---
### Incident Summary
차지백 대응 기한 초과.
### Root Cause
알림 누락.
### Action Items
1. 기한 알림 자동화.
2. 책임자 지정.

---

## 96. PG Transaction Reference Collision
---
service: payment-api
error_message: transaction reference collision
---
### Incident Summary
트랜잭션 참조값 충돌.
### Root Cause
참조 생성 규칙 단순.
### Action Items
1. 참조값 고유성 강화.
2. UUID 적용.

---

## 97. Payment Settlement Tax Calculation Error
---
service: settlement
error_message: tax calculation error
---
### Incident Summary
정산 세금 계산 오류.
### Root Cause
세율 변경 미반영.
### Action Items
1. 세율 업데이트.
2. 계산 로직 검증.

---

## 98. PG Callback Endpoint Rate Limited
---
service: payment-webhook
error_message: rate limited
---
### Incident Summary
웹훅 엔드포인트 호출 제한.
### Root Cause
응답 지연으로 재시도 증가.
### Action Items
1. 응답 속도 개선.
2. Rate Limit 완화.

---

## 99. Payment Order Archive Failed
---
service: payment-api
error_message: archive failed
---
### Incident Summary
결제 주문 아카이빙 실패.
### Root Cause
스토리지 오류.
### Action Items
1. 스토리지 점검.
2. 재처리 배치 실행.

---

## 100. PG End-of-Day Settlement Mismatch
---
service: settlement
error_message: eod settlement mismatch
---
### Incident Summary
일마감 정산 불일치 발생.
### Root Cause
컷오프 기준 차이.
### Action Items
1. 컷오프 기준 통일.
2. 일마감 검증 리포트 생성.

---
