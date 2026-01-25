# Log Generator 배포 가이드

> **목적**: K8s에서 여러 서비스(DB, Web)를 시뮬레이션하는 로그 생성 파드 배포

---

## 🎯 아키텍처

```
EKS Cluster
├─ log-generator-db (Deployment, replicas: 3)
│  └─ 데이터베이스 서버 로그 생성
│
├─ log-generator-web (Deployment, replicas: 3)
│  └─ 웹 서버 로그 생성
│
└─ log-generator-api (Deployment, replicas: 2)
   └─ API 서버 로그 생성

각 Pod → stdout 로그 출력 → Fluent Bit 수집 → Kinesis
```

---

## 📂 폴더 구조

```
log-generator/
├── Dockerfile
├── main.py                      # 로그 생성 로직
└── config.yaml                  # 서비스별 설정
```

---

## 🔧 K8s Deployment 예시

### **k8s/log-generator-deployment.yaml**

```yaml
---
# DB 서버 시뮬레이션
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator-db
  namespace: default
  labels:
    app: log-generator
    service: database
spec:
  replicas: 3
  selector:
    matchLabels:
      app: log-generator
      service: database
  template:
    metadata:
      labels:
        app: log-generator
        service: database
    spec:
      containers:
      - name: log-generator
        image: <ECR_URL>/log-generator:latest
        env:
        - name: SERVICE_NAME
          value: "postgres-db"
        - name: LOG_LEVEL
          value: "ERROR,WARN,INFO"
        - name: ERROR_RATE
          value: "0.1"  # 10% 에러율
        resources:
          limits:
            memory: "128Mi"
            cpu: "100m"

---
# Web 서버 시뮬레이션
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator-web
  namespace: default
  labels:
    app: log-generator
    service: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: log-generator
      service: web
  template:
    metadata:
      labels:
        app: log-generator
        service: web
    spec:
      containers:
      - name: log-generator
        image: <ECR_URL>/log-generator:latest
        env:
        - name: SERVICE_NAME
          value: "nginx-web"
        - name: LOG_LEVEL
          value: "ERROR,WARN,INFO"
        - name: ERROR_RATE
          value: "0.05"  # 5% 에러율

---
# API 서버 시뮬레이션
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator-api
  namespace: default
  labels:
    app: log-generator
    service: api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: log-generator
      service: api
  template:
    metadata:
      labels:
        app: log-generator
        service: api
    spec:
      containers:
      - name: log-generator
        image: <ECR_URL>/log-generator:latest
        env:
        - name: SERVICE_NAME
          value: "payment-api"
        - name: LOG_LEVEL
          value: "ERROR,WARN"
        - name: ERROR_RATE
          value: "0.15"  # 15% 에러율
```

---

## 🐍 Python 코드 예시

### **log-generator/main.py**

```python
import time
import random
import json
import os
from datetime import datetime
from faker import Faker

fake = Faker()
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
ERROR_RATE = float(os.getenv("ERROR_RATE", "0.1"))

# 에러 메시지 템플릿
ERROR_TEMPLATES = [
    "DB Connection timeout after 5s",
    "OutOfMemoryError: Java heap space",
    "ConnectionRefused: Redis connection failed",
    "Timeout: HTTP request to external API exceeded 10s",
    "NullPointerException at line 42",
]

def generate_log():
    """랜덤 로그 생성"""
    level = random.choices(
        ["INFO", "WARN", "ERROR"],
        weights=[0.7, 0.2, 0.1]
    )[0]
    
    if level == "ERROR" and random.random() < ERROR_RATE:
        message = random.choice(ERROR_TEMPLATES)
    else:
        message = f"{fake.word()} request processed successfully"
    
    log = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "service": SERVICE_NAME,
        "message": message,
        "trace_id": fake.uuid4(),
    }
    
    print(json.dumps(log))

if __name__ == "__main__":
    while True:
        generate_log()
        time.sleep(random.uniform(1, 5))  # 1-5초마다 로그 생성
```

---

## 🚀 배포 방법

### **CI/CD 자동 배포**

```bash
# 1. 코드 수정
vim log-generator/main.py

# 2. Git push
git push

# ✅ GitHub Actions가 자동으로:
# - Docker 이미지 빌드
# - ECR 푸시
# - EKS 배포 (8개 Pod 모두 업데이트)
```

---

### **수동 배포 (테스트)**

```bash
# 1. Docker 이미지 빌드
docker build -t log-generator ./log-generator

# 2. ECR 푸시
docker tag log-generator:latest <ECR_URL>/log-generator:latest
docker push <ECR_URL>/log-generator:latest

# 3. K8s 배포
kubectl apply -f k8s/log-generator-deployment.yaml

# 4. Pod 확인
kubectl get pods -l app=log-generator

# 출력:
# NAME                                  READY   STATUS
# log-generator-db-abc123               1/1     Running
# log-generator-db-def456               1/1     Running
# log-generator-db-ghi789               1/1     Running
# log-generator-web-jkl012              1/1     Running
# log-generator-web-mno345              1/1     Running
# log-generator-web-pqr678              1/1     Running
# log-generator-api-stu901              1/1     Running
# log-generator-api-vwx234              1/1     Running
```

---

## 🔍 로그 확인

```bash
# 특정 서비스 로그 확인
kubectl logs -l service=database --tail=20

# 모든 로그 생성기 로그 확인
kubectl logs -l app=log-generator -f

# 로그 흐름 추적
kubectl logs -l app=log-generator | grep ERROR
```

---

## 📊 Pod 분산 구성

| 서비스 | Replicas | 목적 | 에러율 |
|--------|---------|------|--------|
| **log-generator-db** | 3 | DB 서버 시뮬레이션 | 10% |
| **log-generator-web** | 3 | Web 서버 시뮬레이션 | 5% |
| **log-generator-api** | 2 | API 서버 시뮬레이션 | 15% |
| **Total** | **8 Pods** | 다양한 서비스 환경 재현 | |

---

## 💡 확장 방법

### **새로운 서비스 추가**

```yaml
# k8s/log-generator-deployment.yaml에 추가
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: log-generator-cache
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: log-generator
        env:
        - name: SERVICE_NAME
          value: "redis-cache"
```

### **에러율 조정**

```yaml
# deployment.yaml 수정 후 git push
env:
- name: ERROR_RATE
  value: "0.3"  # 30%로 증가
```

---

*최종 업데이트: 2026-01-25*
