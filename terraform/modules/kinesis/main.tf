# =====================================================
# Kinesis 모듈 - 메인 설정
# =====================================================
# 설명: Fan-out 아키텍처로 효율적인 데이터 라우팅
# 
# 아키텍처:
# Fluent Bit → Kinesis Data Stream (단일 진입점)
#   ↓
#   ├─→ Consumer (실시간 구독 - Lambda/ECS)
#   └─→ Kinesis Firehose (자동 전달)
#         ↓
#       ├─→ OpenSearch (검색/시각화)
#       └─→ S3 (영구 백업)
#
# 장점:
# 1. 네트워크 효율: Fluent Bit은 한 곳(Stream)에만 전송
# 2. 버퍼링: Stream이 로그 폭주 시 안정적으로 처리
# 3. 실시간/배치 분리: Stream(실시간) / Firehose(배치)
# =====================================================

# TODO: Kinesis Data Stream 리소스
# resource "aws_kinesis_stream" "cali_log_stream" {
#   name             = "cali-log-stream"
#   shard_count      = 2
#   retention_period = 24  # 24시간 보존
#   
#   shard_level_metrics = [
#     "IncomingBytes",
#     "OutgoingBytes",
#   ]
#   
#   encryption_type = "KMS"
#   kms_key_id      = aws_kms_key.kinesis.id
#
#   tags = {
#     Environment = var.environment
#     Project     = "CALI"
#   }
# }

# TODO: Kinesis Firehose - Stream에서 자동 전달받음
# resource "aws_kinesis_firehose_delivery_stream" "opensearch" {
#   name        = "cali-log-firehose-opensearch"
#   destination = "opensearch"
#
#   kinesis_source_configuration {
#     kinesis_stream_arn = aws_kinesis_stream.cali_log_stream.arn
#     role_arn           = aws_iam_role.firehose.arn
#   }
#
#   opensearch_configuration {
#     domain_arn = var.opensearch_domain_arn
#     index_name = "cali-logs"
#     
#     s3_configuration {
#       role_arn   = aws_iam_role.firehose.arn
#       bucket_arn = var.backup_bucket_arn
#       prefix     = "backup/"
#     }
#   }
# }

# TODO: Kinesis Firehose - S3 백업 전용
# resource "aws_kinesis_firehose_delivery_stream" "s3_backup" {
#   name        = "cali-log-firehose-s3"
#   destination = "extended_s3"
#
#   kinesis_source_configuration {
#     kinesis_stream_arn = aws_kinesis_stream.cali_log_stream.arn
#     role_arn           = aws_iam_role.firehose.arn
#   }
#
#   extended_s3_configuration {
#     role_arn   = aws_iam_role.firehose.arn
#     bucket_arn = var.backup_bucket_arn
#     prefix     = "logs/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
#     
#     compression_format = "GZIP"
#     buffer_size        = 5   # 5 MB
#     buffer_interval    = 300 # 5분
#   }
# }
