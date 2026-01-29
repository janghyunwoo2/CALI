import requests
from typing import Dict, Any
from datetime import datetime

from config.settings import settings
# MVP 단계에서 Throttler가 미구현 상태라면 아래 줄을 주석 처리하거나 빈 클래스로 대체하세요.
try:
    from utils.throttle import Throttler
except ImportError:
    class Throttler:
        def should_send_alert(self, key): return True

from utils.logger import setup_logger

logger = setup_logger(__name__)

class SlackNotifier:
    """Slack 알림 클라이언트"""
    
    def __init__(self):
        """초기화"""
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        # 설정값이 없을 경우를 대비한 기본값 처리
        window = getattr(settings, 'THROTTLE_WINDOW_SECONDS', 60)
        max_alerts = getattr(settings, 'THROTTLE_MAX_ALERTS', 5)
        
        self.throttler = Throttler(window_seconds=window, max_alerts=max_alerts)
        logger.info("Slack Notifier 초기화 완료")
    
    def send_alert(
        self, 
        log_data: Dict[str, Any], 
        analysis_result: Dict[str, str]
    ) -> bool:
        """장애 알림 전송 (AI 분석 결과 포함)"""
        
        # 1. Throttling 체크 (서비스명과 에러코드로 중복 필터링)
        alert_key = f"{log_data.get('service')}_{log_data.get('error_code', 'NO_CODE')}"
        if not self.throttler.should_send_alert(alert_key):
            logger.info(f"Throttling 활성화: 알림 전송 건너뜀 - {alert_key}")
            return False
        
        try:
            # 2. Slack 메시지 구성
            message = self._build_slack_message(log_data, analysis_result)
            
            # 3. Webhook 전송
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack 알림 전송 성공: {alert_key}")
            return True
            
        except Exception as e:
            logger.error(f"Slack 알림 전송 실패: {e}")
            return False
    
    def _build_slack_message(
        self, 
        log_data: Dict[str, Any], 
        analysis_result: Dict[str, str]
    ) -> Dict[str, Any]:
        """Slack Block Kit 포맷 구성"""
        
        # 타임스탬프 가독성 처리
        ts = log_data.get('timestamp')
        time_str = ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts)

        return {
            "text": f"🚨 CALI 장애 감지 리포트: {log_data.get('service')}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 장애 감지: {log_data.get('service')}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Service:*\n{log_data.get('service')}"},
                        {"type": "mrkdwn", "text": f"*Level:*\n`{log_data.get('level')}`"},
                        {"type": "mrkdwn", "text": f"*Time:*\n{time_str}"},
                        {"type": "mrkdwn", "text": f"*Error Code:*\n`{log_data.get('error_code', 'N/A')}`"}
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*원본 로그 메시지:*\n```{log_data.get('message')}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🤖 AI 지능형 분석 결과*\n"
                                f"• *추정 원인:* {analysis_result.get('cause', '분석 중...')}\n"
                                f"• *권고 조치:* {analysis_result.get('action', '수동 확인이 필요합니다.')}"
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Pod Name: {log_data.get('pod_name', 'unknown')} | CALI AIOps Engine v1.0"
                        }
                    ]
                }
            ]
        }