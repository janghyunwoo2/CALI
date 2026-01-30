---
service: auth-service
error_message: High rate of JWT validation failures
---

## Incident Summary
Security Alert - [INC-1BDBD] High rate of JWT validation failures from IP 178.179.138.23.

## Root Cause
특정 IP(178.179.138.23)에서의 Brute Force(무차별 대입) 공격 시도 감지됨.

## Action Items
1. AWS WAF 또는 Security Group에서 해당 공격자 IP(178.179.138.23) 즉시 차단.
2. `Fail2Ban` 정책 활성화 여부 확인.
3. 공격 대상 계정에 대해 임시 잠금 조치 및 비밀번호 변경 안내 발송.


# CALI Knowledge Base – Fintech Auth & Security (01–100)

---

## 01. Abnormal Login Attempts Detected
---
service: auth-service
error_message: high rate of login failures
---
### Incident Summary
특정 계정에 대해 로그인 실패가 급증.
### Root Cause
무차별 대입 공격 시도.
### Action Items
1. 계정 임시 잠금.
2. 공격 IP 차단.

---

## 02. JWT Signature Verification Failed
---
service: auth-service
error_message: invalid jwt signature
---
### Incident Summary
JWT 서명 검증 실패로 인증 거부.
### Root Cause
Secret Key 불일치 또는 키 로테이션 미반영.
### Action Items
1. Secret Key 동기화.
2. 키 로테이션 프로세스 점검.

---

## 03. Access Token Expired
---
service: auth-service
error_message: token expired
---
### Incident Summary
만료된 액세스 토큰으로 요청 발생.
### Root Cause
클라이언트 토큰 갱신 실패.
### Action Items
1. Refresh Token 플로우 점검.
2. 만료 안내 개선.

---

## 04. Refresh Token Reuse Detected
---
service: auth-service
error_message: refresh token reuse detected
---
### Incident Summary
이미 사용된 Refresh Token 재사용 감지.
### Root Cause
토큰 탈취 가능성.
### Action Items
1. 세션 강제 종료.
2. 토큰 전면 폐기.

---

## 05. OAuth Redirect URI Mismatch
---
service: auth-service
error_message: redirect_uri_mismatch
---
### Incident Summary
OAuth 인증 리다이렉트 실패.
### Root Cause
등록되지 않은 Redirect URI 사용.
### Action Items
1. 허용 URI 목록 갱신.
2. 환경별 설정 분리.

---

## 06. CSRF Token Missing
---
service: gateway
error_message: csrf token missing
---
### Incident Summary
CSRF 토큰 누락으로 요청 차단.
### Root Cause
클라이언트 토큰 미전송.
### Action Items
1. CSRF 토큰 주입 로직 확인.
2. 예외 처리 점검.

---

## 07. CSRF Token Invalid
---
service: gateway
error_message: invalid csrf token
---
### Incident Summary
잘못된 CSRF 토큰 사용.
### Root Cause
토큰 만료 또는 세션 불일치.
### Action Items
1. 토큰 재발급.
2. 세션 동기화 점검.

---

## 08. XSS Attack Attempt Detected
---
service: web-firewall
error_message: xss pattern detected
---
### Incident Summary
스크립트 삽입 시도 감지.
### Root Cause
입력값 필터링 미흡.
### Action Items
1. 입력값 이스케이프 강화.
2. WAF 룰 업데이트.

---

## 09. SQL Injection Pattern Detected
---
service: web-firewall
error_message: sql injection detected
---
### Incident Summary
SQL 인젝션 공격 차단.
### Root Cause
취약한 쿼리 패턴 노출.
### Action Items
1. Prepared Statement 사용.
2. 입력 검증 강화.

---

## 10. Brute Force Protection Triggered
---
service: auth-service
error_message: brute force protection triggered
---
### Incident Summary
과도한 로그인 시도로 계정 차단.
### Root Cause
공격 또는 사용자 오입력.
### Action Items
1. CAPTCHA 적용.
2. 로그인 정책 조정.

---

## 11. Password Policy Violation
---
service: auth-service
error_message: password policy violation
---
### Incident Summary
비밀번호 정책 미충족.
### Root Cause
복잡도 부족.
### Action Items
1. 정책 안내 강화.
2. UI 검증 추가.

