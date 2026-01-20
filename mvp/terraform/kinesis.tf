# =====================================================
# Kinesis Stream 리소스
# =====================================================
# 설명: LocalStack에 Kinesis Data Stream 생성
# MVP용 단일 샤드, 24시간 보존
# =====================================================

resource "aws_kinesis_stream" "cali_log_stream" {
  name             = "cali-log-stream"
  shard_count      = 1  # MVP용 단일 샤드
  retention_period = 24 # 24시간 보존

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
  ]

  tags = {
    Environment = "local"
    Project     = "CALI"
    Purpose     = "MVP"
  }
}

# Output
output "kinesis_stream_name" {
  description = "Kinesis Stream 이름"
  value       = aws_kinesis_stream.cali_log_stream.name
}

output "kinesis_stream_arn" {
  description = "Kinesis Stream ARN"
  value       = aws_kinesis_stream.cali_log_stream.arn
}
