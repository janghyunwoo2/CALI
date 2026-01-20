"""
=====================================================
구조화된 로깅 유틸리티
=====================================================
설명: JSON 포맷 로깅 설정
역할: 일관된 로그 형식 제공
=====================================================
"""

import logging
import sys
from typing import Optional


def setup_logger(name: str, level: Optional[int] = logging.INFO) -> logging.Logger:
    """
    구조화된 로거 설정
    
    Args:
        name: 로거 이름 (보통 __name__)
        level: 로그 레벨
    
    Returns:
        설정된 Logger 인스턴스
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 핸들러가 이미 있으면 추가하지 않음 (중복 방지)
    if logger.handlers:
        return logger
    
    # 콘솔 핸들러
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # 포맷터 (구조화된 로그)
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger
