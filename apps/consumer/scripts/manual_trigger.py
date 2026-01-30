from services.kinesis_consumer import KinesisConsumer
from models.log_schema import LogRecord
from utils.logger import setup_logger
import json
import datetime

import logging
import sys

# 로깅 설정: 콘솔 출력 활성화
logger = setup_logger(__name__)
logging.getLogger().setLevel(logging.INFO)
# 기존 핸들러 제거 후 stdout 핸들러 추가 (중복 방지)
for handler in logging.getLogger().handlers[:]:
    logging.getLogger().removeHandler(handler)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(handler)

def test_consumer_manual_trigger():
    print("=== Consumer Manual Trigger Test (Mocking Kinesis) ===")
    
    # 1. KinesisConsumer 인스턴스 생성
    # (실제 AWS/Milvus/OpenAI/Slack 연결 테스트 포함)
    consumer = KinesisConsumer()
    
    # 2. 테스트용 더미 로그 데이터 (Kinesis에서 왔다고 가정)
    # Auth Failure 케이스 (Cache Hit 유도 또는 RAG 분석 테스트)
    mock_log = {
        "service": "auth-service",
        "level": "ERROR",
        "message": "High rate of JWT validation failures",
        "timestamp": datetime.datetime.now().isoformat(),
        "log_content": "Security Alert - [INC-MANUAL-TEST] High rate of JWT validation failures from IP 10.0.0.99. Suspected Brute Force.",
        "trace_id": "test-trace-999",
        "platform": "eks",
        "environment": "dev"
    }

    # 3. process_records 메서드가 받을 수 있는 형태로 포장
    # Kinesis는 보통 [{'Data': bytes}] 형태의 레코드를 줌
    # 하지만 KinesisConsumer.process_records는 boto3 응답을 처리하므로, 
    # 내부 로직인 `_run_rag_pipeline`을 직접 호출하거나, 
    # process_records를 호출하려면 boto3 리턴 포맷을 맞춰야 함.
    # 여기서는 가장 핵심인 _run_rag_pipeline을 직접 호출하여 테스트.
    
    try:
        print("🚀 Sending Mock Log to RAG Pipeline...")
        
        # Pydantic 모델로 변환
        log_record = LogRecord(**mock_log)
        
        # 파이프라인 수동 실행
        # _run_rag_pipeline은 private이지만 테스트 목적 호출 가능
        consumer._run_rag_pipeline(log_record)
        
        print("✅ Pipeline execution finished. Check Slack for notification!")
        
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    test_consumer_manual_trigger()
