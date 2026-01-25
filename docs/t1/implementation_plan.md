# Day 1-1: CALI 인프라 Terraform 구축 계획

CALI 프로젝트의 AWS 인프라를 Terraform으로 구축합니다. VPC, EKS, Kinesis, S3, OpenSearch, ECR, Secrets Manager 등 핵심 컴포넌트를 모듈화하여 관리합니다.

## User Review Required

> [!IMPORTANT]
> **리전 선택**: 기본 리전을 `ap-northeast-2` (서울)로 설정했습니다. 변경이 필요하면 알려주세요.

> [!IMPORTANT]
> **OpenSearch 인스턴스 타입**: 개발 환경으로 `t3.small.search`를 사용합니다. 프로덕션 환경에서는 더 큰 인스턴스가 필요할 수 있습니다.

> [!IMPORTANT]
> **EKS 노드 그룹**: 기본 2개 노드 (`t3.medium`)로 시작합니다. 워크로드에 따라 조정이 필요할 수 있습니다.

> [!WARNING]
> **비용 관리**: OpenSearch와 EKS는 시간당 과금되므로, 개발 시간 외에는 중지하는 것을 권장합니다.

---

## Proposed Changes

### Terraform 프로젝트 구조

```
terraform/
├── main.tf                 # 메인 설정 및 모듈 통합
├── variables.tf            # 입력 변수 정의
├── outputs.tf              # 출력 값 정의
├── versions.tf             # Provider 버전 관리
├── terraform.tfvars        # 환경별 변수 값
├── modules/
│   ├── vpc/                # VPC 및 네트워크
│   ├── eks/                # EKS 클러스터
│   ├── kinesis/            # Kinesis Stream & Firehose
│   ├── s3/                 # S3 버킷
│   ├── opensearch/         # OpenSearch 도메인
│   ├── ecr/                # ECR 리포지토리
│   ├── secrets/            # Secrets Manager
│   └── iam/                # IAM 역할 및 정책
└── .github/
    └── workflows/
        └── terraform.yml   # GitHub Actions CI/CD
```

---

### 1. VPC 모듈

VPC, 서브넷(Public/Private), NAT Gateway, Internet Gateway, Route Table을 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/vpc/main.tf)

**주요 구성**:
- VPC CIDR: `10.0.0.0/16`
- 가용 영역(AZ): 3개 (고가용성)
- Public 서브넷: 3개 (각 AZ당 1개)
- Private 서브넷: 3개 (EKS 워커 노드용)
- Database 서브넷: 3개 (OpenSearch용)
- NAT Gateway: 3개 (각 AZ당 1개, 고가용성)

---

### 2. EKS 모듈

EKS 클러스터, 노드 그룹, OIDC Provider를 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/eks/main.tf)

**주요 구성**:
- EKS 버전: `1.31` (최신 안정 버전)
- 노드 그룹: `t3.medium` 2-4개 (Auto Scaling)
- IRSA (IAM Roles for Service Accounts) 활성화
- VPC CNI, CoreDNS, kube-proxy 애드온
- CloudWatch 로깅 활성화 (API, Audit, Authenticator)

---

### 3. Kinesis 모듈

Kinesis Data Stream과 Kinesis Data Firehose를 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/kinesis/main.tf)

**주요 구성**:
- **Data Stream**: 
  - 샤드 수: 2개 (Auto Scaling 가능)
  - 보존 기간: 24시간
  - 암호화: KMS 사용
- **Data Firehose**:
  - 목적지 1: OpenSearch (실시간 분석)
  - 목적지 2: S3 (백업 및 DLQ)
  - 버퍼링: 5MB 또는 60초
  - 압축: GZIP

---

### 4. S3 모듈

로그 백업, DLQ(Dead Letter Queue), Terraform 상태 저장용 버킷을 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/s3/main.tf)

**주요 구성**:
- **로그 백업 버킷**:
  - 버전 관리 활성화
  - 라이프사이클: 30일 후 Glacier, 90일 후 삭제
  - 암호화: AES256
- **DLQ 버킷**:
  - 처리 실패 로그 저장
- **Terraform 상태 버킷**:
  - 버전 관리 및 암호화
  - DynamoDB 테이블로 상태 잠금

---

### 5. OpenSearch 모듈

OpenSearch 도메인 및 접근 정책을 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/opensearch/main.tf)

**주요 구성**:
- 엔진 버전: `OpenSearch_2.11` (최신 안정 버전)
- 인스턴스: `t3.small.search` 3개 (Multi-AZ)
- EBS 볼륨: 20GB (GP3)
- VPC 내부 배치 (Private 서브넷)
- 마스터 사용자: Secrets Manager로 관리
- 엔드포인트: HTTPS 강제

---

