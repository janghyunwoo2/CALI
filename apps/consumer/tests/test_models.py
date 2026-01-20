"""
=====================================================
Pydantic 모델 테스트
=====================================================
설명: LogRecord 스키마 검증 테스트
=====================================================
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from models.log_schema import LogRecord


def test_valid_log_record():
    """정상적인 로그 레코드 테스트"""
    data = {
        "timestamp": "2026-01-19T14:00:01",
        "level": "ERROR",
        "service": "payment-api",
        "message": "DB Connection timeout",
        "namespace": "production",
        "pod_name": "payment-api-abc123",
        "error_code": "DB_504"
    }
    
    log_record = LogRecord(**data)
    assert log_record.level == "ERROR"
    assert log_record.service == "payment-api"


def test_invalid_log_level():
    """잘못된 로그 레벨 테스트"""
    data = {
        "timestamp": "2026-01-19T14:00:01",
        "level": "INVALID",  # 허용되지 않는 레벨
        "service": "test-service",
        "message": "Test message"
    }
    
    with pytest.raises(ValidationError):
        LogRecord(**data)


# TODO: 추가 테스트 케이스 작성
