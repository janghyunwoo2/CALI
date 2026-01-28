# CALI Infra & Deployment Guide

## 1. Terraform (Infrastructure)

### 작업 위치
`cd infra/terraform`

### 주요 명령어
| 목적 | 명령어 |
| :--- | :--- |
| **초기화** | `terraform init` |
| **문법 검증** | `terraform validate` |
| **계획 확인** (변경점) | `terraform plan` |
| **배포/적용** | `terraform apply -auto-approve` |
| **삭제** (전체 리소스) | `terraform destroy -auto-approve` |
| **출력 값 보기** (ARN/URL) | `terraform output` |

### 🧹 완벽한 삭제 (Deep Clean)
**Terraform 삭제 전 실행 권장** (EBS 볼륨, 로드밸런서 잔존 방지)
```bash
# 1. 모든 K8s 리소스 및 PVC(볼륨) 삭제
kubectl delete all --all -n default
kubectl delete pvc --all -n default
kubectl delete ingress --all -n default

# 2. Terraform 삭제 수행
terraform destroy -auto-approve
```

---

## 2. EKS Deployment (Services)

### 사전 준비
```bash
# EKS 연결 설정 (최초 1회)
aws eks update-kubeconfig --name cali-cluster --region ap-northeast-2
```

### 👥 팀원 EKS 접근 가이드
팀원들이 클러스터에 접속하려면 다음 절차를 따르세요.

**1. 준비물**
*   AWS CLI 및 kubectl 설치
*   `aws configure`로 **본인의 IAM User 키** 설정

**2. 실행 명령어 (터미널)**
```bash
# EKS 연결 정보(kubeconfig) 다운로드
aws eks update-kubeconfig --name cali-cluster --region ap-northeast-2

# 접속 테스트
kubectl get nodes
```

### 서비스별 배포 명령어
#### 0) sc 생성(pvc 용) airflow, milvus 용
kubectl apply -f ../k8s/storage-class.yaml && kubectl get sc

#### 1) Fluent Bit (로그 수집)
```bash
# 1. ConfigMap 배포 (설정 먼저!)
kubectl apply -k apps/fluent-bit/

# 2. Helm 차트 배포 (앱 실행)
helm upgrade --install fluent-bit fluent/fluent-bit -f infra/helm-values/fluent-bit.yaml

# (옵션) 파드 재시작 (설정 변경 시)
kubectl rollout restart daemonset fluent-bit

# (삭제) 서비스 제거
helm uninstall fluent-bit
```

#### 2) Milvus (Vector DB)
```bash
# Helm 차트 배포
helm upgrade --install milvus milvus/milvus -f infra/helm-values/milvus.yaml

# (옵션) 파드 재시작
kubectl rollout restart deployment -l app.kubernetes.io/instance=milvus

# (삭제) 서비스 제거
helm uninstall milvus
```

#### 3) Airflow (배치 파이프라인)
```bash
# Helm 차트 배포
helm upgrade --install airflow apache-airflow/airflow -f infra/helm-values/airflow.yaml --namespace airflow --create-namespace

# (옵션) 파드 재시작 (Webserver & Scheduler)
kubectl rollout restart deployment airflow-webserver -n airflow
kubectl rollout restart deployment airflow-scheduler -n airflow

# (삭제) 서비스 제거
helm uninstall airflow -n airflow
```

#### 4) Grafana (시각화)
```bash
# Helm 차트 배포
helm upgrade --install grafana grafana/grafana -f infra/helm-values/grafana.yaml

# (옵션) 파드 재시작
kubectl rollout restart deployment grafana

# (삭제) 서비스 제거
helm uninstall grafana
```

#### 5) Consumer (로그 분석기)
**※ 주의: 커스텀 앱은 빌드 및 이미지 푸시가 선행되어야 합니다.**

**(1) 이미지 빌드 & 푸시**
```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com

# 빌드
docker build -t cali/consumer ./apps/consumer

# 태그 & 푸시
docker tag cali/consumer:latest <ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/cali/consumer:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-northeast-2.amazonaws.com/cali/consumer:latest
```

**(2) 배포**
```bash
# 매니페스트 배포
kubectl apply -f k8s/consumer-deployment.yaml

# (옵션) 파드 재시작
kubectl rollout restart deployment consumer

# (삭제) 서비스 제거
kubectl delete -f k8s/consumer-deployment.yaml
```

#### 6) Log Generator (테스트용)
**※ 주의: ECR 푸시 필요 (Consumer와 동일 방식)**

```bash
# 매니페스트 배포
kubectl apply -f k8s/log-generator-deployment.yaml

# (옵션) 파드 재시작
kubectl rollout restart deployment log-generator

# (삭제) 서비스 제거
kubectl delete -f k8s/log-generator-deployment.yaml
```

---



## 3. 유용한 확인 명령어

| 목적 | 명령어 |
| :--- | :--- |
| **파드 상태 확인** | `kubectl get pods -A` |
| **특정 파드 로그** | `kubectl logs -f <pod-name>` |
| **ConfigMap 확인** | `kubectl get cm` |
| **서비스(IP) 확인** | `kubectl get svc` |
