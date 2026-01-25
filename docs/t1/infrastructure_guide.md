# CALI 인프라 구축 가이드 (GitOps)

> **방식**: GitOps - Git이 모든 배포의 유일한 진실  
> **업데이트**: 2026-01-25

---

## 🎯 핵심 개념

### **모든 배포는 CI/CD로 자동화**

| 도구 | 대상 | 트리거 |
|------|------|--------|
| **Terraform CI/CD** | AWS 인프라 | `terraform/**` 변경 시 |
| **Helm CI/CD** | K8s 오픈소스 | `helm-values/**` 변경 시 |
| **App CI/CD** | 직접 작성 코드 | `log-generator/**`, `consumer/**` 변경 시 |

**핵심**: 모든 작업 = `git push`

---

## 📋 배포 대상

| 리소스 | CI/CD 파일 | 트리거 |
|--------|-----------|--------|
| **Kinesis, S3, OpenSearch, Grafana, EKS, IAM, ECR** | `terraform.yml` | `terraform/*.tf` |
| **Fluent Bit, Milvus, Airflow** | `helm.yml` | `helm-values/*.yaml` |
| **Log Generator** | `log-generator.yml` | `log-generator/**` |
| **Consumer** | `consumer.yml` | `consumer/**` |

---

## 🔄 워크플로우

```
코드 수정 → git push → GitHub Actions 자동 실행 → Slack 알림
```

---

## 📂 폴더 구조

```
CALI/
├── .github/workflows/      # CI/CD (4개)
├── terraform/              # AWS 인프라 (10개 파일)
├── helm-values/            # Helm 설정 (3개)
├── k8s/                    # K8s 매니페스트 (2개)
├── log-generator/          # 로그 생성기
├── consumer/               # Consumer
├── README.md
└── .gitignore
```

**Terraform 파일**:
- `01-kinesis.tf` (Stream + Firehose 2개)
- `02-s3.tf`, `03-opensearch.tf`, `04-grafana.tf`
- `05-eks.tf`, `06-iam.tf`, `07-ecr.tf`
- `providers.tf`, `backend.tf`, `outputs.tf`

---

## 🚀 초기 설정

### **1. 기본 파일 생성**
- `.gitignore`, `README.md`

### **2. GitHub Secrets**
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `SLACK_WEBHOOK_URL`

### **3. CI/CD 파일**
- 4개 워크플로우 파일 작성

### **4. 첫 배포**
```bash
git push origin main  # 자동 배포 시작
```

---

## 🔧 일상 작업

### **Terraform 수정**
```bash
vim terraform/02-s3.tf
git push  # → PR → plan 확인 → 승인 → apply
```

### **Helm 설정 변경**
```bash
vim helm-values/fluent-bit-values.yaml
git push  # → 자동 upgrade
```

### **앱 코드 변경**
```bash
vim consumer/main.py
git push  # → 빌드 → ECR → EKS
```

---

## 💡 GitOps 장점

| 기존 | GitOps |
|------|--------|
| ❌ 이력 없음 | ✅ Git 기록 |
| ❌ 롤백 어려움 | ✅ `git revert` |
| ❌ 수동 배포 | ✅ 완전 자동화 |

---

## 💰 월 비용: ~$182

- EKS: $73, EC2: $30, OpenSearch: $40, 기타: $39

---

## ✅ Quick Reference

| 작업 | 방법 |
|------|------|
| **배포** | `git push` |
| **Plan 확인** | PR → Actions 탭 |
| **롤백** | `git revert` → `git push` |

---

## 🎯 핵심 원칙

1. Git이 유일한 진실
2. 수동 실행 금지
3. PR 리뷰 필수
4. 모든 변경 추적
5. `git revert`로 롤백

---

*최종 업데이트: 2026-01-25*