---

## 12. MFA Verification Failed
---
service: auth-service
error_message: mfa verification failed
---
### Incident Summary
다중 인증 실패.
### Root Cause
OTP 입력 오류 또는 시간 불일치.
### Action Items
1. 시간 동기화 점검.
2. 재시도 제한.

---

## 13. MFA Bypass Attempt Detected
---
service: auth-service
error_message: mfa bypass detected
---
### Incident Summary
MFA 우회 시도 감지.
### Root Cause
비정상 요청 패턴.
### Action Items
1. 계정 잠금.
2. 보안 알림 발송.

---

## 14. Account Enumeration Attempt
---
service: auth-service
error_message: account enumeration detected
---
### Incident Summary
계정 존재 여부 탐색 시도.
### Root Cause
오류 메시지 차별 노출.
### Action Items
1. 오류 메시지 통일.
2. 요청 제한 적용.

---

## 15. Session Fixation Detected
---
service: auth-service
error_message: session fixation attempt
---
### Incident Summary
세션 고정 공격 시도.
### Root Cause
로그인 후 세션 재발급 미흡.
### Action Items
1. 로그인 시 세션 재발급.
2. 세션 무효화 강화.

---

## 16. Session Hijacking Suspected
---
service: auth-service
error_message: session hijacking suspected
---
### Incident Summary
세션 탈취 의심 활동 감지.
### Root Cause
IP/User-Agent 변경.
### Action Items
1. 세션 강제 종료.
2. 재인증 요구.

---

## 17. SameSite Cookie Misconfigured
---
service: gateway
error_message: samesite cookie misconfigured
---
### Incident Summary
쿠키 SameSite 설정 오류.
### Root Cause
브라우저 정책 변경 미반영.
### Action Items
1. SameSite=None; Secure 적용.
2. 브라우저 호환성 점검.

---

## 18. Secure Cookie Flag Missing
---
service: gateway
error_message: insecure cookie detected
---
### Incident Summary
보안 쿠키 플래그 누락.
### Root Cause
환경 설정 오류.
### Action Items
1. Secure, HttpOnly 설정.
2. 설정 점검 자동화.

---

## 19. API Key Leaked
---
service: api-gateway
error_message: api key compromised
---
### Incident Summary
API Key 유출 의심.
### Root Cause
코드 또는 로그 노출.
### Action Items
1. 키 즉시 폐기.
2. 신규 키 발급.

---

## 20. API Key Permission Overbroad
---
service: api-gateway
error_message: api key scope too broad
---
### Incident Summary
API Key 권한 과다 부여.
### Root Cause
최소 권한 미적용.
### Action Items
1. Scope 축소.
2. 키 관리 정책 강화.

---

## 21. OAuth Token Scope Escalation
---
service: auth-service
error_message: scope escalation detected
---
### Incident Summary
권한 상승 토큰 요청 감지.
### Root Cause
검증 로직 미흡.
### Action Items
1. Scope 검증 강화.
2. 요청 로깅 추가.

---

## 22. OAuth State Parameter Missing
---
service: auth-service
error_message: missing state parameter
---
### Incident Summary
OAuth state 누락으로 요청 차단.
### Root Cause
CSRF 보호 미구현.
### Action Items
1. State 필수 적용.
2. 검증 로직 추가.

---

## 23. Token Audience Mismatch
---
service: auth-service
error_message: invalid token audience
---
### Incident Summary
토큰 대상 불일치.
### Root Cause
잘못된 서비스 호출.
### Action Items
1. Audience 검증.
2. 서비스 간 토큰 분리.

---

## 24. Token Issuer Mismatch
---
service: auth-service
error_message: invalid token issuer
---
### Incident Summary
발급자 불일치 토큰 사용.
### Root Cause
환경 혼용.
### Action Items
1. Issuer 고정.
2. 환경 분리.

---

## 25. Authorization Header Missing
---
service: gateway
error_message: authorization header missing
---
### Incident Summary
인증 헤더 누락.
### Root Cause
클라이언트 구현 오류.
### Action Items
1. 클라이언트 검증.
2. 명확한 에러 응답 제공.

---

