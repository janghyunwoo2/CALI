# **🚀 [최종본 v4.0] 프로젝트 명: CALI (Cloud-native AI Log Insight)**

**팀명:** AIOps 엔지니어즈 | **작성일:** 2026-01-22 | **팀원:** 팀원A, 팀원B

---

## **1. 프로젝트 개요**

- **배경:** 분산 환경(EKS)의 방대한 비정형 로그는 장애 원인 파악을 어렵게 하며, 기존의 사후 분석 방식은 즉각적인 대응에 한계가 있음.
- **목표:** 비정형 로그 실시간 정제, **OpenSearch 기반 시각화**, **AI(RAG) 기반 지능형 추론**을 결합하여 장애 복구 시간(MTTR)을 혁신적으로 단축하는 플랫폼 구축.
- **타겟:** 신속한 장애 대응이 필수적인 핀테크/커머스 기업의 SRE 및 개발팀.

---

## **2. 기존 방식 대비 개선점 (As-Is vs. To-Be)**

| **구분** | **기존 방식 (As-Is)** | **제안 서비스 (To-Be)** | **기대 효과** |
| --- | --- | --- | --- |
| **핵심 프로세스** | 수동 로그 검색 및 분석 (ELK 등) | AI 기반 실시간 장애 원인 추론 리포팅 | 장애 복구 시간(MTTR) 80% 단축 |
| **데이터 활용** | 비정형 텍스트 로그 (단순 적재) | **Regex + Pydantic 정제** 및 벡터화(RAG) | 로그 데이터의 지식 자산화 및 가치 창출 |
| **사용자 경험** | 엔지니어가 직접 원인을 가설/검증 | **Slack으로 분석 결과 및 조치 가이드 수신** | 의사 결정 속도 및 업무 효율성 극대화 |

---

## **3. 시스템 아키텍처 (System Architecture)**

### Production 아키텍처
- **Data Flow:** Raw Logs → **Fluent Bit (1차 JSON 정제)** → **Kinesis Stream** (Fan-out 중심)
- **실시간 분석 (Fast Path):** Kinesis Stream → **Consumer (Pydantic 검증 + ERROR/WARN 필터링)** → Milvus 검색 → LLM 분석 → **Slack 알림 (Throttling 적용)**
- **시각화/저장 (Slow Path):** Consumer → **OpenSearch 인덱싱** (**Grafana** 시각화) / **S3 백업** (데이터 격리 DLQ 포함)

---

## **4. 데이터 흐름 및 단계별 예시 (Data Flow Example)**

| **단계** | **처리 주체** | **데이터 입/출력 예시** |
| --- | --- | --- |
| **Raw Log** | **App Pod** | [ERROR] payment-api: DB Connection timeout at 14:00:01 |
| **1차 정형화** | **Fluent Bit** | {"timestamp": "14:00:01", "level": "ERROR", "service": "payment", "log_content": "..."} |
| **2차 검증** | **Consumer** | Pydantic LogEntry(level="ERROR", service="payment-api") - 검증 성공 |
| **필터링** | **Consumer** | level == "ERROR" → 처리 대상 (INFO는 스킵) |
| **AI 분석** | **RAG/LLM** | {"cause": "DB 과부하", "action": "커넥션 풀 상향 조정"} |
| **최종 알림** | **Slack** | 🚨 [장애] payment-api 에러 발생 (과거 사례와 95% 일치). [가이드 확인] |

---

## **5. 상세 기술 스택 (Tech Stack)**

- **Infrastructure:** Terraform, AWS EKS, **Amazon Kinesis Data Stream**
- **Logging/Analytics:** **Fluent Bit (Multiline 파서)**, Amazon OpenSearch Service, **Grafana**
- **Data & AI:** Python 3.13, **Pydantic**, **Faker (로그 생성)**, OpenAI API (GPT-4o), **Milvus (Vector DB)**, Regex
- **Orchestration:** Apache Airflow (**KubernetesPodOperator**)
- **Data Quality:** **Great Expectations (GE)**

---

## **6. 주요 기능 정의**

