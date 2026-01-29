import json
import boto3
from datetime import datetime
from typing import Any, Dict
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class S3DLQ:
    """S3 Dead Letter Queue handler"""
    
    def __init__(self):
        self.s3 = boto3.client("s3", region_name=settings.AWS_REGION)
        self.bucket = settings.S3_DLQ_BUCKET
        
    def save_failed_record(self, raw_data: Dict[str, Any], error_reason: str):
        """처리 실패한 레코드를 S3에 저장"""
        try:
            timestamp = datetime.now().strftime("%Y/%m/%d/%H")
            file_name = f"dlq/{timestamp}/{datetime.now().timestamp()}_error.json"
            
            payload = {
                "failed_at": datetime.now().isoformat(),
                "error_reason": str(error_reason),
                "raw_data": raw_data
            }
            
            self.s3.put_object(
                Bucket=self.bucket,
                Key=file_name,
                Body=json.dumps(payload, ensure_ascii=False),
                ContentType="application/json"
            )
            logger.info(f"DLQ 저장 완료: s3://{self.bucket}/{file_name}")
            
        except Exception as e:
            # DLQ 저장 실패는 치명적이므로 에러 로그 남김 (재시도 로직은 복잡도상 제외)
            logger.error(f"DLQ 저장 실패! 데이터 유실 위험: {e}")
