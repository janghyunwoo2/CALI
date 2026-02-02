# CALI Simulated Log Cases – Auth / Security (01–100)
# "우리 서비스 로그 한 줄 + 대응 가이드" 형태로 바로 임베딩 가능한 더미데이터

---

## 01. JWT Validation Failures Spike
---
service: auth-security-svc
error_message: High rate of JWT validation failures
---
### Incident Summary
[ERROR] 2024-03-15T10:00:00.123Z auth-security-svc/v4.2.1 [a1b2c3d4]: Security Alert - High rate of JWT validation failures. | Context: {ClientIP="45.12.34.56", FailCount="150/s", AuthMethod="Bearer"}

### Root Cause
토큰 변조/만료 토큰 리플레이/크리덴셜 스터핑 등 공격 트래픽 가능성. 또는 키 로테이션 이후 일부 서비스의 검증 키 미반영.

### Action Items
1. (즉시) ClientIP 레이트리밋 + WAF 임시 차단(연관 대역 포함).
2. (확인) 실패 JWT 샘플의 iss/aud/kid/alg/exp 패턴 분석(리플레이 vs 변조 vs 만료).
3. (확인) kid 기준으로 현재 공개키(JWKS) 최신 여부 점검.
4. (재발방지) JWT 실패율 알람 + per-IP/per-user 제한 + 키 로테이션 배포 체크리스트 추가.

---

## 02. Invalid JWT Signature
---
service: auth-security-svc
error_message: invalid jwt signature
---
### Incident Summary
[WARN] 2024-03-15T10:01:10.456Z auth-security-svc/v4.2.1 [e5f6g7h8]: Auth Failed - invalid jwt signature. | Context: {ClientIP="45.12.34.56", Kid="kid-2024-03", Alg="RS256"}

### Root Cause
서명 검증 키 불일치(로테이션/캐시 지연) 또는 공격자가 위조 토큰을 전송.

### Action Items
1. (즉시) Kid="kid-2024-03"가 JWKS에 존재하는지 확인(캐시 갱신).
2. (즉시) 동일 IP에서 연속 발생 시 차단/쿨다운.
3. (확인) 최근 키 로테이션/인증서 갱신 배포 이력 확인.
4. (재발방지) JWKS 캐시 TTL 단축 + 로테이션 시 강제 캐시 무효화.

---

## 03. Token Expired Errors Spike
---
service: auth-security-svc
error_message: token expired
---
### Incident Summary
[WARN] 2024-03-15T10:02:00.000Z auth-security-svc/v4.2.1 [t0k3nexp]: Auth Failed - token expired. | Context: {ClientIP="203.0.113.10", ExpiredCount="800/5m", Skew="0s"}

### Root Cause
클라이언트 토큰 갱신 로직 실패 또는 서버/클라이언트 시간 불일치. 대규모면 앱 릴리즈/배포 후 회귀 가능.

### Action Items
1. (즉시) 특정 앱 버전/플랫폼에서 집중되는지 확인(User-Agent 집계).
2. (확인) Refresh 토큰 엔드포인트 오류율/지연 확인.
3. (확인) 서버 NTP 동기화 상태 확인(Clock skew).
4. (재발방지) 토큰 갱신 실패 시 사용자 재로그인 가이드 + 지표 대시보드.

---

## 04. Token Not Yet Valid (Clock Skew)
---
service: auth-security-svc
error_message: token not yet valid
---
### Incident Summary
[ERROR] 2024-03-15T10:03:11.111Z auth-security-svc/v4.2.1 [cl0cksk3w]: Auth Failed - token not yet valid. | Context: {ClientIP="198.51.100.2", Nbf="2024-03-15T10:05:00Z", ServerTime="2024-03-15T10:03:11Z"}

### Root Cause
서버 시간 동기화 문제 또는 토큰 발급/검증 서비스 간 시간차. nbf/iat 검증이 엄격할수록 영향.

### Action Items
1. (즉시) 문제 노드의 시간 오프셋 확인 및 NTP 재동기화.
2. (확인) 발급 서비스/검증 서비스의 시간대/시각 동일성 확인.
3. (개선) iat/nbf 허용 오차(leeway) 설정 검토(예: 30~60초).
4. (재발방지) 시간 드리프트 알람 + 노드 교체 자동화.

---

## 05. Authorization Header Missing
---
service: api-gateway
error_message: authorization header missing
---
### Incident Summary
[WARN] 2024-03-15T10:05:00.123Z api-gateway/v3.9.0 [hdrmiss]: Request Rejected - authorization header missing. | Context: {Path="/v1/wallet/balance", ClientIP="203.0.113.77", Method="GET"}

### Root Cause
클라이언트 버그(헤더 미첨부) 또는 비인가 스캐닝.

### Action Items
1. (즉시) 동일 IP가 다수 경로를 스캔하는지 확인(패턴이면 차단).
2. (확인) 특정 앱 버전에서만 발생하는지 확인 후 핫픽스.
3. (개선) 인증 필요 경로는 401과 함께 표준 응답 제공(불필요한 내부 정보 노출 금지).
4. (재발방지) 클라이언트 SDK에서 헤더 주입을 공통화.

---

## 06. Bearer Token Malformed
---
service: api-gateway
error_message: bearer token malformed
---
### Incident Summary
[WARN] 2024-03-15T10:06:20.321Z api-gateway/v3.9.0 [b34rmal]: Request Rejected - bearer token malformed. | Context: {ClientIP="45.12.34.56", TokenLength="12", Path="/v1/payments"}

### Root Cause
공격/스캐너가 임의 문자열 전송 또는 클라이언트 토큰 저장/전송 깨짐.

### Action Items
1. (즉시) 해당 IP 레이트리밋 및 WAF 룰(비정상 토큰 패턴) 적용.
2. (확인) TokenLength/형식 분포 분석으로 공격 여부 판단.
3. (재발방지) 토큰 파싱 오류는 “상세 원인”을 외부에 노출하지 않도록 표준화.

---

## 07. Refresh Token Reuse Detected
---
service: auth-security-svc
error_message: refresh token reuse detected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:08:00.000Z auth-security-svc/v4.2.1 [r3us3tok]: Security Alert - refresh token reuse detected. | Context: {User="user_1029", ClientIP="198.51.100.10", Device="android", TokenId="rt-77aa"}

### Root Cause
Refresh 토큰 탈취 가능성(가장 위험). 정상이라면 멀티 디바이스 처리/회전 정책 버그.

### Action Items
1. (즉시) 해당 사용자 세션 전면 폐기 + 재로그인 강제 + 사용자 알림.
2. (확인) 동일 TokenId가 다른 IP/UA에서 사용되었는지 확인(탈취 증거).
3. (확인) 토큰 회전(rotate) 정책이 올바르게 적용되는지 점검.
4. (재발방지) Refresh 토큰을 기기 바인딩 + 1회성 회전 + 이상 징후 시 단계 인증.

---

## 08. Brute Force Protection Triggered
---
service: auth-security-svc
error_message: brute force protection triggered
---
### Incident Summary
[WARN] 2024-03-15T10:10:10.100Z auth-security-svc/v4.2.1 [brut3]: Login Failed - brute force protection triggered. | Context: {TargetUser="admin", ClientIP="103.20.10.5", FailCount="30/1m"}

### Root Cause
계정 대상 무차별 대입 또는 크리덴셜 스터핑.

### Action Items
1. (즉시) 관리자 계정 잠금 + 보안 채널 알림.
2. (즉시) IP/대역 차단 + 로그인 엔드포인트 레이트리밋 강화.
3. (확인) 동일 시간대 성공 로그인 시도 여부 확인(침해 여부).
4. (재발방지) 관리자 접근은 MFA 필수 + 접근망 제한(제로트러스트/사내망).

---

## 09. Credential Stuffing Suspected
---
service: auth-security-svc
error_message: credential stuffing suspected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:11:00.000Z auth-security-svc/v4.2.1 [stuff1ng]: Security Alert - credential stuffing suspected. | Context: {DistinctUsers="500", SameIP="45.12.34.56", FailRate="98%"}

### Root Cause
하나의 IP에서 다수 계정 대상으로 고속 로그인 시도 → 전형적 스터핑.

### Action Items
1. (즉시) IP 차단 + ASN/Geo 기반 추가 차단.
2. (즉시) 로그인에 CAPTCHA/봇 방어 강제(임시).
3. (확인) 유출된 자격증명 사용 흔적(성공 로그인 계정) 샘플링.
4. (재발방지) 위험 기반 로그인(RBA), 비밀번호 재설정 유도, 2FA 권장/강제.

---

