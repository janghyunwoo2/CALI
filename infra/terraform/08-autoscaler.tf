# ==============================================================================
# CALI Infrastructure - Cluster Autoscaler
# ==============================================================================
# Helm을 사용해 Cluster Autoscaler 설치
# ==============================================================================

resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  namespace  = "kube-system"
  version    = "9.34.0" # EKS 1.29 호환 버전 확인 필요

  values = [
    yamlencode({
      autoDiscovery = {
        clusterName = aws_eks_cluster.main.name
      }
      awsRegion = var.aws_region
      rbac = {
        serviceAccount = {
          create = true
          name   = "cluster-autoscaler"
          annotations = {
            "eks.amazonaws.com/role-arn" = aws_iam_role.cluster_autoscaler.arn
          }
        }
      }
    })
  ]

  # 불필요한 리소스 생성을 막고, 안전하게 삭제되도록 설정
  force_update  = true
  recreate_pods = true
}