### 6. ECR 모듈

Docker 이미지 저장소를 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/ecr/main.tf)

**주요 구성**:
- 리포지토리:
  - `cali/fluent-bit`: Fluent Bit 커스텀 이미지
  - `cali/consumer`: Python Consumer 이미지
  - `cali/api`: (향후) API 서버 이미지
- 이미지 스캔: Push 시 자동 스캔
- 라이프사이클: 최근 10개 이미지만 유지

---

### 7. Secrets Manager 모듈

민감 정보(OpenSearch 자격 증명, OpenAI API Key 등)를 관리합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/secrets/main.tf)

**주요 구성**:
- OpenSearch 마스터 사용자 이름/비밀번호
- OpenAI API Key
- Slack Webhook URL
- Milvus 연결 정보
- 자동 교체 정책 (OpenSearch 비밀번호: 30일)

---

### 8. IAM 모듈

EKS 노드, Fluent Bit, Consumer, Firehose를 위한 IAM 역할 및 정책을 구성합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/modules/iam/main.tf)

**주요 구성**:
- **EKS 노드 역할**:
  - ECR 접근
  - CloudWatch Logs 쓰기
- **Fluent Bit Service Account 역할** (IRSA):
  - Kinesis PutRecord/PutRecords
- **Consumer Service Account 역할** (IRSA):
  - Kinesis GetRecords/GetShardIterator
  - Secrets Manager 읽기
  - S3 쓰기 (DLQ)
- **Firehose 역할**:
  - S3 쓰기
  - OpenSearch 쓰기

---

### 9. 메인 Terraform 설정

모듈을 통합하고 변수를 관리합니다.

#### [NEW] [main.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/main.tf)

모든 모듈을 호출하고 상호 의존성을 연결합니다.

#### [NEW] [variables.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/variables.tf)

프로젝트명, 환경, 리전 등 공통 변수를 정의합니다.

#### [NEW] [outputs.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/outputs.tf)

EKS 클러스터명, OpenSearch 엔드포인트, ECR URL 등을 출력합니다.

#### [NEW] [versions.tf](file:///c:/Users/3571/Desktop/projects/CALI/terraform/versions.tf)

Terraform 및 Provider 버전을 고정합니다.

#### [NEW] [terraform.tfvars](file:///c:/Users/3571/Desktop/projects/CALI/terraform/terraform.tfvars)

실제 사용할 변수 값을 설정합니다.

---

### 10. GitHub Actions CI/CD

Terraform 인프라를 자동으로 검증하고 배포합니다.

#### [NEW] [terraform.yml](file:///c:/Users/3571/Desktop/projects/CALI/.github/workflows/terraform.yml)

**주요 구성**:
- **트리거**: `terraform/` 디렉터리 변경 시
- **Job**:
  1. `terraform fmt -check` (포맷 검증)
  2. `terraform validate` (문법 검증)
  3. `terraform plan` (변경 사항 미리보기)
  4. `terraform apply` (main 브랜치에 머지 시 자동 배포)
- **시크릿**:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `TF_STATE_BUCKET` (S3 백엔드)

---

## Verification Plan

### 1. Terraform 로컬 검증

```bash
# Terraform 초기화
cd terraform
terraform init

# 포맷 확인
terraform fmt -recursive -check

# 문법 검증
terraform validate

# 플랜 확인 (실제 배포 없이)
terraform plan -out=tfplan
```

### 2. 인프라 배포 테스트

```bash
# 실제 배포
terraform apply tfplan

# 출력 확인
terraform output
```

### 3. 리소스 검증

- **VPC**: AWS 콘솔에서 서브넷 및 라우팅 테이블 확인
- **EKS**: `kubectl get nodes` 로 노드 상태 확인
- **Kinesis**: AWS 콘솔에서 스트림 생성 확인
- **S3**: 버킷 생성 및 정책 확인
- **OpenSearch**: VPC 엔드포인트 접근 가능 여부 확인
- **ECR**: 리포지토리 생성 확인
- **Secrets Manager**: 시크릿 생성 확인

### 4. GitHub Actions 검증

- PR 생성 시 `terraform plan` 자동 실행 확인
- main 브랜치 머지 시 `terraform apply` 자동 실행 확인

---

## 다음 단계

1. **사용자 승인 대기**: 이 계획을 검토하고 승인해 주세요.
2. **Terraform 코드 작성**: 승인 후 모든 모듈 및 설정 파일을 생성합니다.
3. **로컬 검증**: Terraform 명령어로 문법 및 플랜을 확인합니다.
4. **인프라 배포**: 실제 AWS 리소스를 생성합니다.
5. **Day 1-2로 이동**: Terraform 모듈화 및 변수 관리 최적화를 진행합니다.
