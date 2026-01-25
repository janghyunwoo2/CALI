# CALI 프로젝트 통합 WBS (5일 완성 전략)

> **핵심 전략**: Day 1 각자 MVP 완성 + 통합 → Day 2-3 추가 기능 → Day 4-5 최종 완성 + 배포

---

## 📋 역할 및 책임 (4인 체제)

| 역할 | 담당 영역 |
|------|----------|
| **역할 1** | 인프라 (Terraform, EKS, Kinesis, S3, OpenSearch, firehose) |
| **역할 2** | 실시간 파이프라인 (Fluent Bit, OpenSearch, Grafana) |
| **역할 3** | 배치 파이프라인 (Airflow, 데이터 품질 관리) |
| **역할 4** | Consumer + **전체 RAG** (Kinesis 폴링, Slack, **RAG 구축 + 분석**) |

---

## 📅 5일 개발 일정

### **Day 1: 역할별 MVP 완성 + 통합** ⚡

**목표**: 각자의 핵심 기능을 완성하고, 오후에 통합하여 기본 파이프라인 동작 확인

#### 오전 (각자 독립 작업)

##### 역할 1: 인프라 (Terraform)
- [ ] VPC 및 네트워크 기본 설정
- [ ] Kinesis Data Stream 생성 (샤드 1개) -> 파이어 호스도 필요함(s3랑 opensearch로 보내는 용)
- [ ] S3 버킷 2개 (백업용, DLQ용) -> 버킷 하나로
- [ ] IAM Role 및 정책 설정
- [ ] Secrets Manager에 Slack Webhook, OpenAI Key 등록
- [ ] **완성 기준**: `terraform apply` 성공 및 모든 리소스 접근 가능-> 지금 필요한 모든 서비스를 테라폼으로 관리 할 수 있나? 로그 생성기, 그라파다, 키네시스, 파이어호스, 컨슈머, 플루언트비트 등

##### 역할 2: 실시간 파이프라인 (Fluent Bit)
- [ ] Fluent Bit 배포(docker-compose) <- 내가 수정했음
- [ ] Multiline 파서 설정 (Stacktrace 처리)
- [ ] Regex 헤더 추출 (timestamp, level, service)
- [ ] Kinesis Output 플러그인 설정 + 파이어호스 까지
- [ ] 로그 생성기 연동 테스트(로그 생성기 말고 단순하게 플루언트 비트로 전송하는 mvp 기능, 로그 생성기로 보내는 건 mvp 이후에)
- [ ] **완성 기준**: 로그 → Fluent Bit → Kinesis 정상 전송 + 파이어호스로 전송 -> s3&오픈서치 -> 그라파다 (우선적으로 로그 생성기에서 그라파다까지 데이터 가는 것을 테스트 하기 위함)

##### 역할 3: 배치 파이프라인 (Airflow)
- [ ] Airflow LocalExecutor 환경 구축
- [ ] Web UI 접근 확인
- [ ] S3 연결 테스트 DAG 작성
- [ ] 간단한 샘플 DAG 실행 (S3 읽기 → 변환 → S3 쓰기)
- [ ] **완성 기준**: Airflow에서 샘플 DAG 정상 실행

##### 역할 4: Consumer (Kinesis 폴링 + Slack)
- [ ] boto3 Kinesis GetRecords 폴링 루프 구현
- [ ] Pydantic LogRecord 스키마 정의 및 검증
- [ ] ERROR/WARN 필터링 로직
- [ ] Slack Webhook 연동
- [ ] Throttling (중복 알림 방지) 로직
- [ ] S3 원본 로그 백업
- [ ] **완성 기준**: Kinesis → Consumer → Slack 알림 정상 동작(키네시스에서 데이터 입력 받는다고 가정하고 개발 하는게 좋겠음 구지 키네시스에서 데이터가 저 오는 것은 구현하지 않고)

#### 오후 (통합 작업 - 전체 협업)

