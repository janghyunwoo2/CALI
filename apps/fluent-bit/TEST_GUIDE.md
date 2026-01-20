# Fluent Bit 설정 테스트 가이드

## 📋 설정 개요

Fluent Bit이 수집하는 로그는 다음과 같이 처리됩니다:

### 1. Multiline 처리
여러 줄로 나오는 에러 로그(스택 트레이스 등)를 하나의 로그로 묶습니다.

**감지 규칙**:
- 타임스탬프로 시작하는 줄 (예: `2026-01-19 14:00:01`)
- 로그 레벨로 시작하는 줄 (예: `[ERROR]`, `ERROR:`)

**예시**:
```
[ERROR] payment-api: DB Connection timeout
  at com.example.Service.connect()
  at com.example.Main.run()
```
→ 3줄이 하나의 로그로 묶임

### 2. 헤더 파싱
로그의 핵심 정보만 추출합니다:
- `timestamp`: 로그 발생 시간
- `level`: 로그 레벨 (ERROR, WARN, INFO 등)
- `service`: 서비스명
- `message`: 나머지 전체 메시지 (에러 전문 포함)

### 3. 원본 보존
파싱된 필드 외에도 원본 로그 전체를 `log_content` 필드에 보존합니다.
→ 데이터 유실 방지!

---

## 🧪 테스트 방법

### 로컬 테스트 (Docker)

```bash
# 1. Fluent Bit 이미지 빌드
cd apps/fluent-bit
docker build -t cali-fluent-bit:test .

# 2. 테스트 로그 파일 생성
cat > /tmp/test.log <<EOF
[ERROR] 2026-01-19 14:00:01 payment-api: DB Connection timeout
  at com.example.PaymentService.connect(PaymentService.java:42)
  at com.example.Main.run(Main.java:15)
[INFO] 14:00:02 order-service: Processing order #12345
ERROR: AuthService authentication failed for user@example.com
Stack trace:
  File "auth.py", line 123, in authenticate
  File "main.py", line 45, in login
EOF

# 3. Fluent Bit 실행
docker run --rm \
  -v $(pwd)/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf \
  -v $(pwd)/parsers.conf:/fluent-bit/etc/parsers.conf \
  -v /tmp/test.log:/var/log/test.log \
  cali-fluent-bit:test
```

### 기대 출력 (JSON)

```json
{
  "timestamp": "2026-01-19 14:00:01",
  "level": "ERROR",
  "service": "payment-api",
  "message": "DB Connection timeout\n  at com.example.PaymentService.connect(PaymentService.java:42)\n  at com.example.Main.run(Main.java:15)",
  "log_content": {
    "log": "[ERROR] 2026-01-19 14:00:01 payment-api: DB Connection timeout\n  at com.example.PaymentService..."
  },
  "kubernetes": {
    "pod_name": "payment-api-7d8f9c-abc123",
    "namespace": "production",
    "container_name": "payment-api"
  },
  "collected_at": "2026-01-19T14:00:01Z"
}
```

---

## 📝 지원하는 로그 패턴

### 패턴 1: 표준 형식
```
[ERROR] 2026-01-19 14:00:01 payment-api: DB Connection timeout
```

### 패턴 2: 간단한 형식
```
ERROR: payment-api DB Connection timeout
```

### 패턴 3: 타임스탬프 없음
```
[ERROR] payment-api: Something went wrong
```

### 패턴 4: 여러 줄 스택 트레이스
```
[ERROR] service-name: Error message
  at package.Class.method(File.java:123)
  at package.Main.run(Main.java:45)
  Caused by: java.sql.SQLException
    at database.Connection.connect()
```

모두 정상적으로 파싱됩니다!

---

## ⚠️ 주의사항

1. **정규식 조정**: 실제 애플리케이션 로그 패턴에 맞게 `parsers.conf`의 정규식을 조정하세요.

2. **Multiline 타임아웃**: `Flush_timeout 1000` (1초)으로 설정됨. 너무 짧으면 로그가 잘릴 수 있음.

3. **메모리 제한**: `Mem_Buf_Limit 5MB` - 큰 로그 파일 처리 시 증가 필요.

---

## 🔧 커스터마이징

### 다른 로그 레벨 추가
`parsers.conf`의 정규식에서:
```regex
(?<level>ERROR|WARN|WARNING|INFO|DEBUG|FATAL|CRITICAL|TRACE)
```
→ `TRACE` 추가됨

### 서비스명 패턴 변경
현재: `[a-zA-Z0-9_-]+` (영숫자, 하이픈, 언더스코어)
특수문자 추가 필요 시 정규식 수정

---

## 🚀 다음 단계

1. ✅ Fluent Bit 설정 완료
2. 📦 Docker 이미지 빌드
3. ☸️ Kubernetes DaemonSet 배포
4. 🧪 실제 애플리케이션 로그 테스트
5. 🔍 Consumer에서 파싱된 로그 확인
