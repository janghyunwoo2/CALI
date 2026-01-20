# =====================================================
# Kinesis 모듈 - 메인 설정
# =====================================================
# 설명: Kinesis Data Stream과 Firehose 구성
# Fast Path: Stream → Consumer → Milvus/LLM
# Slow Path: Firehose → OpenSearch & S3
# =====================================================

# TODO: Kinesis 리소스 정의
# - Kinesis Data Stream (샤드 2개, 24시간 보존, KMS 암호화)
# - Kinesis Firehose (OpenSearch 목적지)
# - Kinesis Firehose (S3 백업 목적지)
