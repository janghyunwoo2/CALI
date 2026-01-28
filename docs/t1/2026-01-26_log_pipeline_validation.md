# CALI 프로젝트 진행 리포트 (2026-01-26)

## 1. 개요
EKS 클러스터 내의 로그 파이프라인(Log Generator -> Fluent Bit -> Kinesis -> Firehose -> S3/OpenSearch)을 검증하고, Grafana를 통한 시각화 환경을 구축함.

## 2. 주요 진행 사항
- **Log Generator 배포**: 실시간 테스트 로그 생성을 위한 Python 스크립트 기반 Pod 배포 완료.
- **파이프라인 데이터 흐름 확인**:
    - Fluent Bit가 Kinesis Stream으로 로그 전송 확인.
    - Firehose를 통해 S3 버킷(`raw/` 경로)에 로그 적재 확인.
    - OpenSearch 인덱스(`cali-logs*`) 생성 확인.
- **Grafana 연동**: OpenSearch 데이터 소스 등록 및 Explore 메뉴를 통한 쿼리 환경 구성.

## 3. 시행착오 및 트러블슈팅 (Troubleshooting)

### 이슈 1: Grafana 시계열 데이터(Timestamp) 인식 불가
- **현상**: "No date field named @timestamp found" 에러 발생.
- **원인**: Kubernetes CRI 로그 포맷(나노초 포함)을 Fluent Bit가 제대로 파싱하지 못해 `@timestamp` 필드가 누락됨.
- **시도**: 
    1. CRI Regex Parser 적용. (나노초 포맷 불일치로 실패)
    2. `iso8601` 포맷 적용. (실패)
- **최종 전략**: 파싱에 의존하지 않고, Fluent Bit의 Output 설정에서 `Time_Key @timestamp`를 사용하여 **Ingestion Time(수집 시간)**을 강제 주입하도록 설정.

### 이슈 2: 설정 변경 미반영 (가짜 재시작 현상)
- **현상**: ConfigMap 수정 후 `kubectl rollout restart`를 실행했으나 S3 데이터 형식이 바뀌지 않음.
- **확인 결과**: Pod의 AGE가 5시간 전으로 고정되어 있었음. `rollout restart`가 실제 Pod 교체를 유발하지 않은 상태.
- **해결**: `kubectl delete pod -l app.kubernetes.io/name=fluent-bit` 명령으로 파드를 강제 삭제하여 새 설정을 즉시 반영하도록 조치.

### 이슈 3: Fluent Bit CrashLoopBackOff
- **현상**: 설정 수정 후 파드가 계속 재시작되며 죽음.
- **원인**: `modify` 필터 내에서 존재하지 않는 필드를 `Rename` 하려 했거나, 빈 `[FILTER]` 블록이 설정에 포함되어 초기화 실패.
- **해결**: 불필요한 필터 블록을 제거하고 설정을 단순화하여 안정화.

## 4. 향후 과제 (Next Steps)
- [ ] Fluent Bit 가동 상태 최종 확인 (현재 최신 패치 적용 대기 중).
- [ ] Airflow를 통한 배치 파이프라인(S3 -> OpenSearch/Milvus) 검증.
- [ ] AI 분석(RAG) 레이어 연동 테스트.

---
**기록자**: CALI 인프라 에이전트
**상태**: 실시간 파이프라인 검증 90% 완료 (타임스탬프 필드 주입 설정 완료)
