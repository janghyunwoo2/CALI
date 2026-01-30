
import json
import boto3
from datetime import datetime
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class S3DLQ:
    """S3 Dead Letter Queue handler"""
    
    def __init__(self):
        self.s3_client = boto3.client("s3")
        self.bucket_name = settings.S3_DLQ_BUCKET if settings.S3_DLQ_BUCKET and settings.S3_DLQ_BUCKET != "pending" else "cali-dlq-bucket"
        logger.info(f"S3 DLQ initialized. Target Bucket: {self.bucket_name}")

    def save_failed_record(self, record: dict, error_reason: str):
        """데이터 검증/파싱 실패 레코드 저장"""
        try:
            timestamp = datetime.now().strftime("%Y/%m/%d/%H")
            # 사용자가 생성한 error_dlq 폴더 활용
            file_name = f"error_dlq/parsing_error/{timestamp}/{datetime.now().timestamp()}.json"
            
            payload = {
                "error": error_reason,
                "record": record,
                "timestamp": datetime.now().isoformat()
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(payload, ensure_ascii=False)
            )
            logger.info(f"DLQ 저장 완료: {file_name}")
            
        except Exception as e:
            logger.error(f"DLQ 저장 실패: {e}")



    def save_rag_miss_log(self, log_record: dict, analysis_result: dict):
        """
        RAG 검색 실패(Cache Miss) 로그 저장
        - 추후 Fine-tuning 및 지식 베이스 보강 학습 데이터로 활용
        """
        try:
            # 사용자가 생성한 error_dlq 폴더 하위에 저장
            target_path_prefix = "error_dlq/rag_miss/" 
            
            service = log_record.get('service', 'unknown')
            timestamp = datetime.now().strftime("%Y/%m/%d")
            file_name = f"{target_path_prefix}{timestamp}/{service}_{datetime.now().timestamp()}.json"
            
            payload = {
                "type": "RAG_MISS",
                "service": service,
                "log_data": log_record,
                "ai_analysis": analysis_result,
                "saved_at": datetime.now().isoformat()
            }
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=json.dumps(payload, ensure_ascii=False, default=str)
            )
            logger.info(f"RAG Miss 로그 S3 저장 완료: {file_name}")
            
        except Exception as e:
            logger.error(f"RAG Miss 로그 저장 실패 (Bucket: {self.bucket_name}, Key: {file_name}): {e}")
            # 개발 단계 디버깅을 위해 Traceback 출력
            import traceback
            logger.error(traceback.format_exc())
