#!/bin/bash
# =====================================================
# 로컬 개발: 테스트 데이터 생성 스크립트
# =====================================================
# 설명: LocalStack Kinesis에 테스트 로그 전송
# =====================================================

echo "📊 테스트 데이터 생성 중..."

ENDPOINT="http://localhost:4566"
STREAM_NAME="cali-log-stream"

# 샘플 로그 데이터
SAMPLE_LOG='{
  "timestamp": "2026-01-19T14:00:01",
  "level": "ERROR",
  "service": "payment-api",
  "message": "DB Connection timeout",
  "namespace": "production",
  "pod_name": "payment-api-abc123",
  "error_code": "DB_504"
}'

# Kinesis에 데이터 전송
echo "Sending log to Kinesis..."
aws --endpoint-url=$ENDPOINT kinesis put-record \
  --stream-name $STREAM_NAME \
  --partition-key "test" \
  --data "$(echo $SAMPLE_LOG | base64)"

echo "✅ 테스트 데이터 전송 완료!"
