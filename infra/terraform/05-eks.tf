# ==============================================================================
# CALI Infrastructure - EKS Cluster
# ==============================================================================
# Amazon EKS 클러스터 및 Node Group
# ==============================================================================

# ------------------------------------------------------------------------------
# VPC (기본 VPC 사용 또는 신규 생성)
# ------------------------------------------------------------------------------
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# ------------------------------------------------------------------------------
# EKS Cluster
# ------------------------------------------------------------------------------
resource "aws_eks_cluster" "main" {
  name     = "${var.project_name}-cluster"
  role_arn = aws_iam_role.eks_cluster.arn
  version  = "1.29"

  vpc_config {
    subnet_ids              = data.aws_subnets.default.ids
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator"]

  depends_on = [
    aws_iam_role_policy_attachment.eks_cluster_policy
  ]

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ------------------------------------------------------------------------------
# EKS Node Group
# ------------------------------------------------------------------------------
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.project_name}-node-group"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = data.aws_subnets.default.ids

  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"

  scaling_config {
    desired_size = 2
    min_size     = 2
    max_size     = 4
  }

  update_config {
    max_unavailable = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry
  ]

  tags = {
    Name = "${var.project_name}-node-group"
  }
}

# ------------------------------------------------------------------------------
# EKS Access Entries (팀원 접근 권한)
# ------------------------------------------------------------------------------
# 변수(team_members_arns)에 등록된 팀원들에게 관리자(Admin) 권한 부여

resource "aws_eks_access_entry" "team_members" {
  for_each      = toset(var.team_members_arns)
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = each.value
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "team_members_admin" {
  for_each      = toset(var.team_members_arns)
  cluster_name  = aws_eks_cluster.main.name
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
  principal_arn = each.value

  access_scope {
    type = "cluster"
  }
}

# ------------------------------------------------------------------------------
# OIDC Provider (IRSA용)
# ------------------------------------------------------------------------------
data "tls_certificate" "eks" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "eks" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

# ------------------------------------------------------------------------------
# EKS Addons - EBS CSI Driver
# ------------------------------------------------------------------------------
resource "aws_eks_addon" "ebs_csi" {
  cluster_name  = aws_eks_cluster.main.name
  addon_name    = "aws-ebs-csi-driver"
  addon_version = "v1.31.0-eksbuild.1" # Safe version for 1.29

  depends_on = [
    aws_eks_node_group.main,
    aws_iam_role_policy_attachment.eks_ebs_csi_driver_policy
  ]
}

# ------------------------------------------------------------------------------
# EBS CSI Driver IAM Policy for Node Group
# ------------------------------------------------------------------------------
resource "aws_iam_role_policy_attachment" "eks_ebs_csi_driver_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.eks_node.name
}