## 26. Role Mapping Failed
---
service: auth-service
error_message: role mapping failed
---
### Incident Summary
사용자 권한 매핑 실패.
### Root Cause
권한 테이블 불일치.
### Action Items
1. 매핑 데이터 점검.
2. 기본 Role 설정.

---

## 27. RBAC Permission Denied
---
service: auth-service
error_message: permission denied
---
### Incident Summary
권한 부족으로 접근 거부.
### Root Cause
Role 설정 누락.
### Action Items
1. Role 할당 검증.
2. 접근 정책 리뷰.

---

## 28. Privilege Escalation Attempt
---
service: auth-service
error_message: privilege escalation detected
---
### Incident Summary
권한 상승 시도 감지.
### Root Cause
파라미터 변조.
### Action Items
1. 서버 권한 검증 강화.
2. 감사 로그 기록.

---

## 29. Rate Limit Exceeded (Auth)
---
service: auth-service
error_message: rate limit exceeded
---
### Incident Summary
인증 요청 한도 초과.
### Root Cause
공격 또는 비정상 클라이언트.
### Action Items
1. Rate Limit 정책 조정.
2. IP 차단.

---

## 30. Suspicious IP Geolocation Change
---
service: auth-service
error_message: suspicious login location
---
### Incident Summary
로그인 위치 급변 감지.
### Root Cause
VPN 또는 계정 탈취.
### Action Items
1. 추가 인증 요구.
2. 사용자 알림.

---

## 31. Password Reset Token Expired
---
service: auth-service
error_message: reset token expired
---
### Incident Summary
비밀번호 재설정 토큰 만료.
### Root Cause
지연된 사용자 처리.
### Action Items
1. 토큰 재발급.
2. 만료 안내 강화.

---

## 32. Password Reset Token Reuse
---
service: auth-service
error_message: reset token reuse detected
---
### Incident Summary
재설정 토큰 재사용 감지.
### Root Cause
토큰 관리 미흡.
### Action Items
1. 토큰 1회성 강제.
2. 로그 강화.

---

## 33. Email Verification Link Invalid
---
service: auth-service
error_message: invalid verification link
---
### Incident Summary
이메일 인증 실패.
### Root Cause
링크 만료 또는 변조.
### Action Items
1. 링크 재발급.
2. 만료 시간 조정.

---

## 34. Email Verification Flood
---
service: auth-service
error_message: verification flood detected
---
### Incident Summary
인증 메일 대량 발송 시도.
### Root Cause
자동화 공격.
### Action Items
1. 발송 제한.
2. CAPTCHA 적용.

---

## 35. Account Lockout Abuse
---
service: auth-service
error_message: lockout abuse detected
---
### Incident Summary
의도적 계정 잠금 유도 공격.
### Root Cause
로그인 실패 유도.
### Action Items
1. Lockout 정책 완화.
2. CAPTCHA 도입.

---

## 36. WAF Rule False Positive
---
service: web-firewall
error_message: false positive block
---
### Incident Summary
정상 요청 차단.
### Root Cause
과도한 WAF 룰.
### Action Items
1. 룰 튜닝.
2. 예외 경로 추가.

---

## 37. DDoS Mitigation Triggered
---
service: edge-security
error_message: ddos mitigation activated
---
### Incident Summary
대규모 트래픽 공격 감지.
### Root Cause
외부 공격.
### Action Items
1. 트래픽 차단 지속.
2. 원인 분석.

---

## 38. IP Whitelist Misconfiguration
---
service: api-gateway
error_message: ip not allowed
---
### Incident Summary
허용 IP 접근 실패.
### Root Cause
화이트리스트 설정 오류.
### Action Items
1. IP 목록 검증.
2. 자동 동기화.

---

## 39. Internal Admin Endpoint Exposed
---
service: gateway
error_message: admin endpoint exposed
---
### Incident Summary
관리자 API 외부 노출.
### Root Cause
라우팅 설정 오류.
### Action Items
1. 접근 제한.
2. 경로 재설계.

---

## 40. Secrets Manager Access Denied
---
service: security
error_message: access denied to secret
---
### Incident Summary
시크릿 접근 실패.
### Root Cause
IAM 권한 부족.
### Action Items
1. IAM 정책 점검.
2. 최소 권한 적용.

---

