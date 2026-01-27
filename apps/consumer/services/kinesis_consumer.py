"""
=====================================================
Kinesis Stream Consumer # TEST
=====================================================
설명: Kinesis Data Stream에서 로그를 실시간으로 구독
역할: 데이터 수신 → Pydantic 검증 → 후속 처리 트리거
=====================================================
"""

import json
from typing import Any, Dict, List

import boto3
from config.settings import settings
from models.log_schema import LogRecord
from pydantic import ValidationError
from utils.logger import setup_logger

logger = setup_logger(__name__)


class KinesisConsumer:
    """Kinesis Stream Consumer 클래스"""

    def __init__(self):
        """초기화"""
        self.kinesis_client = boto3.client("kinesis", region_name=settings.AWS_REGION)
        self.stream_name = settings.KINESIS_STREAM_NAME

        # TODO: S3 DLQ 클라이언트 초기화
        # TODO: Milvus, OpenAI, Slack 클라이언트 초기화

    def start(self):
        """Consumer 시작"""
        logger.info(f"Kinesis Consumer 시작: {self.stream_name}")
        # TODO: 샤드 이터레이터 생성 및 레코드 폴링 루프 구현

    def process_records(self, records: List[Dict[str, Any]]):
        """레코드 처리 (ERROR/WARN만)"""
        for record in records:
            try:
                # Kinesis 데이터 디코딩
                data = json.loads(record["Data"].decode("utf-8"))

                # Pydantic 검증
                log_record = LogRecord(**data)

                # ERROR/WARN만 처리 (INFO는 무시)
                if log_record.level not in ["ERROR", "WARN"]:
                    logger.debug(f"INFO 로그 스킵: {log_record.service}")
                    continue

                # ERROR/WARN 로그만 분석 및 알림
                logger.info(
                    f"에러 로그 처리: {log_record.service} - {log_record.level}"
                )
                # TODO: RAG 분석 및 Slack 알림

            except ValidationError as e:
                # 검증 실패 시 DLQ로 전송
                logger.error(f"Pydantic 검증 실패: {e}")
                # TODO: S3 DLQ에 저장

            except Exception as e:
                logger.error(f"레코드 처리 오류: {e}")
