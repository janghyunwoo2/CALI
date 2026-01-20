"""
=====================================================
애플리케이션 설정 관리
=====================================================
설명: Pydantic Settings를 사용한 환경 변수 관리
용도: AWS, OpenAI, Slack 등 외부 서비스 설정
=====================================================
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # AWS 설정
    AWS_REGION: str = "ap-northeast-2"
    KINESIS_STREAM_NAME: str
    S3_DLQ_BUCKET: str
    
    # OpenAI 설정
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    
    # Milvus 설정
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    
    # Slack 설정
    SLACK_WEBHOOK_URL: str
    
    # Throttling 설정
    THROTTLE_WINDOW_SECONDS: int = 60
    THROTTLE_MAX_ALERTS: int = 5


# 싱글톤 인스턴스
settings = Settings()
