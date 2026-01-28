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
from utils.logger import setup_logger

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
                # 1. Kinesis 데이터 디코딩
                raw_data = json.loads(record["Data"].decode("utf-8"))

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
            # 1. 임베딩 생성 (검색용 쿼리)
            # 로그 메시지와 상세 내용을 조합하여 쿼리 구성
            query_text = f"{log_record.message} {log_record.log_content or ''}"[:8000]
            embedding = self.ai_client.create_embedding(query_text)
            
            # 2. 유사 사례 검색 (Milvus)
            similar_cases = self.milvus_client.search_similar_logs(embedding)
            if similar_cases:
                logger.info(f"🔍 유사 사례 {len(similar_cases)}건 발견")
            
            # 3. AI 원인 분석 (OpenAI)
            analysis_result = self.ai_client.analyze_log(log_record.model_dump(), similar_cases)
            
            # 4. Slack 알림 전송
            self.slack_notifier.send_alert(log_record.model_dump(), analysis_result)
            
            # 5. 자가 학습 (Auto-Learning)
            # 분석 완료된 데이터를 다시 Milvus에 저장하여 지식 축적
            knowledge_data = log_record.model_dump()
            knowledge_data.update(analysis_result) # cause, action 추가
            self.milvus_client.insert_log_case(knowledge_data, embedding)
            
        except Exception as e:
            logger.error(f"RAG 파이프라인 처리 실패: {e}")
