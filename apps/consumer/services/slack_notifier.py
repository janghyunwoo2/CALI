"""
=====================================================
Slack 알림 서비스
=====================================================
설명: Slack Webhook을 통한 장애 알림 전송
역할: Throttling 적용하여 동일 에러 폭주 시 알림 최적화
=====================================================
"""

import requests
from typing import Dict, Any
from datetime import datetime

from config.settings import settings
from utils.throttle import Throttler
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SlackNotifier:
    """Slack 알림 클라이언트"""
    
    def __init__(self):
        """초기화"""
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        self.throttler = Throttler(
            window_seconds=settings.THROTTLE_WINDOW_SECONDS,
            max_alerts=settings.THROTTLE_MAX_ALERTS
        )
        logger.info("Slack Notifier 초기화")
    
    def send_alert(
        self, 
        log_data: Dict[str, Any], 
        analysis_result: Dict[str, str]
    ) -> bool:
        """
        장애 알림 전송 (Throttling 적용)
        
        Args:
            log_data: 로그 데이터
            analysis_result: AI 분석 결과 (cause, action)
        
        Returns:
            전송 성공 여부
        """
        # Throttling 체크
        alert_key = f"{log_data.get('service')}_{log_data.get('error_code')}"
        if not self.throttler.should_send_alert(alert_key):
            logger.debug(f"Throttling: 알림 스킵 - {alert_key}")
            return False
        
        try:
            # Slack 메시지 구성
            message = self._build_slack_message(log_data, analysis_result)
            
            # Webhook 전송
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack 알림 전송 완료: {alert_key}")
            return True
            
        except Exception as e:
            logger.error(f"Slack 알림 전송 실패: {e}")
            return False
    
    def _build_slack_message(
        self, 
        log_data: Dict[str, Any], 
        analysis_result: Dict[str, str]
    ) -> Dict[str, Any]:
        """Slack 메시지 포맷 구성"""
        return {
            "text": f"🚨 [{log_data.get('level')}] {log_data.get('service')} 장애 발생",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 장애 알림: {log_data.get('service')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*서비스:*\n{log_data.get('service')}"},
                        {"type": "mrkdwn", "text": f"*레벨:*\n{log_data.get('level')}"},
                        {"type": "mrkdwn", "text": f"*에러 코드:*\n{log_data.get('error_code', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*시간:*\n{log_data.get('timestamp')}"},
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*메시지:*\n```{log_data.get('message')}```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*🔍 AI 분석 결과:*\n• *원인:* {analysis_result.get('cause')}\n• *조치:* {analysis_result.get('action')}"
                    }
                }
            ]
        }
