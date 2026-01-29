import time
from services.kinesis_consumer import KinesisConsumer
from utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    """CALI Consumer 메인 엔트리포인트 (Production Loop)"""
    logger.info("🚀 CALI Consumer 애플리케이션 시작")
    
    try:
        # Kinesis Client 초기화 및 루프 시작
        # 내부적으로 Milvus, OpenAI, Slack, DLQ 모두 연동됨
        consumer = KinesisConsumer()
        consumer.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 사용자 요청에 의한 중단")
    except Exception as e:
        logger.critical(f"💀 Consumer 프로세스 비정상 종료: {e}")
        raise e

if __name__ == "__main__":
    main()