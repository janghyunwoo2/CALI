import time
from typing import Dict, List, Any
from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Throttle:
    """
    집계형 스로틀링 (Aggregation Throttle)
    - 1단계: 첫 번째 발생 시 즉시 True 반환 (First Alert)
    - 2단계: 이후 Window 시간 동안은 내부 카운트만 증가하고 False 반환
    - 3단계: Window 종료 시, 누적된 카운트를 반환하여 요약 알림 발송 유도
    """
    
    def __init__(self):
        # Key: (service, message_signature)
        # Value: {'start_time': float, 'count': int}
        self.active_windows: Dict[tuple, Dict[str, Any]] = {}
        self.window_seconds = settings.THROTTLE_WINDOW_SECONDS

    def record_occurrence(self, service: str, message: str) -> bool:
        """
        이벤트 기록 및 즉시 알림 여부 판단
        Returns:
            bool: True면 "최초 발생(First Alert)"이므로 즉시 알림 발송 필요
                  False면 "집계 중"이므로 알림 생략
        """
        key = (service, message[:100])
        now = time.time()

        # 1. 신규 발생 (또는 윈도우 만료된 잔여 데이터)
        if key not in self.active_windows:
            self.active_windows[key] = {
                'start_time': now, 
                'count': 1
            }
            return True # First Alert!
        
        # 2. 윈도우 체크 (만약 flush가 제때 안 되어서 남아있는 경우)
        if now - self.active_windows[key]['start_time'] > self.window_seconds:
            # 기존 윈도우 폐기하고 새로 시작
            self.active_windows[key] = {
                'start_time': now, 
                'count': 1
            }
            return True # New Window First Alert!

        # 3. 집계 (Count Up)
        self.active_windows[key]['count'] += 1
        return False # Suppress

    def get_summaries_to_send(self) -> List[Dict[str, Any]]:
        """
        만료된 윈도우를 확인하여 요약 알림이 필요한 건들을 반환
        Returns:
            List[Dict]: [{'service', 'message', 'count', 'duration'}]
        """
        now = time.time()
        summaries = []
        expired_keys = []

        for key, data in self.active_windows.items():
            duration = now - data['start_time']
            
            # 윈도우 시간이 지났는지 확인
            if duration >= self.window_seconds:
                # 2건 이상일 때만 요약 알림 (1건은 이미 First Alert으로 처리됨)
                if data['count'] > 1:
                    summaries.append({
                        'service': key[0],
                        'message': key[1], # message signature
                        'count': data['count'],
                        'duration': int(duration)
                    })
                
                expired_keys.append(key)
        
        # 처리된 윈도우 삭제
        for k in expired_keys:
            del self.active_windows[k]
            
        return summaries