- [ ] **통합 테스트 시나리오 실행**
  1. 로그 생성기 실행 (다양한 레벨 로그)
  2. Fluent Bit → Kinesis 전송 확인
  3. Consumer 폴링 및 ERROR/WARN 필터링 확인
  4. Slack 알림 도착 확인
  5. S3 백업 확인

- [ ] **통합 이슈 해결**
  - 데이터 포맷 불일치 조정
  - 권한 문제 해결
  - 네트워크 연결 확인

- [ ] **Day 1 완료 기준**: 로그 생성 → Fluent Bit → Kinesis → Consumer → Slack 전체 파이프라인 정상 동작
-> 시스템이 전체적으로 동작하는지 확인하는 것이 목표
---

### **Day 2-3: 추가 기능 구현** 🚀

**목표**: RAG 분석, 시각화, 데이터 품질 검증 등 고급 기능 추가-> 이때부터 로그 생성기로 데이터 보내서 통합 된 환경에서 개발

#### Day 2: RAG 기반 분석 + OpenSearch 기초
=> 위 요구 조건과 1일차 mvp 일정에 맞게 싹 수정
##### 역할 1: OpenSearch 인프라
- [ ] OpenSearch 도메인 생성 (t3.small 단일 노드)
- [ ] 인덱스 접근 권한 설정
- [ ] 역할 2/4 지원 (연결 테스트)

##### 역할 2: OpenSearch 인덱싱
- [ ] OpenSearch 인덱스 매핑 설계
  - timestamp, level, service, message, trace_id 등
- [ ] Consumer가 전송한 데이터 인덱싱 로직 구현
- [ ] 인덱싱 정상 동작 확인

##### 역할 3: 데이터 품질 검증 기초
- [ ] Great Expectations 환경 설정
- [ ] S3 로그 데이터 스키마 검증 Suite 작성
- [ ] 기본 검증 룰 정의 (필수 필드, 데이터 타입)

##### 역할 4: Milvus + RAG 기초 구축
- [ ] Milvus Standalone EKS 배포
- [ ] 컬렉션 스키마 설계 (벡터 차원, 메타데이터)
- [ ] 초기 지식 데이터 준비 (과거 장애 사례 샘플)
- [ ] OpenAI Embedding API 연동
- [ ] 샘플 데이터 벡터화 및 Milvus 적재 테스트

#### Day 3: RAG 실시간 분석 + Grafana 시각화
=> 위 요구 조건과 1일차 mvp 일정에 맞게 싹 수정
##### 역할 1: CI/CD 기초
- [ ] ECR 리포지토리 생성
- [ ] GitHub Actions 기본 파이프라인 (Docker 빌드 → ECR Push)

##### 역할 2: Grafana 대시보드
- [ ] Grafana 배포
- [ ] OpenSearch 데이터 소스 연결
- [ ] 실시간 에러 현황 대시보드 구축
  - 시간별 에러 발생 추이
  - 서비스별 로그 레벨 분포
  - 최근 에러 로그 목록

##### 역할 3: Airflow DAG 고도화
- [ ] S3 로그 → Milvus 업데이트 DAG 작성 (역할 4 협업)
- [ ] Great Expectations 검증을 DAG에 통합
- [ ] 스케줄링 설정 (일 1회 자동 실행)

##### 역할 4: 실시간 RAG 분석 완성
- [ ] ERROR/WARN 로그 수신 시 Milvus 유사도 검색
- [ ] 유사 사례 상위 K개 추출
- [ ] OpenAI API 호출 (프롬프트: 원인 분석 + 조치 가이드)
- [ ] Slack 메시지에 AI 분석 결과 포함
  - 기본 알림: 에러 내용
  - AI 분석: 유사 사례 + 추천 조치
- [ ] OpenSearch 인덱싱 연동 (역할 2 협업)

---

### **Day 4-5: 최종 완성 + 배포** 🎯

**목표**: 미완료 작업 처리, 안정화, 프로덕션 배포=> 일단 수정 보류

#### Day 4: 통합 테스트 및 안정화

