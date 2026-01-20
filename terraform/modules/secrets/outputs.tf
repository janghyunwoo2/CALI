# =====================================================
# Secrets Manager 모듈 - 출력 값
# =====================================================

output "opensearch_secret_arn" {
  description = "OpenSearch 자격증명 Secret ARN"
  value       = "" # TODO: Secret 생성 후 참조
}

output "openai_secret_arn" {
  description = "OpenAI API Key Secret ARN"
  value       = "" # TODO: Secret 생성 후 참조
}

# TODO: 추가 출력 값 정의
