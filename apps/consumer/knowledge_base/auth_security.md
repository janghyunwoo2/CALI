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
