
from services.s3_dlq import S3DLQ
from utils.logger import setup_logger
import logging
import sys

# 로깅 설정
logger = setup_logger(__name__)
logging.getLogger().setLevel(logging.INFO)
h = logging.StreamHandler(sys.stdout)
h.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(h)

def test_s3_dlq():
    print("=== S3 DLQ Connection Test ===")
    
    dlq = S3DLQ()
    print(f"Target Bucket: {dlq.bucket_name}")
    
    # Test 1: Save Parsing Error
    try:
        print("\n1. Testing 'save_failed_record' (Parsing Error)...")
        dlq.save_failed_record(
            {"raw_data": "invalid_json_bytes"}, 
            "Test Error: JSONDecodeError"
        )
        print("   -> Call finished (Check logs for success/failure)")
    except Exception as e:
        print(f"   -> Exception: {e}")

    # Test 2: Save RAG Miss
    try:
        print("\n2. Testing 'save_rag_miss_log' (RAG Miss)...")
        dlq.save_rag_miss_log(
            {"service": "test-service", "message": "test error"}, 
            {"cause": "Unknown", "action": "None"}
        )
        print("   -> Call finished (Check logs for success/failure)")
    except Exception as e:
        print(f"   -> Exception: {e}")

if __name__ == "__main__":
    test_s3_dlq()