## 41. Secret Rotation Failed
---
service: security
error_message: secret rotation failed
---
### Incident Summary
시크릿 자동 로테이션 실패.
### Root Cause
권한 또는 스크립트 오류.
### Action Items
1. 로테이션 로그 분석.
2. 수동 갱신 수행.

---

## 42. Hardcoded Secret Detected
---
service: security
error_message: hardcoded secret found
---
### Incident Summary
코드 내 시크릿 하드코딩 감지.
### Root Cause
보안 가이드 미준수.
### Action Items
1. 시크릿 제거.
2. Secrets Manager 사용.

---

## 43. Encryption Key Mismatch
---
service: security
error_message: encryption key mismatch
---
### Incident Summary
암호화 키 불일치로 복호화 실패.
### Root Cause
키 버전 혼용.
### Action Items
1. 키 버전 통일.
2. 키 관리 프로세스 점검.

---

## 44. Data Encryption At Rest Disabled
---
service: security
error_message: encryption at rest disabled
---
### Incident Summary
저장 데이터 암호화 미적용.
### Root Cause
스토리지 설정 누락.
### Action Items
1. 암호화 활성화.
2. 설정 감사.

---

## 45. TLS Version Deprecated
---
service: gateway
error_message: deprecated tls version
---
### Incident Summary
구버전 TLS 사용.
### Root Cause
서버 설정 미갱신.
### Action Items
1. TLS 1.2+ 강제.
2. 보안 설정 업데이트.

---

## 46. Certificate Chain Incomplete
---
service: gateway
error_message: incomplete certificate chain
---
### Incident Summary
인증서 체인 오류.
### Root Cause
중간 인증서 누락.
### Action Items
1. 체인 재설정.
2. 인증서 검증 테스트.

---

## 47. Mutual TLS Handshake Failed
---
service: gateway
error_message: mtls handshake failed
---
### Incident Summary
mTLS 인증 실패.
### Root Cause
클라이언트 인증서 오류.
### Action Items
1. 인증서 재발급.
2. 신뢰 체인 점검.

---

## 48. Clock Skew Affects Token Validation
---
service: auth-service
error_message: token not yet valid
---
### Incident Summary
시간 불일치로 토큰 검증 실패.
### Root Cause
서버 시간 동기화 실패.
### Action Items
1. NTP 동기화.
2. 허용 오차 설정.

---

## 49. Audit Log Missing
---
service: security
error_message: audit log missing
---
### Incident Summary
보안 감사 로그 누락.
### Root Cause
로깅 설정 오류.
### Action Items
1. 감사 로그 강제 활성화.
2. 로그 무결성 검증.

---

## 50. Audit Log Tampering Suspected
---
service: security
error_message: audit log tampering detected
---
### Incident Summary
로그 위변조 의심.
### Root Cause
접근 통제 미흡.
### Action Items
1. 로그 접근 제한.
2. 무결성 체크 적용.

---

## 51. API Replay Attack Detected
---
service: api-gateway
error_message: replay attack detected
---
### Incident Summary
요청 재전송 공격 감지.
### Root Cause
Nonce 검증 미흡.
### Action Items
1. Nonce/타임스탬프 검증.
2. 요청 서명 강화.

---

## 52. Token Blacklist Not Applied
---
service: auth-service
error_message: revoked token accepted
---
### Incident Summary
폐기된 토큰 사용 가능 상태.
### Root Cause
블랙리스트 동기화 실패.
### Action Items
1. 블랙리스트 즉시 반영.
2. 캐시 무효화.

---

## 53. Excessive Permission Granted
---
service: auth-service
error_message: excessive permission granted
---
### Incident Summary
과도한 권한 부여.
### Root Cause
Role 정의 오류.
### Action Items
1. 권한 재정의.
2. 정기 권한 리뷰.

---

## 54. Third-Party SDK Security Flaw
---
service: security
error_message: vulnerable sdk detected
---
### Incident Summary
외부 SDK 취약점 발견.
### Root Cause
업데이트 미적용.
### Action Items
1. SDK 업그레이드.
2. 취약점 스캔 자동화.

---

## 55. Webhook Authentication Missing
---
service: integration
error_message: unauthenticated webhook
---
### Incident Summary
웹훅 인증 누락.
### Root Cause
서명 검증 미구현.
### Action Items
1. 서명 검증 추가.
2. IP 제한 적용.

