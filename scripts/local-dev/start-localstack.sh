# =====================================================
# 로컬 개발: LocalStack 시작 스크립트
# =====================================================
# 설명: AWS 서비스를 로컬에서 에뮬레이션
# 용도: Kinesis, S3 등 로컬 테스트
# =====================================================

#!/bin/bash

echo "🚀 LocalStack 시작..."

docker run -d \
  --name cali-localstack \
  -p 4566:4566 \
  -p 4571:4571 \
  -e SERVICES=kinesis,s3,secretsmanager \
  -e DEBUG=1 \
  -e DATA_DIR=/tmp/localstack/data \
  localstack/localstack:latest

echo "✅ LocalStack이 시작되었습니다."
echo "엔드포인트: http://localhost:4566"
echo ""
echo "Kinesis Stream 생성 예시:"
echo "aws --endpoint-url=http://localhost:4566 kinesis create-stream --stream-name cali-log-stream --shard-count 1"