## 10. Account Enumeration Attempt
---
service: auth-security-svc
error_message: account enumeration detected
---
### Incident Summary
[WARN] 2024-03-15T10:12:00.000Z auth-security-svc/v4.2.1 [enum3r]: Security Alert - account enumeration detected. | Context: {Endpoint="/v1/auth/reset", Pattern="user exists vs not", ClientIP="203.0.113.9"}

### Root Cause
응답 메시지 차이로 계정 존재 여부를 추측 가능.

### Action Items
1. (즉시) reset 응답을 동일 메시지/동일 시간으로 표준화.
2. (확인) 해당 IP의 사용자 목록 스캔 흔적 확인.
3. (재발방지) rate-limit + CAPTCHA + 요청 지연(랜덤) 적용.

---

## 11. MFA Verification Failed
---
service: auth-security-svc
error_message: mfa verification failed
---
### Incident Summary
[WARN] 2024-03-15T10:13:30.333Z auth-security-svc/v4.2.1 [mfa111]: MFA Failed - mfa verification failed. | Context: {User="john_doe", Method="OTP", Attempt="3", ClientIP="203.0.113.10"}

### Root Cause
사용자 입력 오류/OTP 동기화 문제/탈취 시도.

### Action Items
1. (즉시) 3회 실패 후 쿨다운 적용, 추가 실패 시 잠금.
2. (확인) 동일 디바이스/IP에서 다계정 실패 여부 확인.
3. (확인) OTP 검증 서비스 지연/오류율 확인.
4. (재발방지) WebAuthn/Push MFA 도입 및 백업 코드 제공.

---

## 12. MFA Bypass Attempt Detected
---
service: auth-security-svc
error_message: mfa bypass detected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:14:10.010Z auth-security-svc/v4.2.1 [mfabyp]: Security Alert - mfa bypass detected. | Context: {User="user_88", ClientIP="198.51.100.3", Vector="missing step-up token"}

### Root Cause
인증 플로우 우회 시도(파라미터 변조/직접 API 호출).

### Action Items
1. (즉시) 세션 강제 종료 + 계정 보호 조치(잠금/추가 인증).
2. (확인) 우회가 가능했던 엔드포인트/조건(Feature flag, 특정 버전) 확인.
3. (재발방지) step-up 토큰/상태 머신을 서버에서 강제 검증(클라 신뢰 금지).

---

## 13. Suspicious Login Location
---
service: auth-security-svc
error_message: suspicious login location
---
### Incident Summary
[WARN] 2024-03-15T10:16:00.000Z auth-security-svc/v4.2.1 [geo1]: Risk Login - suspicious login location. | Context: {User="user_1029", PrevCountry="KR", NewCountry="RU", TimeDelta="5m"}

### Root Cause
계정 탈취 또는 VPN/프록시.

### Action Items
1. (즉시) 추가 인증(MFA) 강제 + 알림 발송.
2. (확인) 동일 시간대 토큰 발급/결제 시도 여부 확인.
3. (재발방지) 불가능한 이동(impossible travel) 룰을 리스크 엔진에 반영.

---

## 14. Session Fixation Attempt
---
service: auth-security-svc
error_message: session fixation attempt
---
### Incident Summary
[WARN] 2024-03-15T10:17:00.000Z auth-security-svc/v4.2.1 [sessfix]: Security Alert - session fixation attempt. | Context: {User="user_7", SessionId="S-aaaa", Event="login without session rotate"}

### Root Cause
로그인 시 세션 재발급(rotate) 누락 또는 공격 시도.

### Action Items
1. (즉시) 로그인 시 세션 재발급 강제 적용 여부 점검/핫픽스.
2. (확인) 해당 세션으로 비정상 요청이 있었는지 확인.
3. (재발방지) 세션/토큰 회전 정책 표준화 및 테스트 추가.

---

## 15. Session Hijacking Suspected
---
service: auth-security-svc
error_message: session hijacking suspected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:18:00.000Z auth-security-svc/v4.2.1 [hijack]: Security Alert - session hijacking suspected. | Context: {User="user_7", IPChange="KR->US", UAChange="true", SessionId="S-bbbb"}

### Root Cause
세션 탈취 가능성(쿠키 유출, XSS 등) 또는 프록시 환경.

### Action Items
1. (즉시) 세션 폐기 + 전 디바이스 로그아웃 + 사용자 알림.
2. (확인) 쿠키 설정(HttpOnly/Secure/SameSite), XSS 징후 확인.
3. (재발방지) 기기 바인딩/리스크 기반 재인증, 토큰 수명 단축.

---

## 16. CSRF Token Missing
---
service: api-gateway
error_message: csrf token missing
---
### Incident Summary
[WARN] 2024-03-15T10:19:00.000Z api-gateway/v3.9.0 [csrf0]: Request Rejected - csrf token missing. | Context: {Path="/v1/profile/update", Method="POST", ClientIP="203.0.113.77"}

### Root Cause
웹 클라이언트 토큰 미전송 또는 공격.

### Action Items
1. (즉시) 동일 IP에서 반복이면 차단.
2. (확인) 프론트에서 CSRF 토큰 주입/전송 로직 확인.
3. (재발방지) SameSite 쿠키+CSRF 토큰 조합을 표준화.

---

## 17. CSRF Token Invalid
---
service: api-gateway
error_message: invalid csrf token
---
### Incident Summary
[WARN] 2024-03-15T10:20:00.000Z api-gateway/v3.9.0 [csrf1]: Request Rejected - invalid csrf token. | Context: {Session="S-cccc", ClientIP="203.0.113.77", Reason="mismatch"}

### Root Cause
세션 불일치, 토큰 만료, 캐시 문제.

### Action Items
1. (즉시) 사용자에게 재로그인/새로고침 유도.
2. (확인) 다중 탭/도메인 혼용(서브도메인) 여부 점검.
3. (재발방지) 토큰 TTL 및 세션 스토어 일관성 강화.

---

## 18. SameSite Cookie Misconfigured
---
service: api-gateway
error_message: samesite cookie misconfigured
---
### Incident Summary
[ERROR] 2024-03-15T10:21:00.000Z api-gateway/v3.9.0 [cookie1]: Auth Error - samesite cookie misconfigured. | Context: {Cookie="sid", SameSite="None", Secure="false"}

### Root Cause
SameSite=None이면 Secure=true가 필수. 브라우저 정책으로 쿠키가 drop 되어 로그인 루프 발생.

### Action Items
1. (즉시) Secure 플래그 적용 핫픽스.
2. (확인) HTTPS 강제/리다이렉트 체인 점검.
3. (재발방지) 쿠키 정책을 환경별로 자동 검증(CI 테스트).

---

## 19. Secure Cookie Flag Missing
---
service: api-gateway
error_message: insecure cookie detected
---
### Incident Summary
[WARN] 2024-03-15T10:22:00.000Z api-gateway/v3.9.0 [cookie2]: Security Alert - insecure cookie detected. | Context: {Cookie="sid", HttpOnly="false", Secure="false"}

### Root Cause
민감 쿠키에 보안 플래그 누락.

### Action Items
1. (즉시) Secure+HttpOnly 적용 및 배포.
2. (확인) 쿠키가 JS로 접근 가능한지(XSS 위험) 확인.
3. (재발방지) 보안 헤더/쿠키 설정을 공통 미들웨어로 강제.

---

## 20. OAuth Redirect URI Mismatch
---
service: auth-security-svc
error_message: redirect_uri_mismatch
---
### Incident Summary
[ERROR] 2024-03-15T10:23:00.000Z auth-security-svc/v4.2.1 [oauth1]: OAuth Error - redirect_uri_mismatch. | Context: {ClientId="web-123", RedirectURI="https://evil.example/cb"}

### Root Cause
등록되지 않은 redirect URI 요청(공격) 또는 환경별 등록 누락.

### Action Items
1. (즉시) RedirectURI가 합법 도메인인지 확인, 공격이면 차단.
2. (확인) OAuth 콘솔 허용 URI 목록 점검(스테이징/운영 분리).
3. (재발방지) redirect URI 화이트리스트 강제 및 배포 체크리스트.

---

## 21. OAuth State Missing
---
service: auth-security-svc
error_message: missing state parameter
---
### Incident Summary
[WARN] 2024-03-15T10:24:00.000Z auth-security-svc/v4.2.1 [oauth2]: OAuth Error - missing state parameter. | Context: {ClientId="web-123", Flow="authorize"}

### Root Cause
CSRF 방지 state 미첨부(버그) 또는 공격 시도.

### Action Items
1. (즉시) state 없는 요청 차단 유지.
2. (확인) 특정 브라우저/버전에서만 발생하는지 확인.
3. (재발방지) OAuth 라이브러리/SDK로 state 강제 주입.