---

## 56. Insecure CORS Configuration
---
service: gateway
error_message: insecure cors policy
---
### Incident Summary
CORS 설정 과도 개방.
### Root Cause
개발 설정 잔존.
### Action Items
1. 허용 Origin 제한.
2. 설정 감사.

---

## 57. Open Redirect Vulnerability
---
service: web
error_message: open redirect detected
---
### Incident Summary
오픈 리다이렉트 취약점.
### Root Cause
리다이렉트 URL 검증 미흡.
### Action Items
1. 허용 URL 검증.
2. 화이트리스트 적용.

---

## 58. File Upload Malware Detected
---
service: security
error_message: malware detected
---
### Incident Summary
업로드 파일에서 악성 코드 탐지.
### Root Cause
파일 검증 미흡.
### Action Items
1. 바이러스 스캔 적용.
2. 업로드 제한 강화.

---

## 59. Insecure Deserialization Attempt
---
service: security
error_message: insecure deserialization detected
---
### Incident Summary
역직렬화 공격 시도.
### Root Cause
신뢰되지 않은 데이터 처리.
### Action Items
1. 역직렬화 제한.
2. 데이터 검증 강화.

---

## 60. SSRF Attempt Detected
---
service: security
error_message: ssrf detected
---
### Incident Summary
서버 측 요청 위조 공격 감지.
### Root Cause
URL 파라미터 검증 미흡.
### Action Items
1. 내부 주소 차단.
2. URL 화이트리스트.

---

## 61. IAM Role Assumption Abuse
---
service: security
error_message: role abuse detected
---
### Incident Summary
IAM Role 오용 의심.
### Root Cause
권한 과다 부여.
### Action Items
1. Role 권한 축소.
2. CloudTrail 분석.

---

## 62. CloudTrail Logging Disabled
---
service: security
error_message: cloudtrail disabled
---
### Incident Summary
감사 로그 비활성화 감지.
### Root Cause
수동 설정 변경.
### Action Items
1. 즉시 재활성화.
2. 변경 알림 설정.

---

## 63. KMS Key Disabled
---
service: security
error_message: kms key disabled
---
### Incident Summary
암호화 키 비활성화로 서비스 오류.
### Root Cause
수동 비활성화.
### Action Items
1. 키 활성화.
2. 키 관리 정책 강화.

---

## 64. Token Introspection Endpoint Unreachable
---
service: auth-service
error_message: introspection endpoint unreachable
---
### Incident Summary
토큰 검증 실패.
### Root Cause
인증 서버 장애.
### Action Items
1. 캐시 검증 적용.
2. 서버 상태 점검.

---

## 65. Login Anomaly Detected
---
service: auth-service
error_message: login anomaly detected
---
### Incident Summary
비정상 로그인 패턴 감지.
### Root Cause
자동화 또는 계정 탈취.
### Action Items
1. 추가 인증 요구.
2. 사용자 알림.

---

## 66. Password Hash Algorithm Deprecated
---
service: auth-service
error_message: weak hash algorithm
---
### Incident Summary
취약한 해시 알고리즘 사용.
### Root Cause
레거시 설정.
### Action Items
1. bcrypt/argon2 전환.
2. 점진적 재해싱.

---

## 67. Plaintext Password Logged
---
service: security
error_message: plaintext password logged
---
### Incident Summary
로그에 평문 비밀번호 기록.
### Root Cause
디버그 로그 미정리.
### Action Items
1. 로그 마스킹.
2. 로그 정책 강화.

---

## 68. Token Revocation Delay
---
service: auth-service
error_message: token revocation delayed
---
### Incident Summary
토큰 폐기 반영 지연.
### Root Cause
캐시 TTL 과다.
### Action Items
1. 캐시 TTL 축소.
2. 즉시 무효화 경로 제공.

---

## 69. SSO Identity Provider Unreachable
---
service: auth-service
error_message: idp unreachable
---
### Incident Summary
외부 IdP 접근 불가.
### Root Cause
네트워크 또는 IdP 장애.
### Action Items
1. 장애 공지.
2. 대체 로그인 경로 제공.

---

