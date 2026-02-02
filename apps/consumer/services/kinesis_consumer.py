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
from services.openai_client import AIClient
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
        self.ai_client = AIClient()
        self.slack_notifier = SlackNotifier()
        self.dlq = S3DLQ()
        self.throttle = Throttle()
        
        # 샤드 관리를 위한 상태
        self.shard_iterator = None

    def start(self):
        """Consumer 메인 루프 시작"""
        logger.info(f"🚀 Kinesis Consumer 시작: {self.stream_name}")
        
        try:
            # 1. 샤드 목록 가져오기 (단일 샤드 가정)
            response = self.kinesis_client.describe_stream(StreamName=self.stream_name)
            shard_id = response['StreamDescription']['Shards'][0]['ShardId']
            
            # 2. 샤드 이터레이터 생성 (LATEST)
            self.shard_iterator = self.kinesis_client.get_shard_iterator(
                StreamName=self.stream_name,
                ShardId=shard_id,
                ShardIteratorType='LATEST'
            )['ShardIterator']
            
            # 3. 폴링 루프
            while True:
                # [Aggregation] 요약 알림 전송 (매 루프마다 체크)
                summaries = self.throttle.get_summaries_to_send()
                for s in summaries:
                    self.slack_notifier.send_summary_alert(
                        s['service'], s['message'], s['count'], s['duration']
                    )

                response = self.kinesis_client.get_records(
                    ShardIterator=self.shard_iterator,
                    Limit=10
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
                # 1. Kinesis 데이터 디코딩
                raw_str = record["Data"].decode("utf-8")
                
                if "[DATA received from" in raw_str:
                    try:
                        raw_str = raw_str.split("]: ", 1)[1]
                    except IndexError:
                        logger.warning(f"메타데이터 제거 실패, 원본 사용: {raw_str[:50]}...")

                raw_data = json.loads(raw_str)
                log_record = LogRecord(**raw_data)

                if log_record.level not in ["ERROR", "WARN"]:
                    continue

                logger.info(f"🚨 에러 감지: {log_record.service} - {log_record.message}")
                
                # 4. RAG 분석 파이프라인 실행
                self._run_rag_pipeline(log_record)

            except ValidationError as e:
                logger.error(f"데이터 검증 실패: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 실패: {e}")
            except Exception as e:
                logger.error(f"레코드 처리 중 알 수 없는 오류: {e}")

    def _run_rag_pipeline(self, log_record: LogRecord):
        """RAG 분석 및 알림 파이프라인"""
        try:
            # 0. 스로틀링 체크 (First Alert 여부 판단)
            if not self.throttle.record_occurrence(log_record.service, log_record.message):
                return

            # 1. 임베딩 생성
            clean_query = clean_log_for_embedding(
                log_record.service, 
                log_record.message, 
                log_record.log_content
            )
            embedding = self.ai_client.create_embedding(clean_query)
            
            # 2. 유사 사례 검색
            similar_cases = self.milvus_client.search_similar_logs(embedding)
            
            # Cache Hit 로직
            best_match = None
            if similar_cases:
                top_case = similar_cases[0]
                if top_case.get('score') < 0.35:
                    best_match = top_case
                    logger.info(f"⚡ [Cache Hit] 유사 사례 발견 (Distance: {top_case['score']:.4f})")

            rag_info = {}
            if best_match:
                analysis_result = {
                    "cause": f"[과거 사례 기반 자동 분석] {best_match['cause']}",
                    "action": best_match['action'] 
                }
                rag_info = {
                    "source": "Cache Hit",
                    "distance": best_match['score'],
                    "similar_count": len(similar_cases)
                }
            else:
                if similar_cases:
                    logger.info(f"🔍 유사 사례 {len(similar_cases)}건 발견. AI 정밀 분석 수행.")
                
                start_time = time.time()
                analysis_result = self.ai_client.analyze_log(log_record.model_dump(), similar_cases)
                latency = time.time() - start_time
                
                rag_info = {
                    "source": "OpenAI",
                    "distance": similar_cases[0]['score'] if similar_cases else None,
                    "similar_count": len(similar_cases),
                    "latency": f"{latency:.2f}s"
                }

                self.dlq.save_rag_miss_log(log_record.model_dump(), analysis_result)
            
            # 3. 발생 횟수 (이 시점엔 무조건 1회차 First Alert임)
            rag_info["occurrence_count"] = 1
            
            # 4. Slack 알림 전송
            self.slack_notifier.send_alert(log_record.model_dump(), analysis_result, rag_info)
            
        except Exception as e:
            logger.error(f"RAG 파이프라인 처리 실패: {e}")
