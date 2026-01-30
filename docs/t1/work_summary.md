# 인프라 및약접근제어작업요약
**날짜* 2026-01-29

## 1. 개요
본는문서는 OpSeSe리 로드u관리 방식r개선,w워크로드()o접한안iw결 인Ai경flow)의사항을 접근권한보안 강화그리고권한문제 해결을 위해 수행된 CALI 인프라 변경 사항을 요약합니다

## 2. 주요변변경 사항

### A. OpenSearch 인덱스플템플릿화)인프라강화
-   **기존방방식ll_resource`를 사용하여 를파사용하여u파드l내부에서령ON을 전송.명령어로리하고 에을 전송러 관리가 복잡하고 에러 발생 가능성이 높았음. 발생 가능성이 높았음.
-   **변경방방식rafo `opensear네이티브 ch_index_template` 리소스 도입.리소스 도입
-   **효과드 기반코드 기반((Declarativ)e상태관관리 가능일치설정및불일치이자동감지및수정 용이
-   **관련 파일**:
    -   rraform/03-opensearch.tf` (리소스 정의) (리소스 정의)
    -   erraform/opensearch_template.json` (템플릿 설정 (템플릿 설정 분리) 분리)

### B. S3 접근(제어RSA)
-   **목적flowAi flow와 Coosumm`가버킷에 대해 읽기/쓰기 권 버킷에한대해 읽기/쓰기권권한을수가지되, 최소권한원칙을준수하도록설정
-   **조치*내용
    -   **복구ir: 부분을 원래 상태로 복구 정책을 실수로 변경했던 부분을 원래 상태로.복구
    -   **신규 생성: : S3S읽기/쓰기기전용 정책인 `workload_s3_access`생성
    -   **Rerr 생성**:및 신뢰 관계(OIDC) 설정.를 위한 `airflow_role` 생성 및 신뢰 관계(OIDC) 설정
    -   **권한 연결 `:workload_s3_access` 정`정책을low_role`과 Cons과uCoesumer용용 `app_role에 각각`연결
-   **관련 파일**:
### C. Airflow 설정
-   **문제**: Air설정이 아닌 노드 기본 Role을 사용하고 있어 S3 접근 시 `AccessDenied` 에러 발생.
-   **문제가전용Roe이아닌노드기본을사용하고있어3접근시`AcceDd` 에러 발생
    - 해결용**: Terraform을 통해 Helm Release에 `serviceAccount.annotations.eks.amazonaws.com/role-arn` 주석 추가. 이제 Airflow가 `airflow_role`을 사용합니다.
    -  **: 추후  적용커스:텀Terraform을(통해 Helm 라e브러a리e에 `s용을 대비해`Docker.및u 일 생성 (현s.배포에는 기본 이미지 사용 중).주석추가.이제 가`airfow_ro`을 사용합니다
-   **관련**빌드i준비**: 추후 커스텀 이미지(라이브러리 포함) 사용을 대비해 nfra/terrafor및0-helm-relea파일.생성현재배포에는기본이미지사용중
관련 파일#

-   **검증행및중현재s상태
-   **조치**: `kubectl rollout restart` 명령어로 파드를 재시작하여 변경된 IAM 권한을 적용받도록 함.
-   **결과**: 로앱 (로그 수집기)인 결과 Kinesis로부터 데이터 수신 성공함.
    - 상태: 현재 수정상포실행과중 및 Ki드의sis 연결됨가 맞지 않아 발생하는 Pydantic 에러는 별도 수정 필요.
조치#low (배치 작업)명령어로파드를재시작하여변경된-IAM 권한을 적용받도록 함.
**상태**결과**:✅로그 확인결과로부터데이터수신성공함
-   **결과*참고er 현재 수신되는 로그r포맷과p코드상의 스키마가l맞지므않아 발생하는일Pyd한n  에러는별도수정필요

## 4. 향후 계획 (배치 작업)
-   **상태er**: 실행 중 및 설정B업데이트t완료포맷에 맞춰 Pydantic 모델(`LogRecord`) 수정 필요.
-   **결과botApply를통해올바른IMRol이할당되었으므로,파일접근권한문제해결됨향후계획luent Bt에서 보내는 로그 포맷에 맞춰모델(`LRed`)수정필요`bo3` 외추가라이브러리가필요한경우,아까준비한`bud.f`를활성화하여커스텀이미지를사용하도록전환가능