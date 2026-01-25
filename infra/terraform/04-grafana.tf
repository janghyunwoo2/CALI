# ==============================================================================
# CALI Infrastructure - AWS Managed Grafana
# ==============================================================================
# OpenSearch 데이터 소스 연결 Grafana 워크스페이스
# ==============================================================================

# ------------------------------------------------------------------------------
# Grafana Workspace
# ------------------------------------------------------------------------------
resource "aws_grafana_workspace" "main" {
  name                     = "${var.project_name}-grafana"
  account_access_type      = "CURRENT_ACCOUNT"
  authentication_providers = ["AWS_SSO"]
  permission_type          = "SERVICE_MANAGED"
  role_arn                 = aws_iam_role.grafana.arn

  data_sources = ["AMAZON_OPENSEARCH_SERVICE"]

  tags = {
    Name = "${var.project_name}-grafana"
  }
}

# ------------------------------------------------------------------------------
# Grafana Role Policy (서비스 관리형)
# ------------------------------------------------------------------------------
resource "aws_grafana_workspace_service_account" "main" {
  name         = "terraform-service-account"
  grafana_role = "ADMIN"
  workspace_id = aws_grafana_workspace.main.id
}
