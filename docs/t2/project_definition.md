# CALI (Cloud-Native Auto Log Intelligence) 프로젝트 정의서

## 1. 개요 (Overview)
본 문서는 대규모 분산 환경(EKS)에서 발생하는 **비정형 로그(Unstructured Log)**를 실시간으로 수집·분석하고, **RAG(Retrieval-Augmented Generation)** 기술을 활용해 장애 원인을 즉각 추론하여 자동 리포팅하는 지능형 관제 플랫폼의 아키텍처를 정의한다.

**핵심 목표:**
1. **MTTR 단축:** 장애 발생 시 로그 분석 시간을 분 단위에서 '초 단위'로 단축.
2. **지능형 분석:** 기존 키워드 매칭의 한계를 넘어, 과거 유사 장애 사례(Vector DB)를 기반으로 한 문맥적 원인 추론.
3. **운영 자동화:** 장애 감지부터 원인 분석, 조치 가이드 제공까지의 과정을 사람의 개입 없이 자동화.

---

## 2. 전체 아키텍처 (Architecture)

**전략:** 대량의 로그를 안정적으로 처리하기 위해 **Kinesis(Streaming)**를 버퍼로 활용하고, **Milvus(Vector DB)**와 **OpenAI(LLM)**를 결합하여 분석 품질을 극대화한다.

### 2.1 데이터 파이프라인 (Data Pipeline)
*   **Source**: EKS 내 마이크로서비스 (Application Logs)
*   **Ingestion**: Fluentd / Logstash → **Amazon Kinesis Data Stream**
*   **Processing**: **Python Consumer (CALI Engine)**
    *   *Preprocessing*: 노이즈(IP, Timestamp) 제거 및 정규화
    *   *Embedding*: `text-embedding-3-small` 모델 활용
*   **Storage**:
    *   *Vector DB*: **Milvus** (과거 장애 패턴 및 해결책 저장)
    *   *Data Lake*: S3 (원본 로그 장기 보관 및 DLQ)

### 2.2 지능형 분석 흐름 (Intelligence Flow)
1.  **Anomaly Detection**: Consumer가 에러 로그 패턴 감지.
2.  **RAG Search**: Milvus에서 유사한 과거 장애 사례 검색 (Cache Hit 전략 적용).
    *   *High Similarity (< 0.35)*: 검증된 과거 해결책 즉시 반환 (비용 절감).
    *   *Low Similarity*: LLM(GPT-4o)이 상세 원인 정밀 분석 수행.
3.  **Actionable Alerting**: "근본 원인"과 "실행 가능한 조치 명령어(kubectl, SQL)"를 포함하여 Slack 전송.

---

## 3. 핵심 기술 (Key Technologies)
*   **Compute**: AWS EKS (Kubernetes)
*   **Streaming**: Amazon Kinesis
*   **AI/ML**: OpenAI API (GPT-4o), LangChain Concept (Custom Implementation)
*   **Database**: Milvus (Vector Search), Redis (Throttling)
*   **DevOps**: Docker, ArgoCD (GitOps)
