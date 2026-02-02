# ==============================================================================
# CALI Infrastructure - Metrics Server
# ==============================================================================
# HPA (Horizontal Pod Autoscaler)를 위한 메트릭 수집 서버
# ==============================================================================

resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  namespace  = "kube-system"
  version    = "3.11.0"

  set {
    name  = "args[0]"
    value = "--kubelet-insecure-tls"
  }

  # EKS Node Group 이후 설치
  depends_on = [
    aws_eks_node_group.main
  ]
}
