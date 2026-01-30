# ConfigMap for Airflow Python requirements

resource "kubernetes_config_map" "airflow_requirements" {
  metadata {
    name      = "airflow-requirements"
    namespace = "airflow"
  }

  data = {
    "requirements.txt" = file("${path.module}/../../apps/airflow/requirements.txt")
  }
}

resource "helm_release" "airflow" {
  name             = "airflow"
  repository       = "https://airflow.apache.org"
  chart            = "airflow"
  version          = "1.15.0"
  namespace        = "airflow"
  create_namespace = true

  values = [
    file("${path.module}/../helm-values/airflow.yaml")
  ]

  timeout = 900
  wait    = true



  # Global ServiceAccount annotation (fallback)
  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.airflow_role.arn
  }

  # Component-specific ServiceAccount annotations (Crucial for effective IRSA)
  set {
    name  = "scheduler.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.airflow_role.arn
  }
  set {
    name  = "webserver.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.airflow_role.arn
  }
  set {
    name  = "triggerer.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.airflow_role.arn
  }
  set {
    name  = "workers.serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.airflow_role.arn
  }

  # Use Custom ECR Image for Airflow
  set {
    name  = "images.airflow.repository"
    value = aws_ecr_repository.airflow_custom.repository_url
  }
  set {
    name  = "images.airflow.tag"
    value = "latest"
  }
  set {
    name  = "images.airflow.pullPolicy"
    value = "Always"
  }

  depends_on = [
    kubernetes_storage_class.gp2,
    kubernetes_config_map.airflow_requirements,
    null_resource.airflow_custom_build
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

resource "kubernetes_namespace" "logging" {
  metadata {
    name = "logging"
  }
}

resource "kubernetes_config_map" "fluent_bit_config" {
  metadata {
    name      = "fluent-bit-custom-config"
    namespace = kubernetes_namespace.logging.metadata[0].name
  }

  data = {
    "fluent-bit.conf" = file("${path.module}/../../apps/fluent-bit/fluent-bit.conf")
    "parsers.conf"    = file("${path.module}/../../apps/fluent-bit/parsers.conf")
  }
}

resource "helm_release" "fluent_bit" {
  name       = "fluent-bit"
  repository = "https://fluent.github.io/helm-charts"
  chart      = "fluent-bit"
  version    = "0.47.7"
  namespace  = kubernetes_namespace.logging.metadata[0].name
  # create_namespace removed because we manage it explicitly

  values = [
    file("${path.module}/../helm-values/fluent-bit.yaml")
  ]

  depends_on = [
    kubernetes_config_map.fluent_bit_config
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

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = aws_iam_role.grafana.arn
  }
}
