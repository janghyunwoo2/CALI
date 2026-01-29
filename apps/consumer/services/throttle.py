import time
from collections import defaultdict
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Throttle:
    """
    간단한 메모리 기반 스로틀링 클래스
    동일한 (Service, Error Message) 쌍에 대해 일정 시간 내 알림 횟수 제한
    """
    
    def __init__(self):
        # Key: (service, message_signature)
        # Value: list of timestamps
        self.alert_history = defaultdict(list)
        self.window_seconds = settings.THROTTLE_WINDOW_SECONDS
        self.max_alerts = settings.THROTTLE_MAX_ALERTS

    def should_send_alert(self, service: str, message: str) -> bool:
        """알림 전송 여부 결정"""
        key = (service, message[:100]) # 메시지가 너무 길면 앞부분만 키로 사용
        now = time.time()
        
        # 1. 만료된 기록 정리 (Window 바깥의 타임스탬프 제거)
        self.alert_history[key] = [
            t for t in self.alert_history[key] 
            if now - t < self.window_seconds
        ]
        
        # 2. 횟수 체크
        current_count = len(self.alert_history[key])
        
        if current_count < self.max_alerts:
            self.alert_history[key].append(now)
            return True
        else:
            logger.debug(f"🔇 알림 스로틀링 중: {service} (Last {self.window_seconds}s: {current_count} hits)")
            return False