---

## 22. OAuth Code Reuse Detected
---
service: auth-security-svc
error_message: authorization code reuse detected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:25:00.000Z auth-security-svc/v4.2.1 [oauth3]: Security Alert - authorization code reuse detected. | Context: {CodeId="c-7788", ClientIP="198.51.100.9"}

### Root Cause
인가 코드 재사용은 탈취/리플레이 가능성. 또는 서버 측 1회성 처리 누락.

### Action Items
1. (즉시) 해당 세션/사용자 토큰 발급 중단 및 재인증 요구.
2. (확인) 코드 저장소에서 1회성 폐기 처리 여부 점검.
3. (재발방지) 코드 1회성 + 짧은 TTL + PKCE 강제.

---

## 23. PKCE Verification Failed
---
service: auth-security-svc
error_message: pkce verification failed
---
### Incident Summary
[ERROR] 2024-03-15T10:26:00.000Z auth-security-svc/v4.2.1 [pkce1]: OAuth Error - pkce verification failed. | Context: {ClientId="mobile-456", Reason="code_verifier mismatch"}

### Root Cause
앱 저장소/세션 관리 문제로 verifier 누락/변조 또는 공격.

### Action Items
1. (즉시) 특정 앱 버전 집중 여부 확인(회귀면 롤백/핫픽스).
2. (확인) PKCE 파라미터 저장/전송 경로 점검.
3. (재발방지) PKCE 흐름 E2E 테스트 추가.

---

## 24. Token Audience Mismatch
---
service: auth-security-svc
error_message: invalid token audience
---
### Incident Summary
[ERROR] 2024-03-15T10:27:00.000Z auth-security-svc/v4.2.1 [aud1]: Auth Failed - invalid token audience. | Context: {Aud="payments", Expected="wallet", ClientIP="203.0.113.12"}

### Root Cause
서비스 간 토큰 혼용 또는 공격자가 다른 서비스 토큰을 재사용.

### Action Items
1. (즉시) aud mismatch 요청 차단 유지.
2. (확인) 클라이언트/게이트웨이 라우팅 오류로 다른 서비스 토큰을 붙였는지 점검.
3. (재발방지) 서비스별 토큰 분리 및 SDK에서 자동 선택.

---

## 25. Token Issuer Mismatch
---
service: auth-security-svc
error_message: invalid token issuer
---
### Incident Summary
[ERROR] 2024-03-15T10:28:00.000Z auth-security-svc/v4.2.1 [iss1]: Auth Failed - invalid token issuer. | Context: {Iss="https://staging-idp", Expected="https://prod-idp"}

### Root Cause
스테이징/운영 환경 혼용 또는 설정 오류.

### Action Items
1. (즉시) 배포 환경 변수/시크릿 점검 후 수정.
2. (확인) 특정 노드만 misconfig인지 확인(부분 배포).
3. (재발방지) 환경별 설정 검증 프리플라이트 추가.

---

## 26. Rate Limit Exceeded (Auth)
---
service: auth-security-svc
error_message: rate limit exceeded
---
### Incident Summary
[WARN] 2024-03-15T10:29:00.000Z auth-security-svc/v4.2.1 [rl1]: Rate Limit - auth endpoint rate limit exceeded. | Context: {ClientIP="45.12.34.56", Limit="20/s", Path="/v1/auth/login"}

### Root Cause
공격/봇 또는 잘못된 재시도 정책.

### Action Items
1. (즉시) IP 차단/대역 레이트리밋 강화.
2. (확인) 실패율이 높은지(공격) 성공률이 높은지(남용) 구분.
3. (재발방지) 지수 백오프+jitter 강제 및 봇 방어(CAPTCHA) 적용.

---

## 27. Password Reset Token Expired
---
service: auth-security-svc
error_message: reset token expired
---
### Incident Summary
[INFO] 2024-03-15T10:30:00.000Z auth-security-svc/v4.2.1 [rst1]: Reset Failed - reset token expired. | Context: {User="user_20", TTL="15m", Age="40m"}

### Root Cause
사용자 처리 지연(정상) 또는 메일 지연.

### Action Items
1. (즉시) 재발급 버튼 제공 및 안내.
2. (확인) 메일 발송/도착 지연 여부 점검(메일 벤더).
3. (재발방지) TTL 정책 조정(보안-편의 균형) 및 안내 강화.

---

## 28. Password Reset Token Reuse
---
service: auth-security-svc
error_message: reset token reuse detected
---
### Incident Summary
[WARN] 2024-03-15T10:31:00.000Z auth-security-svc/v4.2.1 [rst2]: Security Alert - reset token reuse detected. | Context: {User="user_20", TokenId="pr-9911", ClientIP="198.51.100.4"}

### Root Cause
토큰 1회성 처리 누락 또는 탈취.

### Action Items
1. (즉시) 해당 토큰 폐기 + 사용자 알림.
2. (확인) 토큰 저장소에서 1회성 소비 처리 여부 점검.
3. (재발방지) reset 토큰을 1회성+짧은 TTL로 강제, 실패/재시도 로깅 강화.

---

## 29. Email Verification Link Invalid
---
service: auth-security-svc
error_message: invalid verification link
---
### Incident Summary
[INFO] 2024-03-15T10:32:00.000Z auth-security-svc/v4.2.1 [mail1]: Verify Failed - invalid verification link. | Context: {User="user_33", Reason="tampered"}

### Root Cause
링크 변조/만료 또는 복사 과정 문제.

### Action Items
1. (즉시) 재발급 링크 제공.
2. (확인) 동일 IP에서 다수 계정 링크 검증 실패면 공격 의심.
3. (재발방지) 링크에 서명/만료 포함 및 실패율 모니터링.

---

## 30. Email Verification Flood
---
service: auth-security-svc
error_message: verification flood detected
---
### Incident Summary
[WARN] 2024-03-15T10:33:00.000Z auth-security-svc/v4.2.1 [mail2]: Abuse Alert - verification flood detected. | Context: {ClientIP="203.0.113.200", Requests="500/10m"}

### Root Cause
봇이 인증 메일 발송을 악용(스팸/리소스 소모).

### Action Items
1. (즉시) 발송 엔드포인트 레이트리밋 + CAPTCHA.
2. (확인) 특정 도메인/이메일 패턴(가짜) 필터링.
3. (재발방지) 이메일 발송 쿼터 및 abuse 탐지 룰 추가.

---

## 31. API Key Compromised Suspected
---
service: api-gateway
error_message: api key compromised
---
### Incident Summary
[CRITICAL] 2024-03-15T10:34:00.000Z api-gateway/v3.9.0 [keycmp]: Security Alert - api key compromised suspected. | Context: {APIKey="sk_live_xxx", Geo="unknown", Burst="1000/s"}

### Root Cause
키 유출 후 남용 가능성(호출 급증/비정상 지리).

### Action Items
1. (즉시) 해당 키 폐기/차단, 영향 범위 파악.
2. (확인) 사용 이력(엔드포인트/UA/IP/시간대) 분석.
3. (재발방지) 키 로테이션 자동화, 키 스코프 최소화, 키 사용량 알람.

---

## 32. API Key Scope Too Broad
---
service: api-gateway
error_message: api key scope too broad
---
### Incident Summary
[WARN] 2024-03-15T10:35:00.000Z api-gateway/v3.9.0 [keyscp]: Policy Alert - api key scope too broad. | Context: {APIKey="sk_live_xxx", Scopes="*", Owner="partner-A"}

### Root Cause
최소권한 위반으로 침해 시 피해가 커짐.

### Action Items
1. (즉시) 파트너 키 스코프를 필요한 권한만으로 축소.
2. (확인) 실제 호출 엔드포인트 기반으로 권한 재정의.
3. (재발방지) 키 발급 워크플로우에 보안 리뷰 강제.

---

## 33. IP Whitelist Denied
---
service: api-gateway
error_message: ip not allowed
---
### Incident Summary
[ERROR] 2024-03-15T10:36:00.000Z api-gateway/v3.9.0 [ipwl1]: Request Rejected - ip not allowed. | Context: {ClientIP="198.51.100.7", APIKeyOwner="partner-A", Path="/v1/payouts"}

### Root Cause
화이트리스트 누락 또는 파트너 IP 변경.

### Action Items
1. (즉시) 파트너에 IP 변경 여부 확인 후 반영.
2. (확인) 운영/스테이징 정책 혼동 여부 점검.
3. (재발방지) 파트너 IP 변경 프로세스+알림 체계화.

---

## 34. WAF SQLi Pattern Detected
---
service: web-firewall
error_message: sql injection detected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:37:00.000Z web-firewall/v1.1.0 [wafsql]: WAF Block - sql injection detected. | Context: {ClientIP="45.12.34.56", Path="/v1/search", Param="q=' OR 1=1 --"}

