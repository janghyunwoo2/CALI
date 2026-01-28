resource "helm_release" "airflow" {
  name             = "airflow"
  repository       = "https://airflow.apache.org"
  chart            = "airflow"
  version          = "1.11.0"
  namespace        = "airflow"
  create_namespace = true

  values = [
    file("${path.module}/../helm-values/airflow.yaml")
  ]

  depends_on = [
    kubernetes_storage_class.gp2
  ]
}

resource "helm_release" "milvus" {
  name             = "milvus"
  repository       = "https://zilliztech.github.io/milvus-helm/"
  chart            = "milvus"
  version          = "4.1.11"
  namespace        = "milvus"
  create_namespace = true

  values = [
    file("${path.module}/../helm-values/milvus.yaml")
  ]

  depends_on = [
    kubernetes_storage_class.gp2
  ]
}

resource "helm_release" "fluent_bit" {
  name             = "fluent-bit"
  repository       = "https://fluent.github.io/helm-charts"
  chart            = "fluent-bit"
  version          = "0.47.7"
  namespace        = "logging"
  create_namespace = true

  values = [
    file("${path.module}/../helm-values/fluent-bit.yaml")
  ]
}

# Grafana (Optional - commented out or active based on preference)
resource "helm_release" "grafana" {
  name             = "grafana"
  repository       = "https://grafana.github.io/helm-charts"
  chart            = "grafana"
  version          = "7.0.0"
  namespace        = "monitoring"
  create_namespace = true

  values = [
    file("${path.module}/../helm-values/grafana.yaml")
  ]
}