## 70. SAML Assertion Validation Failed
---
service: auth-service
error_message: invalid saml assertion
---
### Incident Summary
SAML 검증 실패.
### Root Cause
서명 또는 시간 오류.
### Action Items
1. 인증서 점검.
2. 시간 동기화.

---

## 71. SAML Audience Restriction Violation
---
service: auth-service
error_message: saml audience mismatch
---
### Incident Summary
SAML 대상 불일치.
### Root Cause
SP 설정 오류.
### Action Items
1. Audience 설정 수정.
2. 설정 검증 자동화.

---

## 72. OAuth Consent Screen Abuse
---
service: auth-service
error_message: consent abuse detected
---
### Incident Summary
동의 화면 악용.
### Root Cause
자동화 요청.
### Action Items
1. Rate Limit 적용.
2. CAPTCHA 도입.

---

## 73. Device Fingerprint Collision
---
service: auth-service
error_message: device fingerprint collision
---
### Incident Summary
기기 식별 충돌.
### Root Cause
식별 로직 단순.
### Action Items
1. 식별 요소 보강.
2. 보조 인증 적용.

---

## 74. Remember-Me Token Theft
---
service: auth-service
error_message: remember-me token misuse
---
### Incident Summary
자동 로그인 토큰 오용.
### Root Cause
토큰 보호 미흡.
### Action Items
1. 토큰 회전.
2. 기기 바인딩 적용.

---

## 75. Excessive Logout Requests
---
service: auth-service
error_message: logout flood
---
### Incident Summary
로그아웃 요청 폭증.
### Root Cause
자동화 공격.
### Action Items
1. Rate Limit 적용.
2. 요청 검증.

---

## 76. API Schema Validation Missing
---
service: gateway
error_message: schema validation missing
---
### Incident Summary
입력 스키마 검증 미흡.
### Root Cause
보안 검증 누락.
### Action Items
1. 스키마 검증 추가.
2. 공통 미들웨어 적용.

---

## 77. Broken Object Level Authorization
---
service: auth-service
error_message: bola detected
---
### Incident Summary
객체 단위 접근 제어 실패.
### Root Cause
ID 기반 검증 누락.
### Action Items
1. 객체 권한 검증 추가.
2. 테스트 강화.

---

## 78. Excessive Data Exposure
---
service: api-gateway
error_message: excessive data exposure
---
### Incident Summary
불필요한 데이터 노출.
### Root Cause
응답 필터링 미흡.
### Action Items
1. 응답 필드 제한.
2. 보안 리뷰 수행.

---

## 79. Insecure Direct Object Reference
---
service: auth-service
error_message: idor detected
---
### Incident Summary
IDOR 취약점 발견.
### Root Cause
권한 검증 누락.
### Action Items
1. 접근 제어 강화.
2. 테스트 자동화.

---

## 80. Security Header Missing
---
service: gateway
error_message: missing security headers
---
### Incident Summary
보안 헤더 누락.
### Root Cause
서버 설정 미흡.
### Action Items
1. CSP/HSTS 설정.
2. 보안 헤더 표준화.

---

## 81. HSTS Misconfigured
---
service: gateway
error_message: hsts misconfigured
---
### Incident Summary
HSTS 설정 오류.
### Root Cause
도메인 정책 미정의.
### Action Items
1. max-age 설정.
2. preload 검토.

---

## 82. CSP Violation Detected
---
service: gateway
error_message: csp violation
---
### Incident Summary
콘텐츠 보안 정책 위반.
### Root Cause
외부 스크립트 사용.
### Action Items
1. CSP 룰 조정.
2. 스크립트 검토.

---

## 83. Clickjacking Protection Missing
---
service: web
error_message: clickjacking risk
---
### Incident Summary
클릭재킹 방어 미적용.
### Root Cause
X-Frame-Options 미설정.
### Action Items
1. DENY/SAMEORIGIN 적용.
2. CSP frame-ancestors 설정.

---

## 84. Dependency Vulnerability Scan Failed
---
service: security
error_message: dependency scan failed
---
### Incident Summary
의존성 취약점 스캔 실패.
### Root Cause
스캐너 설정 오류.
### Action Items
1. 스캔 재실행.
2. CI 연동 점검.

---

