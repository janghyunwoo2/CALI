# ==============================================================================
# CALI Infrastructure - Kinesis Data Stream & Firehose
# ==============================================================================
# Kinesis Stream (중앙 버퍼) + Firehose 2개 (S3, OpenSearch)
# ==============================================================================

# ------------------------------------------------------------------------------
# Kinesis Data Stream
# ------------------------------------------------------------------------------
resource "aws_kinesis_stream" "logs" {
  name             = "${var.project_name}-logs-stream"
  shard_count      = 1
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  tags = {
    Name = "${var.project_name}-logs-stream"
  }
}

# ------------------------------------------------------------------------------
# Firehose #1: Kinesis → S3 (raw/ 백업용)
# ------------------------------------------------------------------------------
resource "aws_kinesis_firehose_delivery_stream" "to_s3" {
  name        = "${var.project_name}-firehose-to-s3"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.logs.arn
    role_arn           = aws_iam_role.firehose.arn
  }

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose.arn
    bucket_arn = aws_s3_bucket.logs.arn
    prefix              = "raw/dt=!{timestamp:yyyy-MM-dd}/"
    error_output_prefix = "raw-error/result=!{firehose:error-output-type}/"

    buffering_size     = 5
    buffering_interval = 60

    compression_format = "GZIP"

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/kinesisfirehose/${var.project_name}-to-s3"
      log_stream_name = "S3Delivery"
    }
  }

  tags = {
    Name = "${var.project_name}-firehose-to-s3"
  }
}

# ------------------------------------------------------------------------------
# Firehose #2: Kinesis → OpenSearch
# ------------------------------------------------------------------------------
resource "aws_kinesis_firehose_delivery_stream" "to_opensearch" {
  name        = "${var.project_name}-firehose-to-opensearch"
  destination = "opensearch"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.logs.arn
    role_arn           = aws_iam_role.firehose.arn
  }

  opensearch_configuration {
    domain_arn = aws_opensearch_domain.logs.arn
    role_arn   = aws_iam_role.firehose.arn
    index_name = "cali-logs"

    buffering_interval = 60
    buffering_size     = 5

    retry_duration = 300

    s3_backup_mode = "FailedDocumentsOnly"

    s3_configuration {
      role_arn   = aws_iam_role.firehose.arn
      bucket_arn = aws_s3_bucket.logs.arn
      prefix     = "firehose-failed/"

      buffering_size     = 5
      buffering_interval = 60

      compression_format = "GZIP"
    }

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = "/aws/kinesisfirehose/${var.project_name}-to-opensearch"
      log_stream_name = "OpenSearchDelivery"
    }
  }

  tags = {
    Name = "${var.project_name}-firehose-to-opensearch"
  }
}