### Root Cause
명백한 SQLi 공격 시도.

### Action Items
1. (즉시) IP 차단 + 룰 강화.
2. (확인) 해당 엔드포인트의 쿼리 빌드 방식 점검(Prepared Statement 여부).
3. (재발방지) 입력 검증/파라미터 바인딩 강제 및 보안 테스트 자동화.

---

## 35. WAF XSS Pattern Detected
---
service: web-firewall
error_message: xss pattern detected
---
### Incident Summary
[WARN] 2024-03-15T10:38:00.000Z web-firewall/v1.1.0 [wafxss]: WAF Block - xss pattern detected. | Context: {ClientIP="203.0.113.50", Path="/v1/comment", Payload="<script>alert(1)</script>"}

### Root Cause
XSS 공격 시도 또는 악성 입력.

### Action Items
1. (즉시) 공격 IP 차단(반복 시).
2. (확인) 저장형 XSS 가능 경로(렌더링) 점검.
3. (재발방지) 출력 이스케이프 표준화 + CSP 설정 강화.

---

## 36. SSRF Attempt Detected
---
service: web-firewall
error_message: ssrf detected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:39:00.000Z web-firewall/v1.1.0 [wafssrf]: WAF Block - ssrf detected. | Context: {ClientIP="198.51.100.8", TargetURL="http://169.254.169.254/latest/meta-data"}

### Root Cause
클라우드 메타데이터 탈취 시도(심각).

### Action Items
1. (즉시) 요청 차단 + IP 차단.
2. (확인) 해당 기능(URL fetch, webhook tester 등)에 내부망 접근 차단이 적용되는지 점검.
3. (재발방지) URL allowlist + RFC1918/metadata 차단 + egress 정책 강화.

---

## 37. Insecure CORS Policy
---
service: api-gateway
error_message: insecure cors policy
---
### Incident Summary
[WARN] 2024-03-15T10:40:00.000Z api-gateway/v3.9.0 [cors1]: Policy Alert - insecure cors policy. | Context: {AllowOrigin="*", AllowCredentials="true"}

### Root Cause
CORS 과도 개방으로 토큰/쿠키 유출 위험.

### Action Items
1. (즉시) AllowOrigin을 화이트리스트로 제한, Credentials 사용 시 '*' 금지.
2. (확인) 실제 필요한 Origin 목록 수집.
3. (재발방지) 환경별 CORS 정책 템플릿화 + 자동 점검.

---

## 38. Security Headers Missing
---
service: api-gateway
error_message: missing security headers
---
### Incident Summary
[WARN] 2024-03-15T10:41:00.000Z api-gateway/v3.9.0 [hdrsec]: Policy Alert - missing security headers. | Context: {Missing="HSTS,CSP,X-Frame-Options", Path="/"}

### Root Cause
기본 보안 헤더 설정 누락.

### Action Items
1. (즉시) 공통 미들웨어에서 HSTS/CSP/XFO 적용.
2. (확인) 일부 경로만 누락인지(정적/리버스프록시) 확인.
3. (재발방지) 보안 헤더 스캐너를 CI에 연동.

---

## 39. Clickjacking Risk
---
service: web
error_message: clickjacking risk
---
### Incident Summary
[WARN] 2024-03-15T10:42:00.000Z web/v2.1.0 [cj1]: Security Alert - clickjacking risk. | Context: {Header="X-Frame-Options missing", Page="/settings"}

### Root Cause
iframe 내 렌더링 허용으로 클릭재킹 가능.

### Action Items
1. (즉시) X-Frame-Options: DENY 또는 CSP frame-ancestors 적용.
2. (재발방지) 보안 헤더 표준화.

---

## 40. HSTS Misconfigured
---
service: api-gateway
error_message: hsts misconfigured
---
### Incident Summary
[ERROR] 2024-03-15T10:43:00.000Z api-gateway/v3.9.0 [hsts1]: Policy Alert - hsts misconfigured. | Context: {maxAge="0", includeSubDomains="false"}

### Root Cause
HSTS 비활성화로 다운그레이드 공격 위험.

### Action Items
1. (즉시) 적절한 max-age 설정(예: 6~12개월) 및 includeSubDomains 검토.
2. (재발방지) HSTS 정책 템플릿/테스트 추가.

---

## 41. TLS Deprecated Version Detected
---
service: api-gateway
error_message: deprecated tls version
---
### Incident Summary
[WARN] 2024-03-15T10:44:00.000Z api-gateway/v3.9.0 [tls1]: Security Alert - deprecated tls version. | Context: {TLS="1.0", ClientIP="203.0.113.99"}

### Root Cause
구버전 TLS 클라이언트가 접속하거나 LB 설정 미흡.

### Action Items
1. (즉시) TLS 1.2+만 허용하도록 LB/서버 설정.
2. (확인) 차단 시 영향 고객군 파악 후 공지.
3. (재발방지) 보안 기준 문서화 및 정기 점검.

---

## 42. Certificate Expired
---
service: api-gateway
error_message: SSL certificate expired
---
### Incident Summary
[CRITICAL] 2024-03-15T10:45:00.000Z api-gateway/v3.9.0 [cert1]: TLS Error - SSL certificate expired. | Context: {Domain="api.cali.local", ExpiredAt="2024-03-14"}

### Root Cause
인증서 갱신 누락.

### Action Items
1. (즉시) 인증서 갱신 및 배포(가능하면 자동 갱신).
2. (재발방지) 만료 30/14/7/1일 알람 + 자동 갱신 파이프라인.

---

## 43. Certificate Chain Incomplete
---
service: api-gateway
error_message: incomplete certificate chain
---
### Incident Summary
[ERROR] 2024-03-15T10:46:00.000Z api-gateway/v3.9.0 [cert2]: TLS Error - incomplete certificate chain. | Context: {Domain="api.cali.local", Missing="intermediate"}

### Root Cause
중간 인증서 누락으로 일부 클라이언트 연결 실패.

### Action Items
1. (즉시) fullchain으로 교체.
2. (재발방지) 배포 전 SSL 검사 자동화.

---

## 44. mTLS Handshake Failed
---
service: internal-gateway
error_message: mtls handshake failed
---
### Incident Summary
[ERROR] 2024-03-15T10:47:00.000Z internal-gateway/v1.6.0 [mtls1]: TLS Error - mtls handshake failed. | Context: {ClientCN="svc-wallet", Reason="unknown ca"}

### Root Cause
클라이언트 인증서/CA 신뢰 설정 불일치.

### Action Items
1. (즉시) 신뢰 CA 체인/인증서 만료 확인.
2. (확인) 최근 인증서 로테이션 여부 확인.
3. (재발방지) mTLS 로테이션 runbook + 점진 배포.

---

## 45. Secrets Manager Access Denied
---
service: security
error_message: access denied to secret
---
### Incident Summary
[ERROR] 2024-03-15T10:48:00.000Z security/v1.0.0 [sec1]: Secret Error - access denied to secret. | Context: {Secret="prod/jwt-private-key", Role="eks-node-role"}

### Root Cause
IAM 정책/역할 설정 오류.

### Action Items
1. (즉시) 해당 서비스 역할에 최소 권한으로 secret read 부여.
2. (확인) IRSA/RoleArn 설정 및 정책 조건 확인.
3. (재발방지) 시크릿 접근 권한을 IaC로 관리 + 변경 감지.

---

## 46. Secret Rotation Failed
---
service: security
error_message: secret rotation failed
---
### Incident Summary
[ERROR] 2024-03-15T10:49:00.000Z security/v1.0.0 [sec2]: Secret Rotation - secret rotation failed. | Context: {Secret="prod/pg-api-key", Step="update", Error="timeout"}

### Root Cause
로테이션 람다/잡 오류, 권한 부족, 외부 의존 실패.

### Action Items
1. (즉시) 수동 로테이션 수행(서비스 영향 최소화).
2. (확인) 로테이션 로그에서 실패 단계 확인.
3. (재발방지) 로테이션 dry-run/헬스체크 + 실패 알림 강화.

---

## 47. Hardcoded Secret Found
---
service: security
error_message: hardcoded secret found
---
### Incident Summary
[CRITICAL] 2024-03-15T10:50:00.000Z security/v1.0.0 [sec3]: Code Scan - hardcoded secret found. | Context: {Repo="cali-api", File="config.py", Type="api_key"}

### Root Cause
비밀정보가 코드에 포함됨(유출 위험).