##### 전체 협업
- [ ] **전체 파이프라인 E2E 테스트**
  1. 로그 생성 → Fluent Bit → Kinesis
  2. Consumer 폴링 → Pydantic 검증
  3. ERROR/WARN 필터링
  4. Milvus 유사도 검색 → OpenAI 분석
  5. Slack AI 분석 알림 도착
  6. S3 백업 및 OpenSearch 인덱싱
  7. Grafana 대시보드 업데이트
  8. Airflow DAG 실행 → Milvus 업데이트

- [ ] **성능 테스트**
  - 대량 로그 발생 시 처리 속도
  - Throttling 동작 확인
  - Kinesis 샤드 처리량 모니터링

- [ ] **에러 처리 강화**
  - DLQ 동작 확인 (검증 실패 로그)
  - 재시도 로직 추가
  - 장애 복구 시나리오 테스트

##### 역할별 개선 작업
- **역할 1**: 인프라 안정화 (Auto Scaling, 멀티 AZ)
- **역할 2**: 대시보드 고도화 (알림 규칙 추가)
- **역할 3**: 데이터 품질 리포트 자동화
- **역할 4**: RAG 프롬프트 튜닝 및 응답 품질 개선

#### Day 5: 프로덕션 배포 및 문서화

##### 배포 작업
- [ ] **Consumer Docker 이미지 최종 빌드**
  - 멀티 스테이지 빌드 최적화
  - 환경 변수 검증
  - ECR Push

- [ ] **EKS 배포**
  - Consumer Deployment/Service YAML 작성
  - ConfigMap/Secret 설정
  - 헬스 체크 및 로깅 설정
  - HPA (Horizontal Pod Autoscaler) 설정

- [ ] **CI/CD 파이프라인 완성**
  - GitHub Actions 전체 워크플로우 완성
  - 자동 테스트 → 빌드 → 배포 파이프라인
  - Slack 알림 연동 (배포 성공/실패)

##### 문서화
- [ ] **README 업데이트**
  - 프로젝트 개요
  - 아키텍처 다이어그램
  - Quick Start 가이드

- [ ] **운영 가이드 작성**
  - 인프라 설정 방법
  - Airflow DAG 추가 방법
  - 장애 대응 매뉴얼

- [ ] **API 문서**
  - Pydantic 스키마 문서
  - Slack 알림 포맷
  - OpenSearch 인덱스 구조

##### 최종 검증
- [ ] 프로덕션 환경에서 실제 로그 발생 시뮬레이션
- [ ] 모니터링 및 알림 정상 동작 확인
- [ ] 팀 내부 데모 및 피드백 수렴
- [ ] **Day 5 완료 기준**: 프로덕션 배포 완료 및 안정적 운영 가능

---

## 📊 일별 주요 마일스톤

| Day | 마일스톤 | 완료 기준 |
|:---:|:---|:---|
| **Day 1** | 기본 파이프라인 통합 완료 | 로그 → Kinesis → Consumer → Slack 흐름 정상 동작 |
| **Day 2** | RAG 기초 + OpenSearch 인덱싱 | Milvus 구축 완료, OpenSearch 인덱싱 시작 |
| **Day 3** | RAG 실시간 분석 + 대시보드 | AI 분석 Slack 알림 성공, Grafana 대시보드 완성 |
| **Day 4** | 전체 통합 테스트 + 안정화 | E2E 테스트 통과, 성능 검증 완료 |
| **Day 5** | 프로덕션 배포 완료 | EKS 배포, CI/CD 완성, 문서화 완료 |

---

## 🎯 역할별 상세 체크리스트

### 👤 역할 1: 인프라 담당 (Terraform, AWS)

#### Day 1: 기본 인프라
- [ ] VPC (Public 서브넷 2개, 멀티 AZ)
- [ ] Security Group 설정
- [ ] Kinesis Data Stream (샤드 1개, 24시간 보존)
- [ ] S3 버킷 (백업용, DLQ용)
- [ ] IAM Role/Policy (EKS Pod → Kinesis/S3)
- [ ] Secrets Manager (Slack, OpenAI Key)
- [ ] Terraform 상태 관리 (S3 Backend)

