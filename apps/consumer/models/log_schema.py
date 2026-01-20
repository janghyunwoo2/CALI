"""
=====================================================
Pydantic 로그 스키마 정의
=====================================================
설명: Fluent Bit에서 전송된 로그의 2차 검증 스키마
역할: 데이터 무결성 보장 및 타입 안정성 확보
=====================================================
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class LogRecord(BaseModel):
    """로그 레코드 스키마"""
    
    timestamp: datetime = Field(..., description="로그 발생 시간")
    level: str = Field(..., description="로그 레벨 (ERROR, WARN, INFO 등)")
    service: str = Field(..., description="서비스 이름 (예: payment-api)")
    message: str = Field(..., description="로그 메시지")
    
    # Kubernetes 메타데이터
    namespace: Optional[str] = Field(None, description="K8s 네임스페이스")
    pod_name: Optional[str] = Field(None, description="K8s Pod 이름")
    container_name: Optional[str] = Field(None, description="컨테이너 이름")
    
    # 추가 필드
    error_code: Optional[str] = Field(None, description="에러 코드")
    trace_id: Optional[str] = Field(None, description="분산 추적 ID")
    
    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """로그 레벨 검증"""
        allowed_levels = ["DEBUG", "INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"Invalid log level: {v}. Allowed: {allowed_levels}")
        return v_upper
    
    class Config:
        """Pydantic 설정"""
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-19T14:00:01",
                "level": "ERROR",
                "service": "payment-api",
                "message": "DB Connection timeout",
                "namespace": "production",
                "pod_name": "payment-api-7d8f9c-abc123",
                "container_name": "payment-api",
                "error_code": "DB_504",
                "trace_id": "xyz-789"
            }
        }
