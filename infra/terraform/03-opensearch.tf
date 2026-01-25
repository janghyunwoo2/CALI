# ==============================================================================
# CALI Infrastructure - OpenSearch Domain
# ==============================================================================
# 로그 인덱싱 및 검색용 OpenSearch Service
# ==============================================================================

# ------------------------------------------------------------------------------
# OpenSearch Domain
# ------------------------------------------------------------------------------
resource "aws_opensearch_domain" "logs" {
  domain_name    = "${var.project_name}-logs"
  engine_version = "OpenSearch_2.11"

  cluster_config {
    instance_type  = "t3.small.search"
    instance_count = 1

    zone_awareness_enabled = false
  }

  ebs_options {
    ebs_enabled = true
    volume_type = "gp3"
    volume_size = 20
  }

  encrypt_at_rest {
    enabled = true
  }

  node_to_node_encryption {
    enabled = true
  }

  domain_endpoint_options {
    enforce_https       = true
    tls_security_policy = "Policy-Min-TLS-1-2-2019-07"
  }

  advanced_security_options {
    enabled                        = true
    internal_user_database_enabled = true

    master_user_options {
      master_user_name     = "admin"
      master_user_password = var.opensearch_master_password
    }
  }

  access_policies = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.firehose.arn
        }
        Action   = "es:*"
        Resource = "arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.project_name}-logs/*"
      },
      {
        Effect = "Allow"
        Principal = {
          AWS = aws_iam_role.grafana.arn
        }
        Action = [
          "es:ESHttpGet",
          "es:ESHttpPost"
        ]
        Resource = "arn:aws:es:${var.aws_region}:${data.aws_caller_identity.current.account_id}:domain/${var.project_name}-logs/*"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-logs"
  }
}

# ------------------------------------------------------------------------------
# OpenSearch Password (Secrets Manager 권장)
# ------------------------------------------------------------------------------
variable "opensearch_master_password" {
  description = "OpenSearch 마스터 비밀번호 (최소 8자, 대소문자+숫자+특수문자)"
  type        = string
  sensitive   = true
}