### Action Items
1. (즉시) 키 폐기/재발급, 커밋 히스토리 정리(필요 시).
2. (확인) 노출 범위(레포 접근자/빌드 로그/아티팩트) 확인.
3. (재발방지) secret scanning + pre-commit hook + CI 차단 규칙.

---

## 48. CloudTrail Disabled
---
service: security
error_message: cloudtrail disabled
---
### Incident Summary
[CRITICAL] 2024-03-15T10:51:00.000Z security/v1.0.0 [trail1]: Audit Alert - cloudtrail disabled. | Context: {Account="prod", Region="ap-northeast-2", Actor="unknown"}

### Root Cause
의도치 않은 설정 변경 또는 침해 시도.

### Action Items
1. (즉시) CloudTrail 즉시 재활성화 + 변경 주체 조사.
2. (확인) 동일 시간대 IAM 변경/권한 상승 이벤트 확인.
3. (재발방지) Config/Guardrails로 비활성화 차단 및 알림.

---

## 49. KMS Key Disabled
---
service: security
error_message: kms key disabled
---
### Incident Summary
[CRITICAL] 2024-03-15T10:52:00.000Z security/v1.0.0 [kms1]: Crypto Alert - kms key disabled. | Context: {KeyId="kms-1234", Impact="decrypt failures"}

### Root Cause
키 비활성화로 복호화 불가(서비스 중단 유발).

### Action Items
1. (즉시) 키 재활성화 및 영향을 받는 서비스 확인.
2. (확인) 변경 주체/정책(자동화/수동) 조사.
3. (재발방지) KMS 변경에 승인 워크플로우 + 알림 강화.

---

## 50. PII Logged in Plaintext
---
service: security
error_message: pii logged
---
### Incident Summary
[CRITICAL] 2024-03-15T10:53:00.000Z security/v1.0.0 [pii1]: Privacy Alert - pii logged in plaintext. | Context: {Field="resident_id", Path="/v1/auth/register", Sample="900101-1******"}

### Root Cause
로깅 마스킹 누락/디버그 로그 잔존.

### Action Items
1. (즉시) 해당 로그 스트림 접근 제한 + 보존 정책 단축(규정 준수).
2. (즉시) 마스킹 핫픽스 배포 + 과거 로그 삭제/격리(정책에 따라).
3. (재발방지) 공통 로깅 레이어에서 민감 필드 자동 마스킹 강제.

---

## 51. Data Masking Bypass Detected
---
service: security
error_message: masking bypass detected
---
### Incident Summary
[ERROR] 2024-03-15T10:54:00.000Z security/v1.0.0 [mask1]: Privacy Alert - masking bypass detected. | Context: {Service="wallet-service", Field="card_number", Reason="custom logger"}

### Root Cause
커스텀 로거/우회 경로로 마스킹 미적용.

### Action Items
1. (즉시) 우회 로거 사용 금지 및 공통 로깅으로 강제 전환.
2. (확인) 마스킹 커버리지 스캔(정적/런타임).
3. (재발방지) 마스킹 단위 테스트 + 린터 규칙 추가.

---

## 52. Replay Attack Detected
---
service: api-gateway
error_message: replay attack detected
---
### Incident Summary
[CRITICAL] 2024-03-15T10:55:00.000Z api-gateway/v3.9.0 [rply1]: Security Alert - replay attack detected. | Context: {Nonce="n-123", Timestamp="old", ClientIP="198.51.100.30"}

### Root Cause
Nonce/타임스탬프 재사용으로 요청 재전송.

### Action Items
1. (즉시) 해당 IP 차단 및 nonce 저장소 상태 확인.
2. (개선) Nonce 1회성 강제 + 허용 시간창 제한.
3. (재발방지) 요청 서명(HMAC) 적용 및 서버에서 검증 강제.

---

## 53. Revoked Token Accepted
---
service: auth-security-svc
error_message: revoked token accepted
---
### Incident Summary
[CRITICAL] 2024-03-15T10:56:00.000Z auth-security-svc/v4.2.1 [rev1]: Security Alert - revoked token accepted. | Context: {TokenId="at-555", CacheTTL="30m", RevokedAt="now"}

### Root Cause
블랙리스트/폐기 토큰 반영 지연(캐시 TTL 과다, 무효화 이벤트 누락).

### Action Items
1. (즉시) 토큰 검증 캐시 무효화 및 해당 사용자 세션 강제 종료.
2. (확인) 토큰 폐기 이벤트가 소비되었는지(로그/메트릭) 확인.
3. (재발방지) revocation 이벤트 즉시 반영 + TTL 단축 + 강제 무효화 엔드포인트 제공.

---

## 54. Token Introspection Unreachable
---
service: auth-security-svc
error_message: introspection endpoint unreachable
---
### Incident Summary
[ERROR] 2024-03-15T10:57:00.000Z auth-security-svc/v4.2.1 [intro1]: Auth Error - introspection endpoint unreachable. | Context: {Endpoint="https://idp/introspect", Timeout="2s"}

### Root Cause
IDP 장애/네트워크 문제로 실시간 검증 불가.

### Action Items
1. (즉시) 캐시 기반 검증(허용 범위 내) 또는 임시 degrade 정책 적용.
2. (확인) IDP 상태/네트워크 라우팅 점검.
3. (재발방지) IDP HA 및 circuit breaker + fallback 설계.

---

## 55. SSO IdP Unreachable
---
service: auth-security-svc
error_message: idp unreachable
---
### Incident Summary
[ERROR] 2024-03-15T10:58:00.000Z auth-security-svc/v4.2.1 [sso1]: SSO Error - idp unreachable. | Context: {Provider="SAML", Timeout="3s", ClientIP="203.0.113.41"}

### Root Cause
외부 IdP 장애/네트워크 이슈.

### Action Items
1. (즉시) 사용자 공지 + 대체 로그인(로컬 계정) 가능 여부 확인.
2. (확인) IdP 상태 페이지 및 네트워크 경로 점검.
3. (재발방지) IdP 다중화/페일오버 검토.

---

## 56. SAML Assertion Invalid
---
service: auth-security-svc
error_message: invalid saml assertion
---
### Incident Summary
[ERROR] 2024-03-15T10:59:00.000Z auth-security-svc/v4.2.1 [saml1]: SSO Error - invalid saml assertion. | Context: {Reason="signature", ClockSkew="120s"}

### Root Cause
서명 인증서 불일치 또는 시간 불일치.

### Action Items
1. (즉시) SP/IdP 인증서 체인 및 만료 확인.
2. (확인) NTP 동기화 및 허용 오차 설정.
3. (재발방지) SAML 메타데이터 로테이션 자동화.

---

## 57. SAML Audience Mismatch
---
service: auth-security-svc
error_message: saml audience mismatch
---
### Incident Summary
[ERROR] 2024-03-15T11:00:00.000Z auth-security-svc/v4.2.1 [saml2]: SSO Error - saml audience mismatch. | Context: {Aud="app-staging", Expected="app-prod"}

### Root Cause
환경 혼용 또는 SP 설정 오류.

### Action Items
1. (즉시) prod/staging 메타데이터 분리 확인.
2. (재발방지) 환경별 설정 프리플라이트 검증.

---

## 58. Device Fingerprint Collision
---
service: auth-security-svc
error_message: device fingerprint collision
---
### Incident Summary
[WARN] 2024-03-15T11:01:00.000Z auth-security-svc/v4.2.1 [dev1]: Risk Alert - device fingerprint collision. | Context: {Fingerprint="fp-aaa", Users="25", ClientIP="203.0.113.1"}

### Root Cause
지문 생성 로직이 단순하여 충돌(공유 프록시/브라우저) 또는 스푸핑.

### Action Items
1. (확인) 지문 생성 구성 요소(UA+HW+cookie 등) 점검 및 개선.
2. (개선) 위험도 상승 시 step-up 인증 요구.
3. (재발방지) 지문을 보조 신호로만 사용(단독 의존 금지).

---

## 59. Remember-Me Token Misuse
---
service: auth-security-svc
error_message: remember-me token misuse
---
### Incident Summary
[CRITICAL] 2024-03-15T11:02:00.000Z auth-security-svc/v4.2.1 [rm1]: Security Alert - remember-me token misuse. | Context: {User="user_9", TokenId="rm-001", NewIP="US", OldIP="KR"}

### Root Cause
장기 토큰 탈취 가능성 또는 기기 바인딩 미적용.

### Action Items
1. (즉시) remember-me 토큰 폐기 + 재로그인 강제.
2. (재발방지) 장기 토큰 회전/기기 바인딩/리스크 기반 재인증.

---

## 60. Excessive Logout Requests
---
service: auth-security-svc
error_message: logout flood
---
### Incident Summary
[WARN] 2024-03-15T11:03:00.000Z auth-security-svc/v4.2.1 [logout1]: Abuse Alert - logout flood. | Context: {ClientIP="198.51.100.70", Requests="500/5m"}

