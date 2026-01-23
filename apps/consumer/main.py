import time
from models.log_schema import LogRecord
from services.openai_client import OpenAIClient
from services.slack_notifier import SlackNotifier
from utils.logger import setup_logger

logger = setup_logger(__name__)

# [수정 포인트 1] Day 1 MVP용 로컬 더미 데이터 리스트 정의
DUMMY_LOGS = [
    {
        "level": "ERROR",
        "service": "payment-api",
        "message": "Connection pool exhausted",
        "log_content": "java.sql.SQLException: Cannot get connection from HikariPool... active: 20, max: 20",
        "error_code": "DB_504",
        "pod_name": "payment-api-7d8f9c-abc123"
    },
    {
        "level": "INFO",
        "service": "order-service",
        "message": "Order processed successfully",
        "log_content": "Order ID: ORD-9982, User: user_77"
    }
]

def main():
    """메인 실행 함수: 로컬 MVP 버전"""
    logger.info("CALI Consumer MVP 시작 (Local Test Mode)")
    
    # [수정 포인트 2] 필요한 서비스들 초기화
    ai_client = OpenAIClient()
    slack_notifier = SlackNotifier()

    # [수정 포인트 3] 데이터 루프 (Kinesis 대신 리스트 순회)
    for raw_log in DUMMY_LOGS:
        try:
            # 1. Pydantic 검증: 데이터 무결성 체크
            log_record = LogRecord(**raw_log)
            
            # 2. 필터링: ERROR 레벨만 AI 분석 진행
            if log_record.level == "ERROR":
                logger.info(f"🚨 에러 감지 [{log_record.service}]: AI 분석을 시작합니다.")
                
                # 3. AI 분석 호출: OpenAI GPT-4o
                analysis_result = ai_client.analyze_log(log_record.model_dump())
                
                # 4. 슬랙 전송: 분석 결과와 로그 메타데이터 전달
                slack_notifier.send_alert(log_record.model_dump(), analysis_result)
                
            else:
                logger.info(f"✅ 일반 로그 스킵 ({log_record.service})")
                
        except Exception as e:
            logger.error(f"로그 처리 중 에러 발생: {e}")

if __name__ == "__main__":
    main()