"""
=====================================================
Kinesis Stream Consumer
=====================================================
설명: Kinesis Data Stream에서 로그를 실시간으로 구독
역할: 데이터 수신 → Pydantic 검증 → RAG 분석 → Slack 알림
=====================================================
"""

import json
import time
from typing import Any, Dict, List

import boto3
from config.settings import settings
from models.log_schema import LogRecord
from pydantic import ValidationError
from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from services.s3_dlq import S3DLQ
from services.slack_notifier import SlackNotifier
from services.throttle import Throttle
from utils.logger import setup_logger
from utils.text_preprocessor import clean_log_for_embedding

logger = setup_logger(__name__)


class KinesisConsumer:
    """Kinesis Stream Consumer 클래스"""

    def __init__(self):
        """초기화 및 클라이언트 설정"""
        self.kinesis_client = boto3.client("kinesis", region_name=settings.AWS_REGION)
        self.stream_name = settings.KINESIS_STREAM_NAME
        
        # 외부 서비스 클라이언트 초기화
        self.milvus_client = MilvusClient()
        self.ai_client = OpenAIClient()
        self.slack_notifier = SlackNotifier()
        self.dlq = S3DLQ()
        self.throttle = Throttle()
        
        # 샤드 관리를 위한 상태
        self.shard_iterator = None

    def start(self):
        """Consumer 메인 루프 시작"""
        logger.info(f"🚀 Kinesis Consumer 시작: {self.stream_name}")
        
        try:
            # 1. 샤드 목록 가져오기 (단일 샤드 가정, multi-shard시 로직 확장 필요)
            response = self.kinesis_client.describe_stream(StreamName=self.stream_name)
            shard_id = response['StreamDescription']['Shards'][0]['ShardId']
            
            # 2. 샤드 이터레이터 생성 (LATEST: 실행 시점 이후 데이터만)
            self.shard_iterator = self.kinesis_client.get_shard_iterator(
                StreamName=self.stream_name,
                ShardId=shard_id,
                ShardIteratorType='LATEST'
            )['ShardIterator']
            
            # 3. 폴링 루프
            while True:
                response = self.kinesis_client.get_records(
                    ShardIterator=self.shard_iterator,
                    Limit=10  # 배치 사이즈
                )
                
                records = response.get('Records', [])
                if records:
                    logger.info(f"📥 {len(records)}개 레코드 수신")
                    self.process_records(records)
                
                # 다음 이터레이터 갱신
                self.shard_iterator = response.get('NextShardIterator')
                if not self.shard_iterator:
                    logger.warning("ShardIterator 만료됨. 재연결 필요.")
                    break
                
                # AWS API 스로틀링 방지
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Consumer 실행 중 치명적 오류: {e}")
            raise e

    def process_records(self, records: List[Dict[str, Any]]):
        """레코드 배치 처리"""
        for record in records:
            try:
                # 1. Kinesis 데이터 디코딩 및 전처리
                raw_str = record["Data"].decode("utf-8")
                
                # [DATA received from shardId...] 접두어 제거
                if "[DATA received from" in raw_str:
                    try:
                        # 접두어 뒤의 실제 JSON 부분만 추출
                        # 예: "[DATA...] {"level":...}" -> "{"level":...}"
                        raw_str = raw_str.split("]: ", 1)[1]
                    except IndexError:
                        logger.warning(f"메타데이터 제거 실패, 원본 사용: {raw_str[:50]}...")

                raw_data = json.loads(raw_str)

                # 2. Pydantic 검증
                log_record = LogRecord(**raw_data)

                # 3. 레벨 필터링 (ERROR/WARN만 처리)
                if log_record.level not in ["ERROR", "WARN"]:
                    # INFO 로그는 디버그 모드에서만 출력
                    # logger.debug(f"ℹ️ INFO 스킵: {log_record.service}")
                    continue

                logger.info(f"🚨 에러 감지: {log_record.service} - {log_record.message}")
                
                # 4. RAG 분석 파이프라인 실행
                self._run_rag_pipeline(log_record)

            except ValidationError as e:
                logger.error(f"데이터 검증 실패: {e}")
                # DLQ 저장
                self.dlq.save_failed_record(raw_data, str(e))
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                self.dlq.save_failed_record({"raw_bytes": str(record["Data"])}, str(e))

            except Exception as e:
                logger.error(f"레코드 처리 중 알 수 없는 오류: {e}")

    def _run_rag_pipeline(self, log_record: LogRecord):
        """RAG 분석 및 알림 파이프라인"""
        try:
            # 0. 스로틀링 체크 (과도한 알림 방지)
            if not self.throttle.should_send_alert(log_record.service, log_record.message):
                return

            # 1. 임베딩 생성 (검색용 쿼리)
            # [RAG 최적화] 텍스트 전처리 적용 (노이즈 제거)
            clean_query = clean_log_for_embedding(
                log_record.service, 
                log_record.message, 
                log_record.log_content
            )
            embedding = self.ai_client.create_embedding(clean_query)
            
            # 2. 유사 사례 검색 (Milvus)
            similar_cases = self.milvus_client.search_similar_logs(embedding)
            
            # [RAG 최적화] 유사도가 매우 높은(거리 가까운) 사례가 있으면 AI 호출 생략
            # L2 Distance metric: 0에 가까울수록 유사함 (임계값: 0.35 설정)
            best_match = None
            if similar_cases:
                top_case = similar_cases[0]
                if top_case.get('score') < 0.35:
                    best_match = top_case
                    logger.info(f"⚡ [Cache Hit] 유사 사례 발견 (Distance: {top_case['score']:.4f}). AI 분석 생략.")

            if best_match:
                # 캐시된 답변 사용
                analysis_result = {
                    "cause": f"[과거 사례 기반 자동 분석] {best_match['cause']}",
                    "action": best_match['action'] 
                }
            else:
                # 3. AI 원인 분석 (OpenAI)
                if similar_cases:
                    logger.info(f"🔍 유사 사례 {len(similar_cases)}건 발견 (Distance: {similar_cases[0]['score']:.4f}). AI 정밀 분석 수행.")
                analysis_result = self.ai_client.analyze_log(log_record.model_dump(), similar_cases)
            
            # 4. Slack 알림 전송
            self.slack_notifier.send_alert(log_record.model_dump(), analysis_result)
            
            # [삭제됨] 자가 학습 (Auto-Learning) 로직 제거됨 (User Request)
            
        except Exception as e:
            logger.error(f"RAG 파이프라인 처리 실패: {e}")