### Root Cause
서비스 방해 또는 봇 트래픽.

### Action Items
1. (즉시) logout 엔드포인트 레이트리밋.
2. (확인) 동일 IP가 다른 인증 엔드포인트도 스캔하는지 확인.
3. (재발방지) 인증 엔드포인트 공통 방어 정책 적용.

---

## 61. Broken Object Level Authorization (BOLA)
---
service: authz-service
error_message: bola detected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:04:00.000Z authz-service/v1.3.0 [bola1]: Security Alert - bola detected. | Context: {User="user_1", Resource="wallet:user_2", Path="/v1/wallet/statement"}

### Root Cause
객체 단위 권한 검증 누락(ID만 바꾸면 접근 가능).

### Action Items
1. (즉시) 해당 엔드포인트 차단/핫픽스(서버에서 owner 검증).
2. (확인) 유사 엔드포인트 전수 점검(검색/다운로드).
3. (재발방지) 정책 기반 authorization 미들웨어 + 테스트(권한 케이스) 추가.

---

## 62. IDOR Attempt Detected
---
service: authz-service
error_message: idor detected
---
### Incident Summary
[WARN] 2024-03-15T11:05:00.000Z authz-service/v1.3.0 [idor1]: Security Alert - idor detected. | Context: {User="user_1", Param="accountId=99999", Result="403"}

### Root Cause
직접 객체 참조 취약점 시도.

### Action Items
1. (즉시) 403 유지, 반복 시 IP/계정 레이트리밋.
2. (재발방지) 모든 리소스 접근에 owner/role 검증 강제.

---

## 63. Excessive Data Exposure
---
service: api-gateway
error_message: excessive data exposure
---
### Incident Summary
[ERROR] 2024-03-15T11:06:00.000Z api-gateway/v3.9.0 [edata1]: Policy Alert - excessive data exposure. | Context: {Endpoint="/v1/user/profile", Fields="resident_id,full_card_number"}

### Root Cause
응답 필드 필터링 누락으로 민감 정보 노출.

### Action Items
1. (즉시) 민감 필드 제거 핫픽스 + 캐시 무효화.
2. (확인) 로그/트래픽에서 노출 범위 파악(규정 준수 대응).
3. (재발방지) Response DTO 화이트리스트 + 자동 스키마 검증.

---

## 64. Dependency Vulnerability Found
---
service: security
error_message: vulnerable dependency detected
---
### Incident Summary
[WARN] 2024-03-15T11:07:00.000Z security/v1.0.0 [dep1]: SCA Alert - vulnerable dependency detected. | Context: {Package="log4j", Version="2.14.1", CVE="CVE-xxxx"}

### Root Cause
취약한 라이브러리 사용.

### Action Items
1. (즉시) 패치 버전으로 업그레이드 계획 수립(고위험은 즉시).
2. (확인) 실제 런타임에서 취약 경로 사용 여부 확인.
3. (재발방지) CI에 SCA 차단 정책 적용.

---

## 65. Dependency Scan Failed
---
service: security
error_message: dependency scan failed
---
### Incident Summary
[ERROR] 2024-03-15T11:08:00.000Z security/v1.0.0 [dep2]: CI Security - dependency scan failed. | Context: {Pipeline="build#8812", Reason="scanner timeout"}

### Root Cause
스캐너 설정/네트워크 장애로 보안 게이트 실패.

### Action Items
1. (즉시) 재시도 및 스캐너 리소스 증설.
2. (재발방지) 스캐너를 HA 구성, 실패 시 우회(승인 필요) 정책 정의.

---

## 66. DDoS Mitigation Activated
---
service: edge-security
error_message: ddos mitigation activated
---
### Incident Summary
[CRITICAL] 2024-03-15T11:09:00.000Z edge-security/v2.0.0 [ddos1]: Edge Alert - ddos mitigation activated. | Context: {RPS="250k", Target="/v1/auth/login", GeoTop="US"}

### Root Cause
대규모 트래픽 공격.

### Action Items
1. (즉시) 보호 모드 유지, WAF/RateLimit 상향.
2. (확인) 정상 트래픽 영향(오탐) 최소화 설정.
3. (재발방지) Anycast/CDN/봇 관리 강화 및 런북/훈련.

---

## 67. Admin Endpoint Exposed
---
service: api-gateway
error_message: admin endpoint exposed
---
### Incident Summary
[CRITICAL] 2024-03-15T11:10:00.000Z api-gateway/v3.9.0 [adm1]: Security Alert - admin endpoint exposed. | Context: {Path="/admin/debug", Public="true"}

### Root Cause
라우팅/ACL 설정 오류로 내부 엔드포인트 외부 노출.

### Action Items
1. (즉시) 엔드포인트 차단(ACL/인그레스) 및 접근 로그 보존.
2. (확인) 노출 기간 동안 접근 흔적 조사.
3. (재발방지) 관리자 경로는 빌드에서 제외 또는 내부망 전용으로 강제.

---

## 68. Audit Log Missing
---
service: security
error_message: audit log missing
---
### Incident Summary
[ERROR] 2024-03-15T11:11:00.000Z security/v1.0.0 [aud1]: Audit Alert - audit log missing. | Context: {Service="auth-security-svc", Window="10m"}

### Root Cause
로깅 파이프라인 장애 또는 설정 누락.

### Action Items
1. (즉시) 로깅 수집기/전송 상태 점검.
2. (확인) 해당 기간 보안 이벤트 복구(대체 로그/트레이스).
3. (재발방지) 감사 로그는 이중 전송 + 무결성/누락 알람.

---

## 69. Audit Log Tampering Suspected
---
service: security
error_message: audit log tampering detected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:12:00.000Z security/v1.0.0 [aud2]: Audit Alert - audit log tampering detected. | Context: {HashMismatch="true", Stream="audit-prod"}

### Root Cause
로그 위변조 또는 저장소 무결성 문제.

### Action Items
1. (즉시) 접근 권한 회수 + 증적 보존(포렌식).
2. (확인) 변경 주체/접근 경로 조사(CloudTrail 포함).
3. (재발방지) WORM 스토리지/서명 기반 무결성 체계 도입.

---

## 70. GDPR Consent Missing
---
service: compliance
error_message: consent missing
---
### Incident Summary
[ERROR] 2024-03-15T11:13:00.000Z compliance/v1.2.0 [gdpr1]: Compliance Alert - consent missing. | Context: {User="user_77", Feature="marketing_optin", Event="export"}

### Root Cause
동의 기록 저장/조회 로직 누락 또는 마이그레이션 오류.

### Action Items
1. (즉시) 동의 없는 데이터 처리 차단 및 리포트 생성.
2. (확인) 동의 테이블/이벤트 로그 정합성 점검.
3. (재발방지) 동의 기록은 별도 원장처럼 내구성 있게 저장.

---

## 71. PCI DSS Violation Detected
---
service: compliance
error_message: pci dss violation
---
### Incident Summary
[CRITICAL] 2024-03-15T11:14:00.000Z compliance/v1.2.0 [pci1]: Compliance Alert - pci dss violation. | Context: {Finding="PAN stored unencrypted", Location="db:cards"}

### Root Cause
카드 PAN 저장 정책 위반(암호화/토큰화 미적용).

### Action Items
1. (즉시) 접근 차단 및 데이터 암호화/토큰화 적용 계획 수립.
2. (확인) 저장된 데이터 범위/노출 여부 파악.
3. (재발방지) PAN 저장 금지/토큰화 강제 + 정기 감사.

---

## 72. Security Patch Delayed
---
service: security
error_message: security patch delayed
---
### Incident Summary
[WARN] 2024-03-15T11:15:00.000Z security/v1.0.0 [patch1]: Ops Alert - security patch delayed. | Context: {CVE="CVE-xxxx", Age="45d", Severity="High"}

### Root Cause
패치 윈도우/운영 우선순위 문제.

### Action Items
1. (즉시) High/critical은 긴급 패치 일정 확정.
2. (재발방지) 패치 SLA(예: critical 7일) 수립 및 준수 모니터링.

---

## 73. Security Configuration Drift
---
service: security
error_message: config drift detected
---
### Incident Summary
[ERROR] 2024-03-15T11:16:00.000Z security/v1.0.0 [drift1]: Drift Alert - config drift detected. | Context: {Resource="WAF-RuleSet", Change="manual", Actor="unknown"}

### Root Cause
수동 변경으로 표준 설정과 불일치.

### Action Items
1. (즉시) 변경 롤백(IaC 기준으로 복구).
2. (확인) 변경 주체 조사 및 권한 점검.
3. (재발방지) GitOps+drift detector로 수동 변경 차단.

