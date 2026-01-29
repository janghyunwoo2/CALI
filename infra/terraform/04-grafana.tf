# ==============================================================================
# CALI Infrastructure - AWS Managed Grafana (주석 처리됨)
# ==============================================================================
# Helm으로 EKS에 직접 Grafana 배포 예정 (helm-values/grafana.yaml)
# AWS SSO 없이 사용 가능하도록 변경
# ==============================================================================

# ------------------------------------------------------------------------------
# Grafana Workspace (AWS Managed Grafana) - SSO 필요하여 주석 처리
# ------------------------------------------------------------------------------
# resource "aws_grafana_workspace" "main" {
#   name                     = "${var.project_name}-grafana"
#   account_access_type      = "CURRENT_ACCOUNT"
#   authentication_providers = ["AWS_SSO"]
#   permission_type          = "SERVICE_MANAGED"
#   role_arn                 = aws_iam_role.grafana.arn
#
#   data_sources = ["AMAZON_OPENSEARCH_SERVICE"]
#
#   tags = {
#     Name = "${var.project_name}-grafana"
#   }
# }

# ------------------------------------------------------------------------------
# Grafana Service Account - 주석 처리
# ------------------------------------------------------------------------------
# resource "aws_grafana_workspace_service_account" "main" {
#   name         = "terraform-service-account"
#   grafana_role = "ADMIN"
#   workspace_id = aws_grafana_workspace.main.id
# }
