# Airflow 배포 이슈 해결 및 최적화 작업 요약

**날짜:** 2026-01-30  
**상태:** 진행 중 (인프라 반영 및 최종 검증 단계)

## 1. 주요 문제 및 해결 내용

### 1-1. PostgreSQL 이미지 풀 오류 (`ErrImagePull`)
- **문제:** Helm 차트 기본 설정의 Postgres 이미지 태그가 유효하지 않아 배포가 중단됨.
- **해결:** `airflow.yaml`에 ECR 기반의 안정적인 이미지(`cali/postgres:11`)를 명시적으로 설정하여 해결.

### 1-2. 라이브러리(`openai` 등) 설치 실패
- **문제:** `extraInitContainers` 설정을 파일 루트 레벨에 정의했으나, 최신 Airflow Helm 차트에서 이를 인식하지 못해 라이브러리 설치가 누락됨.
- **해결:** 설정을 각 컴포넌트(`scheduler`, `webserver`, `triggerer`) 하위로 이동시켜 파드 생성 시 반드시 `install-requirements` 컨테이너가 포함되도록 수정.

### 1-3. 설정 관리 및 구조 최적화
- **Terraform 설정 통합:** `10-helm-releases.tf`에 분산되어 있던 수많은 `set` 블록을 `helm-values/airflow.yaml` 파일로 통합하여 가시성과 유지보수성 향상.
- **YAML Anchor 도입:** 각 컴포넌트(Scheduler, Webserver, Triggerer)에 중복되던 Init Container 및 Volume 설정을 YAML Anchor(`&`, `*`) 기능을 사용하여 획기적으로 중복 제거 및 리팩토링 수행.

### 1-4. GitSync 설정 복구
- **문제:** 리팩토링 작업 중 실수로 `dags` (GitSync) 설정 블록이 삭제됨.
- **해결:** 즉시 해당 블록을 복구하여 GitHub(`feat/t4/airflow` 브랜치)의 DAG 파일이 실시간 동기화되도록 조치.

## 2. 현재 상태 (2026-01-30 14:40 기준)
- **Terraform Apply 상황:** `airflow.yaml` 리팩토링 후 반영 중, 파드들이 새로 생성되면서 `Init` 상태에 머물러 있어 타임아웃 발생.
- **진단:** 파드들이 DB 마이그레이션(`wait-for-airflow-migrations`) 또는 라이브러리 설치 단계에서 지연되고 있는 것으로 보임.

## 3. 향후 계획 (Next Steps)
1. **Init 지연 해결:** `kubectl describe` 및 로그 분석을 통해 파드가 `Init` 상태에서 넘어가지 못하는 구체적인 원인 해결.
2. **현업 스타일 개선 (Long-term):** 현재의 Init Container 방식 대신, 전용 Docker 이미지를 빌드하여 ECR에 올리고 이를 사용하는 방식으로 전환 (배포 속도 및 안정성 극대화).
3. **DAG 검증:** 라이브러리 설치 완료 후, `openai` 모듈 import 에러가 해결되었는지 최종 확인.
