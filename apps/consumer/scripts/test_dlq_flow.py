
from services.kinesis_consumer import KinesisConsumer
from utils.logger import setup_logger
import json
import logging
import sys

logger = setup_logger(__name__)
logging.getLogger().setLevel(logging.INFO)
h = logging.StreamHandler(sys.stdout)
logging.getLogger().addHandler(h)

def test_failure_flow():
    print("=== Consumer Failure Flow Test ===")
    
    consumer = KinesisConsumer()
    
    # Invalid Data (Missing 'service' field) to trigger ValidationError
    invalid_record = {
        "Data": json.dumps({
            "level": "ERROR",
            "message": "This should fail validation",
            "timestamp": "2024-01-01T00:00:00"
            # Missing service, trace_id, etc.
        }).encode('utf-8')
    }
    
    print("\n[Test] Sending Invalid Record...")
    try:
        # process_records expects a list of dicts with 'Data' key
        consumer.process_records([invalid_record])
        print("✅ Process method executed (Check logs for '데이터 검증 실패')")
    except Exception as e:
        print(f"❌ Unexpected crash: {e}")

if __name__ == "__main__":
    test_failure_flow()