#### Day 2: OpenSearch 인프라
- [ ] OpenSearch 도메인 (t3.small 단일 노드)
- [ ] 인덱스 접근 권한 설정
- [ ] VPC 내 프라이빗 연결 설정

#### Day 3: CI/CD 기초
- [ ] ECR 리포지토리 생성
- [ ] GitHub Actions 기본 워크플로우

#### Day 4: 안정화
- [ ] Auto Scaling 설정
- [ ] CloudWatch 알람 설정
- [ ] 비용 최적화 검토

#### Day 5: 배포 지원
- [ ] EKS 클러스터 최종 점검
- [ ] CI/CD 파이프라인 완성
- [ ] 인프라 문서화

---

### 👤 역할 2: 실시간 파이프라인 담당 (Fluent Bit, OpenSearch, Grafana)

#### Day 1: Fluent Bit 기본 설정
- [ ] DaemonSet YAML
- [ ] Multiline 파서 (Stacktrace)
- [ ] Regex 헤더 추출 (timestamp, level, service)
- [ ] Kinesis Output 플러그인
- [ ] 로그 생성기 연동 테스트

#### Day 2: OpenSearch 인덱싱
- [ ] 인덱스 매핑 설계
- [ ] Consumer 연동 (역할 4 협업)
- [ ] 인덱싱 테스트

#### Day 3: Grafana 대시보드
- [ ] Grafana 배포
- [ ] OpenSearch 데이터 소스 연결
- [ ] 실시간 에러 현황 대시보드
- [ ] 서비스별 로그 통계 대시보드

#### Day 4: 대시보드 고도화
- [ ] 알림 규칙 추가 (임계값 기반)
- [ ] 커스텀 쿼리 최적화
- [ ] 대시보드 템플릿화

#### Day 5: 문서화
- [ ] Fluent Bit 설정 가이드
- [ ] Grafana 대시보드 사용법
- [ ] 인덱스 구조 문서

---

### 👤 역할 3: 배치 파이프라인 담당 (Airflow, 데이터 품질)

#### Day 1: Airflow 기본 환경
- [ ] Airflow LocalExecutor 배포
- [ ] Web UI 접근
- [ ] S3 연결 테스트
- [ ] 샘플 DAG 실행

#### Day 2: 데이터 품질 검증 기초
- [ ] Great Expectations 설정
- [ ] S3 스키마 검증 Suite
- [ ] 기본 검증 룰 정의

#### Day 3: Airflow DAG 고도화
- [ ] S3 → Milvus 업데이트 DAG (역할 4 협업)
- [ ] Great Expectations 통합
- [ ] 스케줄링 설정 (일 1회)

#### Day 4: 품질 리포트 자동화
- [ ] 검증 결과 리포트 생성
- [ ] Slack 알림 연동 (품질 이슈 발생 시)
- [ ] 통계 분석 DAG 추가

#### Day 5: 문서화
- [ ] Airflow DAG 작성 가이드
- [ ] 데이터 품질 기준 문서
- [ ] 운영 매뉴얼

---

### 👤 역할 4: Consumer + 전체 RAG 담당 (Kinesis, Slack, Milvus, LLM)

#### Day 1: Consumer 기본 기능
- [ ] boto3 Kinesis 폴링 루프
- [ ] Pydantic LogRecord 스키마
- [ ] ERROR/WARN 필터링
- [ ] Slack Webhook 연동
- [ ] Throttling 로직
- [ ] S3 백업

#### Day 2: Milvus + RAG 기초
- [ ] Milvus Standalone 배포
- [ ] 컬렉션 스키마 설계
- [ ] 초기 지식 데이터 준비
- [ ] OpenAI Embedding 연동
- [ ] 샘플 벡터화 및 적재

