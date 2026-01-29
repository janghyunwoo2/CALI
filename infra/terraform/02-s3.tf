# ==============================================================================
# CALI Infrastructure - S3 Bucket
# ==============================================================================
# 로그 저장용 S3 버킷 (raw/, new_errors/)
# ==============================================================================

# ------------------------------------------------------------------------------
# S3 Bucket
# ------------------------------------------------------------------------------
# data "aws_caller_identity" "current" {} # 이미 06-iam.tf에 정의됨

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${data.aws_caller_identity.current.account_id}"

  force_destroy = true

  tags = {
    Name = "${var.project_name}-logs"
  }
}

# ------------------------------------------------------------------------------
# Bucket Versioning
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ------------------------------------------------------------------------------
# Bucket Encryption (SSE-S3)
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ------------------------------------------------------------------------------
# Block Public Access
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ------------------------------------------------------------------------------
# Lifecycle Rules (비용 최적화)
# ------------------------------------------------------------------------------
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "archive-old-logs"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }

  rule {
    id     = "cleanup-failed-firehose"
    status = "Enabled"

    filter {
      prefix = "firehose-failed/"
    }

    expiration {
      days = 7
    }
  }
}
