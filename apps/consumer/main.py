"""
=====================================================
Consumer 메인 엔트리포인트
=====================================================
설명: Kinesis Stream 구독 및 로그 처리 메인 루프
역할: 데이터 수신 → 검증 → 분석 → 알림
=====================================================
"""

from config.settings import settings
from services.kinesis_consumer import KinesisConsumer
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """메인 실행 함수"""
    logger.info("CALI Consumer 시작")
    logger.info(f"Kinesis Stream: {settings.KINESIS_STREAM_NAME}")
    
    # TODO: Kinesis Consumer 초기화 및 실행
    # consumer = KinesisConsumer()
    # consumer.start()


if __name__ == "__main__":
    main()
