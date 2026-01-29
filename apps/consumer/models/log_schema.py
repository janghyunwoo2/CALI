from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

class LogRecord(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    level: str = Field(..., description="ERROR, WARN 등")
    service: str = Field(..., description="서비스명")
    message: str = Field(..., description="짧은 요약")
    # 핵심: 비정형 로그 전문을 담는 필드 (LLM 분석용)
    log_content: Optional[str] = Field(None, description="상세 스택트레이스 전문")
    
    # 메타데이터 (프로덕션 로그 포맷 반영)
    version: Optional[str] = None
    trace_id: Optional[str] = None
    platform: Optional[str] = None
    environment: Optional[str] = None
    pod_name: Optional[str] = None
    error_code: Optional[str] = None

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed: return "INFO"
        return v_upper