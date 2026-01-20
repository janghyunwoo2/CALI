"""
=====================================================
윈도우 기반 Throttling 유틸리티
=====================================================
설명: 동일 에러 폭주 시 알림 빈도 제어
역할: 시간 윈도우 내 최대 알림 횟수 제한
=====================================================
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict


class Throttler:
    """Throttling 관리 클래스"""
    
    def __init__(self, window_seconds: int = 60, max_alerts: int = 5):
        """
        초기화
        
        Args:
            window_seconds: 윈도우 시간 (초)
            max_alerts: 윈도우 내 최대 알림 횟수
        """
        self.window_seconds = window_seconds
        self.max_alerts = max_alerts
        
        # {alert_key: [timestamp1, timestamp2, ...]}
        self.alert_history: Dict[str, list] = defaultdict(list)
    
    def should_send_alert(self, alert_key: str) -> bool:
        """
        알림 전송 여부 판단
        
        Args:
            alert_key: 알림 식별 키 (예: "payment-api_DB_504")
        
        Returns:
            전송 허용 여부
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # 윈도우 밖의 오래된 타임스탬프 제거
        self.alert_history[alert_key] = [
            ts for ts in self.alert_history[alert_key] 
            if ts > window_start
        ]
        
        # 최대 알림 횟수 체크
        if len(self.alert_history[alert_key]) >= self.max_alerts:
            return False
        
        # 알림 허용 및 타임스탬프 기록
        self.alert_history[alert_key].append(now)
        return True
    
    def reset(self, alert_key: str):
        """특정 키의 히스토리 초기화"""
        if alert_key in self.alert_history:
            del self.alert_history[alert_key]