---

## 74. Insider Abuse Suspected
---
service: security
error_message: insider abuse suspected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:17:00.000Z security/v1.0.0 [ins1]: Security Alert - insider abuse suspected. | Context: {User="employee_3", Action="export_all_users", Time="02:13Z"}

### Root Cause
권한 남용/계정 탈취 가능.

### Action Items
1. (즉시) 계정 접근 차단 및 증적 확보.
2. (확인) 정당한 업무 요청인지 확인(승인 기록).
3. (재발방지) 관리자 작업은 2인 승인+감사 로깅+이상행위 탐지.

---

## 75. Open Redirect Detected
---
service: web
error_message: open redirect detected
---
### Incident Summary
[WARN] 2024-03-15T11:18:00.000Z web/v2.1.0 [redir1]: Security Alert - open redirect detected. | Context: {Param="next=https://evil.example", Path="/login"}

### Root Cause
리다이렉트 파라미터 검증 누락.

### Action Items
1. (즉시) 리다이렉트 URL 화이트리스트 적용.
2. (재발방지) 보안 테스트(OWASP) 케이스 추가.

---

## 76. Insecure Deserialization Attempt
---
service: web-firewall
error_message: insecure deserialization detected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:19:00.000Z web-firewall/v1.1.0 [deser1]: WAF Block - insecure deserialization detected. | Context: {ClientIP="198.51.100.66", Payload="rO0ABXNy..."}

### Root Cause
역직렬화 기반 RCE 시도 가능.

### Action Items
1. (즉시) 차단 유지, IP 차단.
2. (확인) 해당 입력이 처리되는 엔드포인트 존재 여부 점검.
3. (재발방지) 역직렬화 금지/안전 포맷(JSON) 강제.

---

## 77. File Upload Malware Detected
---
service: security
error_message: malware detected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:20:00.000Z security/v1.0.0 [mal1]: Security Alert - malware detected. | Context: {User="user_5", File="kyc.zip", Engine="clamav"}

### Root Cause
악성 파일 업로드(의도적 공격 가능).

### Action Items
1. (즉시) 업로드 차단 및 사용자 세션 제한.
2. (확인) 동일 사용자/ IP 반복 여부 확인.
3. (재발방지) 업로드 확장자/용량 제한 + 샌드박스 스캔.

---

## 78. Webhook Authentication Missing
---
service: integration
error_message: unauthenticated webhook
---
### Incident Summary
[ERROR] 2024-03-15T11:21:00.000Z integration/v1.4.0 [wh1]: Webhook Error - unauthenticated webhook received. | Context: {Source="unknown", Path="/webhooks/pg"}

### Root Cause
서명 검증 미구현 또는 설정 누락.

### Action Items
1. (즉시) 서명 검증/시크릿 설정 즉시 적용.
2. (확인) 과거 수신 이벤트 중 위조 여부 점검.
3. (재발방지) webhook은 반드시 signature + timestamp + allowlist/IP 제한.

---

## 79. Webhook Signature Invalid
---
service: integration
error_message: invalid webhook signature
---
### Incident Summary
[WARN] 2024-03-15T11:22:00.000Z integration/v1.4.0 [wh2]: Webhook Error - invalid webhook signature. | Context: {Provider="PG-A", Reason="secret mismatch"}

### Root Cause
시크릿 불일치(로테이션 미반영) 또는 위조 요청.

### Action Items
1. (즉시) 시크릿 최신화/환경 혼용 점검.
2. (확인) 위조 트래픽 패턴이면 IP 차단.
3. (재발방지) 로테이션 시 동시 지원(구/신) 기간 운영.

---

## 80. Webhook Replay Detected
---
service: integration
error_message: replay detected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:23:00.000Z integration/v1.4.0 [wh3]: Security Alert - webhook replay detected. | Context: {EventId="evt-1001", Seen="true", Age="2h"}

### Root Cause
이벤트 재전송 공격 또는 제공사 재시도(정상)인데 멱등 처리 필요.

### Action Items
1. (즉시) EventId 기반 중복 제거 유지.
2. (확인) 제공사 재전송 정책(정상 범위)인지 확인.
3. (재발방지) webhook 처리 멱등성(이벤트 저장) 강제.

---

## 81. Excessive Permission Granted
---
service: authz-service
error_message: excessive permission granted
---
### Incident Summary
[ERROR] 2024-03-15T11:24:00.000Z authz-service/v1.3.0 [rbac1]: RBAC Alert - excessive permission granted. | Context: {Role="support", Granted="admin:write"}

### Root Cause
Role 정의 오류 또는 관리 콘솔 오조작.

### Action Items
1. (즉시) 과다 권한 회수 및 영향 사용자 확인.
2. (확인) 변경 이력/승인 여부 확인.
3. (재발방지) 권한 변경은 승인 워크플로우 + 정기 권한 리뷰.

---

## 82. Role Mapping Failed
---
service: authz-service
error_message: role mapping failed
---
### Incident Summary
[ERROR] 2024-03-15T11:25:00.000Z authz-service/v1.3.0 [rbac2]: AuthZ Error - role mapping failed. | Context: {User="user_10", Group="grp-unknown"}

### Root Cause
권한 매핑 테이블 누락/동기화 실패.

### Action Items
1. (즉시) 기본 최소 권한 role 부여로 서비스 계속성 확보.
2. (확인) 그룹-롤 매핑 데이터 동기화 점검.
3. (재발방지) 매핑 변경 시 검증 테스트/알림.

---

## 83. Permission Denied Spike
---
service: authz-service
error_message: permission denied
---
### Incident Summary
[WARN] 2024-03-15T11:26:00.000Z authz-service/v1.3.0 [rbac3]: Access Denied - permission denied spike. | Context: {Denied="1200/5m", Endpoint="/v1/admin"}

### Root Cause
정상 사용자에겐 배포 회귀(권한 매핑 깨짐), 공격자에겐 스캐닝.

### Action Items
1. (확인) 사용자군/경로 분석(특정 롤만? 특정 버전만?).
2. (즉시) 배포 회귀면 롤백/핫픽스.
3. (재발방지) 권한 계약 테스트 추가.

---

## 84. Login Anomaly Detected
---
service: auth-security-svc
error_message: login anomaly detected
---
### Incident Summary
[WARN] 2024-03-15T11:27:00.000Z auth-security-svc/v4.2.1 [anom1]: Risk Alert - login anomaly detected. | Context: {User="user_55", Signal="new_device+new_geo", Score="70"}

### Root Cause
계정 탈취 의심 또는 사용자 환경 변화.

### Action Items
1. (즉시) step-up 인증 요구(MFA).
2. (확인) 최근 결제/출금 시도 여부 확인.
3. (재발방지) 리스크 엔진 룰 튜닝 및 사용자 알림 개선.

---

## 85. CAPTCHA Verification Failed
---
service: auth-security-svc
error_message: captcha verification failed
---
### Incident Summary
[WARN] 2024-03-15T11:28:00.000Z auth-security-svc/v4.2.1 [cap1]: Auth Failed - captcha verification failed. | Context: {ClientIP="203.0.113.9", Provider="reCAPTCHA", Error="timeout"}

### Root Cause
CAPTCHA 제공사 장애 또는 네트워크 지연.

### Action Items
1. (즉시) CAPTCHA 실패 시 fallback 정책(간단한 퍼즐/추가 제한) 적용.
2. (확인) 제공사 상태/타임아웃 조정.
3. (재발방지) 멀티 CAPTCHA/캐시 검토.

---

## 86. OTP Provider Timeout
---
service: auth-security-svc
error_message: otp provider timeout
---
### Incident Summary
[ERROR] 2024-03-15T11:29:00.000Z auth-security-svc/v4.2.1 [otp1]: MFA Error - otp provider timeout. | Context: {Provider="SMS-A", Timeout="3s", FailRate="60%"}

### Root Cause
외부 SMS/OTP 제공사 지연.

### Action Items
1. (즉시) 재시도는 큐잉 기반으로 제한, 사용자에게 지연 공지.
2. (즉시) 대체 제공사로 failover(가능 시).
3. (재발방지) 멀티 벤더, SLA 모니터링.

---

## 87. Account Lockout Abuse Detected
---
service: auth-security-svc
error_message: lockout abuse detected
---
### Incident Summary
[WARN] 2024-03-15T11:30:00.000Z auth-security-svc/v4.2.1 [lock1]: Abuse Alert - lockout abuse detected. | Context: {TargetUsers="50", SameIP="198.51.100.99", Pattern="fail-to-lock"}

### Root Cause
로그인 실패를 유도해 계정을 잠그는 서비스 방해 공격.

