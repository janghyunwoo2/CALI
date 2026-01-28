import time
from models.log_schema import LogRecord
from services.openai_client import OpenAIClient
from services.milvus_client import MilvusClient
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
    milvus_client = MilvusClient()
    slack_notifier = SlackNotifier()

    # [수정 포인트 3] 데이터 루프 (Kinesis 대신 리스트 순회)
    for raw_log in DUMMY_LOGS:
        try:
            # 1. Pydantic 검증: 데이터 무결성 체크
            log_record = LogRecord(**raw_log)
            
            # 2. 필터링: ERROR 레벨만 AI 분석 진행
            if log_record.level == "ERROR":
                logger.info(f"🚨 에러 감지 [{log_record.service}]: AI 분석을 시작합니다.")
                
                # 3. RAG: 유사 장애 사례 검색
                query_text = f"{log_record.message} {log_record.log_content}"[:8000]
                embedding = ai_client.create_embedding(query_text)
                similar_cases = milvus_client.search_similar_logs(embedding)
                
                # 4. AI 분석 호출: OpenAI GPT-4o (with RAG context)
                analysis_result = ai_client.analyze_log(log_record.model_dump(), similar_cases)
                
                # 5. 슬랙 전송
                slack_notifier.send_alert(log_record.model_dump(), analysis_result)
                
                # 6. 자가 학습 (Auto-Learning): 분석된 결과를 다시 벡터 DB에 저장
                #    다음 유사 장애 발생 시 이 지식을 활용하기 위함
                try:
                    # 분석 결과가 포함된 완성된 지식 데이터 구성
                    knowledge_data = log_record.model_dump()
                    knowledge_data.update(analysis_result) # cause, action 추가
                    
                    milvus_client.insert_log_case(knowledge_data, embedding)
                except Exception as e:
                    logger.error(f"자가 학습 데이터 저장 실패: {e}")
                
            else:
                logger.info(f"✅ 일반 로그 스킵 ({log_record.service})")
                
        except Exception as e:
            logger.error(f"로그 처리 중 에러 발생: {e}")

if __name__ == "__main__":
    main()