### 핵심 기능
1. **Fluent Bit Multiline 파싱**: Java/Python 스택 트레이스 15-30줄을 하나로 묶어 처리
2. **Pydantic 스키마 검증**: Consumer에서 로그 필드 타입 검증 (실패 시 DLQ)
3. **ERROR/WARN 필터링**: Consumer가 중요 로그만 선별 처리
4. **Slack 실시간 알림**: Webhook을 통한 즉각적인 장애 통지 (Throttling 적용)
5. **OpenSearch 통합 분석**: Grafana 대시보드 및 전문 검색
6. **RAG 기반 지능형 분석**: Milvus + OpenAI를 활용한 할루시네이션 없는 조치 권고
7. **데이터 품질 보증 (GE)**: Airflow를 통한 S3 데이터 무결성 검증

---

## **7. 개발 일정 (WBS - 5일 완성 전략)**

> **핵심 전략**: Day 1 각자 MVP 완성 + 통합 → Day 2-3 추가 기능 → Day 4-5 최종 완성 + 배포

### **Day 1: 역할별 MVP 완성 + 통합** ⚡

**목표**: 각자의 핵심 기능을 완성하고, 오후에 통합하여 기본 파이프라인 동작 확인

#### 오전 (각자 독립 작업)
- **역할 1 (인프라)**: VPC, Kinesis Stream, S3 버킷, IAM, Secrets Manager 설정
- **역할 2 (실시간 파이프라인)**: Fluent Bit 배포, Multiline 파서, Kinesis Output 연동
- **역할 3 (배치 파이프라인)**: Airflow LocalExecutor 환경 구축, S3 연결 테스트 DAG
- **역할 4 (Consumer + RAG)**: Kinesis 폴링, Pydantic 검증, ERROR/WARN 필터링, Slack 연동

#### 오후 (통합 작업)
- **통합 테스트**: 로그 생성 → Fluent Bit → Kinesis → Consumer → Slack 전체 파이프라인 검증
- **완료 기준**: 전체 파이프라인 정상 동작

---

### **Day 2: RAG 기초 + OpenSearch 구축**

- **역할 1**: OpenSearch 도메인 생성, 인덱스 접근 권한 설정
- **역할 2**: OpenSearch 인덱스 매핑 설계, 인덱싱 로직 구현
- **역할 3**: Great Expectations 환경 설정, S3 로그 스키마 검증
- **역할 4**: Milvus 배포, 컬렉션 스키마 설계, OpenAI Embedding 연동

---

### **Day 3: RAG 실시간 분석 + Grafana 시각화**

- **역할 1**: CI/CD 기초 (ECR, GitHub Actions)
- **역할 2**: Grafana 대시보드 구축 (실시간 에러 현황, 서비스별 통계)
- **역할 3**: Airflow DAG 고도화 (S3 → Milvus 업데이트, GE 통합)
- **역할 4**: 실시간 RAG 분석 완성 (Milvus 검색 → OpenAI 분석 → Slack AI 알림)

---

### **Day 4: 통합 테스트 및 안정화**

- **전체 협업**: E2E 테스트, 성능 테스트, 에러 처리 강화
- **역할별 개선**: 인프라 안정화, 대시보드 고도화, 품질 리포트 자동화, RAG 프롬프트 튜닝

---

### **Day 5: 프로덕션 배포 및 문서화**

- **배포 작업**: Consumer Docker 이미지 빌드, EKS 배포, CI/CD 파이프라인 완성
- **문서화**: README 업데이트, 운영 가이드, API 문서 작성
- **최종 검증**: 프로덕션 환경 시뮬레이션, 팀 데모

---

## **8. 역할 및 책임 (4인 체제)**

| 역할 | 담당 영역 |
|------|----------|
| **역할 1: 인프라** | Terraform, AWS EKS, Kinesis, S3, OpenSearch, Firehose 구축 및 관리 |
| **역할 2: 실시간 파이프라인** | Fluent Bit, OpenSearch 인덱싱, Grafana 대시보드 구축 |
| **역할 3: 배치 파이프라인** | Airflow DAG 작성, Great Expectations 데이터 품질 관리 |
| **역할 4: Consumer + 전체 RAG** | Kinesis 폴링, Pydantic 검증, Slack 알림, **RAG 구축 및 분석** (Milvus + OpenAI) |

---

*최종 업데이트: 2026-01-23*
*작성자: CALI 프로젝트 팀*