### Action Items
1. (즉시) 해당 IP/대역 차단, CAPTCHA 강화.
2. (개선) lockout 정책을 계정만이 아니라 IP/디바이스 기반으로도 적용.
3. (재발방지) 사용자 통지 및 self-unlock(안전한) 제공.

---

## 88. Password Hash Algorithm Weak
---
service: auth-security-svc
error_message: weak hash algorithm
---
### Incident Summary
[ERROR] 2024-03-15T11:31:00.000Z auth-security-svc/v4.2.1 [hash1]: Security Alert - weak hash algorithm. | Context: {Algo="SHA1", UsersAffected="12000"}

### Root Cause
레거시 해시 사용으로 침해 시 피해 확대.

### Action Items
1. (즉시) 신규 비밀번호는 강한 해시(Argon2/bcrypt)로 저장.
2. (개선) 로그인 시 점진적 재해싱(마이그레이션).
3. (재발방지) 보안 기준 상향 및 정기 점검.

---

## 89. Plaintext Password Logged
---
service: security
error_message: plaintext password logged
---
### Incident Summary
[CRITICAL] 2024-03-15T11:32:00.000Z security/v1.0.0 [pwlog1]: Security Alert - plaintext password logged. | Context: {Service="auth-security-svc", Logger="debug", Field="password"}

### Root Cause
디버그 로그/요청 바디 로깅이 민감필드를 포함.

### Action Items
1. (즉시) 해당 로깅 비활성화 + 로그 접근 제한.
2. (즉시) 영향 범위 파악 및 비밀번호 재설정 유도(정책에 따라).
3. (재발방지) request/body 로깅은 민감 필드 자동 마스킹 강제.

---

## 90. Zero Trust Policy Violation
---
service: security
error_message: zero trust violation
---
### Incident Summary
[WARN] 2024-03-15T11:33:00.000Z security/v1.0.0 [zt1]: Policy Alert - zero trust violation. | Context: {Service="admin", Access="no-device-posture", User="employee_9"}

### Root Cause
기기 보안 상태 미검증/예외 경로 존재.

### Action Items
1. (즉시) 정책 위반 접근 차단.
2. (확인) 예외 설정 존재 여부 점검.
3. (재발방지) 예외는 승인/기간 제한으로 운영.

---

## 91. Alerting Channel Failure
---
service: security
error_message: alert missed
---
### Incident Summary
[ERROR] 2024-03-15T11:34:00.000Z security/v1.0.0 [al1]: Ops Alert - alert missed. | Context: {Channel="slack", Error="webhook 410", AlertsDropped="25"}

### Root Cause
알림 채널/웹훅 만료로 경보 누락.

### Action Items
1. (즉시) 대체 채널(메일/문자)로 전환.
2. (확인) 웹훅 재발급 및 테스트.
3. (재발방지) 알림 이중화 + 정기 점검 작업.

---

## 92. SOC Escalation Delayed
---
service: security
error_message: soc escalation delayed
---
### Incident Summary
[WARN] 2024-03-15T11:35:00.000Z security/v1.0.0 [soc1]: Process Alert - soc escalation delayed. | Context: {Severity="High", Delay="25m", OnCall="unacked"}

### Root Cause
온콜 부재/프로세스 미흡.

### Action Items
1. (즉시) 대체 담당자 호출/에스컬레이션.
2. (재발방지) 온콜 로테이션/자동 전화 에스컬레이션 도입.

---

## 93. Incident Playbook Missing
---
service: security
error_message: playbook missing
---
### Incident Summary
[ERROR] 2024-03-15T11:36:00.000Z security/v1.0.0 [pb1]: Process Alert - playbook missing. | Context: {Incident="token theft suspected", Owner="security"}

### Root Cause
문서화 부재로 대응 지연.

### Action Items
1. (즉시) 임시 런북 작성(필수 단계: 차단/폐기/증적/공지).
2. (재발방지) 정기 모의훈련 + 플레이북 유지보수.

---

## 94. Evidence Lost
---
service: security
error_message: evidence lost
---
### Incident Summary
[CRITICAL] 2024-03-15T11:37:00.000Z security/v1.0.0 [ev1]: Forensics Alert - evidence lost. | Context: {LogRetention="1d", Needed="30d", Stream="auth-prod"}

### Root Cause
보존 정책 미흡으로 증적 유실.

### Action Items
1. (즉시) 보존 기간 상향, 즉시 스냅샷/아카이빙.
2. (재발방지) 보안 이벤트 로그는 규정에 맞는 보존 정책 적용.

---

## 95. Data Retention Policy Violated
---
service: compliance
error_message: retention violation
---
### Incident Summary
[ERROR] 2024-03-15T11:38:00.000Z compliance/v1.2.0 [ret1]: Compliance Alert - retention violation. | Context: {Dataset="login_attempts", Retain="90d", Actual="365d"}

### Root Cause
자동 삭제 배치 미구현/실패.

### Action Items
1. (즉시) 삭제/익명화 작업 실행(정책 준수).
2. (확인) 배치 실패 원인(권한/스케줄러) 확인.
3. (재발방지) 보존 정책을 코드로 관리(IaC) + 실패 알림.

---

## 96. RBAC Policy Drift
---
service: authz-service
error_message: rbac policy drift
---
### Incident Summary
[WARN] 2024-03-15T11:39:00.000Z authz-service/v1.3.0 [rbacd1]: Policy Alert - rbac policy drift. | Context: {Expected="gitops", Actual="manual edit", Count="12 rules"}

### Root Cause
수동 변경으로 정책 일관성 붕괴.

### Action Items
1. (즉시) GitOps 기준으로 롤백.
2. (재발방지) 정책 변경 승인/리뷰 강제 및 drift 감지 자동화.

---

## 97. Suspicious API Pattern (Scanning)
---
service: api-gateway
error_message: suspicious scanning pattern
---
### Incident Summary
[WARN] 2024-03-15T11:40:00.000Z api-gateway/v3.9.0 [scan1]: Security Alert - suspicious scanning pattern. | Context: {ClientIP="45.12.34.56", Paths="1500/10m", Status="401/403"}

### Root Cause
경로 스캐닝/취약점 탐색.

### Action Items
1. (즉시) IP/대역 차단, WAF 룰 강화.
2. (재발방지) 401/403 폭주 기반 자동 차단 룰.

---

## 98. Security Posture Degraded
---
service: security
error_message: security posture degraded
---
### Incident Summary
[WARN] 2024-03-15T11:41:00.000Z security/v1.0.0 [post1]: Security Posture - security posture degraded. | Context: {OpenFindings="128", Critical="7", Trend="up"}

### Root Cause
미조치 취약점/설정 이슈 누적.

### Action Items
1. (즉시) Critical 7건 우선 조치 계획 수립(오너/기한).
2. (재발방지) 보안 부채 SLO/OKR화 및 정기 점검.

---

## 99. OAuth Consent Abuse Detected
---
service: auth-security-svc
error_message: consent abuse detected
---
### Incident Summary
[WARN] 2024-03-15T11:42:00.000Z auth-security-svc/v4.2.1 [cons1]: Abuse Alert - consent abuse detected. | Context: {ClientIP="203.0.113.250", Requests="300/5m", App="unknown"}

### Root Cause
동의 화면을 자동화로 남용(피싱/스팸/리소스 소모).

### Action Items
1. (즉시) rate-limit + CAPTCHA 적용.
2. (확인) 앱 등록/검증 절차(unknown app) 강화.
3. (재발방지) OAuth 앱 심사/승인 프로세스 도입.

---

## 100. Critical Auth Incident – Potential Token Theft
---
service: auth-security-svc
error_message: potential token theft detected
---
### Incident Summary
[CRITICAL] 2024-03-15T11:43:00.000Z auth-security-svc/v4.2.1 [tokth1]: Security Incident - potential token theft detected. | Context: {User="user_1029", Signal="refresh_reuse+geo_jump+new_device", Severity="Critical"}

### Root Cause
Refresh 재사용 + 위치 급변 + 신규 기기 조합은 토큰 탈취 가능성이 매우 높음.

### Action Items
1. (즉시) 사용자 세션 전면 폐기 + 비밀번호 재설정 강제 + 결제/출금 기능 임시 제한(보호 모드).
2. (즉시) 사건 증적 보존(로그/토큰 발급/요청 트레이스) 및 SOC 에스컬레이션.
3. (확인) 동일 공격 캠페인(연관 IP/UA/ASN) 확산 여부 조사 후 차단 확대.
4. (재발방지) Refresh 토큰 1회성 회전 + 기기 바인딩 + 리스크 기반 step-up + 보안 알림 자동화.

---