## 85. Zero Trust Policy Violation
---
service: security
error_message: zero trust violation
---
### Incident Summary
제로 트러스트 정책 위반.
### Root Cause
신뢰 경로 예외.
### Action Items
1. 접근 재검증.
2. 정책 보완.

---

## 86. Insider Access Abuse Suspected
---
service: security
error_message: insider abuse suspected
---
### Incident Summary
내부자 오용 의심.
### Root Cause
권한 남용.
### Action Items
1. 접근 감사.
2. 권한 회수.

---

## 87. Security Incident Alert Missed
---
service: security
error_message: alert missed
---
### Incident Summary
보안 알림 누락.
### Root Cause
알림 채널 장애.
### Action Items
1. 알림 이중화.
2. 테스트 정례화.

---

## 88. SOC Escalation Delay
---
service: security
error_message: soc escalation delayed
---
### Incident Summary
보안 사고 에스컬레이션 지연.
### Root Cause
운영 프로세스 미흡.
### Action Items
1. 에스컬레이션 룰 정의.
2. 담당자 지정.

---

## 89. Incident Response Playbook Missing
---
service: security
error_message: playbook missing
---
### Incident Summary
사고 대응 절차 부재.
### Root Cause
문서화 미흡.
### Action Items
1. 플레이북 작성.
2. 모의 훈련 수행.

---

## 90. Security Patch Delay
---
service: security
error_message: security patch delayed
---
### Incident Summary
보안 패치 적용 지연.
### Root Cause
운영 일정 충돌.
### Action Items
1. 패치 윈도우 확보.
2. 자동 패치 도입.

---

## 91. Vulnerability Disclosure Ignored
---
service: security
error_message: vuln disclosure ignored
---
### Incident Summary
취약점 제보 미처리.
### Root Cause
프로세스 부재.
### Action Items
1. VDP 프로세스 수립.
2. 책임자 지정.

---

## 92. Penetration Test Finding Unresolved
---
service: security
error_message: pentest finding open
---
### Incident Summary
모의 해킹 취약점 미조치.
### Root Cause
우선순위 미설정.
### Action Items
1. 리스크 기반 분류.
2. 조치 일정 수립.

---

## 93. Data Masking Bypassed
---
service: security
error_message: masking bypass detected
---
### Incident Summary
민감 데이터 마스킹 우회.
### Root Cause
로그 처리 누락.
### Action Items
1. 마스킹 강제.
2. 로그 감사.

---

## 94. PII Logged in Plaintext
---
service: security
error_message: pii logged
---
### Incident Summary
개인정보 평문 로그 기록.
### Root Cause
로깅 정책 미준수.
### Action Items
1. 마스킹 적용.
2. 로그 점검 자동화.

---

## 95. Data Retention Policy Violated
---
service: security
error_message: retention violation
---
### Incident Summary
데이터 보관 정책 위반.
### Root Cause
자동 삭제 미구현.
### Action Items
1. 보관 주기 설정.
2. 삭제 배치 구현.

---

## 96. GDPR Consent Not Recorded
---
service: security
error_message: consent missing
---
### Incident Summary
동의 이력 누락.
### Root Cause
저장 로직 미구현.
### Action Items
1. 동의 로그 저장.
2. 감사 대응 준비.

---

## 97. PCI DSS Requirement Violation
---
service: security
error_message: pci dss violation
---
### Incident Summary
PCI DSS 요구사항 미충족.
### Root Cause
보안 설정 누락.
### Action Items
1. 요구사항 점검.
2. 정기 감사 수행.

---

## 98. Security Configuration Drift
---
service: security
error_message: config drift detected
---
### Incident Summary
보안 설정 변경 감지.
### Root Cause
수동 수정.
### Action Items
1. GitOps 적용.
2. Drift 감지 자동화.

---

## 99. Incident Evidence Lost
---
service: security
error_message: evidence lost
---
### Incident Summary
사고 증적 유실.
### Root Cause
보관 정책 미흡.
### Action Items
1. 증적 보존 강화.
2. 접근 제한.

---

## 100. Security Posture Degradation
---
service: security
error_message: security posture degraded
---
### Incident Summary
전반적 보안 상태 저하 감지.
### Root Cause
누적된 미조치 이슈.
### Action Items
1. 보안 부채 정리.
2. 정기 점검 체계화.

---