#### Day 3: 실시간 RAG 분석
- [ ] Milvus 유사도 검색 로직
- [ ] OpenAI API 호출 (원인 분석)
- [ ] Slack AI 분석 알림
- [ ] OpenSearch 인덱싱 연동 (역할 2 협업)

#### Day 4: 프롬프트 튜닝 및 안정화
- [ ] RAG 프롬프트 최적화
- [ ] 응답 품질 개선
- [ ] 에러 처리 강화
- [ ] 성능 테스트

#### Day 5: 배포 및 문서화
- [ ] Docker 이미지 최종 빌드
- [ ] EKS 배포
- [ ] Consumer 운영 가이드
- [ ] RAG 프롬프트 튜닝 가이드

---

## ✅ 통합 테스트 체크리스트

### Day 1 통합 테스트 (기본 파이프라인)
- [ ] 로그 생성기 → Fluent Bit 수집 확인
- [ ] Fluent Bit → Kinesis 전송 확인
- [ ] Kinesis → Consumer 폴링 확인
- [ ] Consumer → Slack 알림 도착
- [ ] S3 백업 확인
- [ ] DLQ 동작 확인 (잘못된 포맷 로그)

### Day 3 통합 테스트 (RAG 분석)
- [ ] ERROR 로그 발생 → Milvus 검색
- [ ] 유사 사례 추출 확인
- [ ] OpenAI 분석 결과 생성
- [ ] Slack에 AI 분석 포함 알림 도착
- [ ] OpenSearch 인덱싱 확인
- [ ] Grafana 대시보드 업데이트

### Day 4 통합 테스트 (E2E)
- [ ] 대량 로그 발생 시나리오
- [ ] Throttling 동작 확인
- [ ] Airflow DAG 실행 → Milvus 업데이트
- [ ] 데이터 품질 검증 통과
- [ ] 모든 컴포넌트 정상 동작

---

## 🚩 주요 리스크 및 대응 방안

### 리스크 1: Day 1 통합 실패
**원인**: 데이터 포맷 불일치, 권한 문제
**대응**: 오전 중 API 스펙 사전 합의, 통합 전 로컬 테스트

### 리스크 2: RAG 성능 이슈
**원인**: Milvus 검색 속도, OpenAI API 응답 지연
**대응**: 캐싱 전략, 비동기 처리, Fallback 로직

### 리스크 3: 배포 일정 지연
**원인**: 미완료 기능, 버그
**대응**: Day 4부터 우선순위 조정, MVP 기능 우선 배포

---

## 📈 성공 기준

### 기술적 성공 기준
- [ ] 로그 처리 Latency < 5초
- [ ] Slack 알림 도달률 > 99%
- [ ] RAG 분석 정확도 주관 평가 > 80%
- [ ] 시스템 가용성 > 99%

### 비즈니스 성공 기준
- [ ] 실제 장애 상황에서 AI 분석이 MTTR 단축에 기여
- [ ] 팀 내부 사용자 만족도 높음
- [ ] 확장 가능한 아키텍처 구현

---

## 🎓 학습 및 개선 포인트

### 각 역할별 핵심 학습 내용
- **역할 1**: Terraform IaC, AWS 리소스 설계
- **역할 2**: Fluent Bit 파서, OpenSearch DSL, Grafana 대시보드
- **역할 3**: Airflow DAG 작성, Great Expectations
- **역할 4**: RAG 아키텍처, LLM 프롬프트 엔지니어링, 벡터 DB

### 프로젝트 종료 후 개선 과제
- [ ] 멀티 샤드 처리 (Kinesis Consumer 확장)
- [ ] LLM 모델 파인튜닝 (도메인 특화)
- [ ] 자동화된 A/B 테스트 (프롬프트 비교)
- [ ] 비용 최적화 (Spot Instance 활용)

---

> [!NOTE]
> 이 WBS는 **5일 집중 개발** 기준이며, 실제 진행 상황에 따라 유동적으로 조정 가능합니다.
> 각 Day 종료 시점에 **Daily Standup**을 진행하여 진행 상황을 공유하고, 블로커를 해결합니다.
