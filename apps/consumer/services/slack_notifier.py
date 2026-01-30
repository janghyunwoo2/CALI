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
        analysis_result: Dict[str, str],
        rag_info: Dict[str, Any] = None
    ) -> bool:
        """장애 알림 전송 (AI 분석 결과 + RAG 정보 포함)"""
        
        # 1. Throttling 체크 (서비스명과 에러코드로 중복 필터링)
        alert_key = f"{log_data.get('service')}_{log_data.get('error_code', 'NO_CODE')}"
        if not self.throttler.should_send_alert(alert_key):
            logger.info(f"Throttling 활성화: 알림 전송 건너뜀 - {alert_key}")
            return False
        
        try:
            # 2. Slack 메시지 구성
            if rag_info is None:
                rag_info = {}
            message = self._build_slack_message(log_data, analysis_result, rag_info)
            
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
        analysis_result: Dict[str, str],
        rag_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Slack Block Kit + Attachments (Card Style Redesign)"""
        
        # 1. 메타데이터 가공
        ts = log_data.get('timestamp')
        time_str = ts.strftime('%Y-%m-%d %H:%M:%S') if isinstance(ts, datetime) else str(ts)
        service = log_data.get('service', 'unknown')
        
        # Occurrence
        occurrence_count = rag_info.get("occurrence_count", 1) 
        occurrence_text = f"최근 1분간 {occurrence_count}건 발생" if occurrence_count > 1 else "신규 발생"

        # RAG Mode & Metric
        source = rag_info.get("source", "Unknown")
        distance = rag_info.get("distance", 1.0)
        
        if source == "Cache Hit":
            mode_text = "⚡ Fast Path (Cache)"
            confidence = f"{min((1.0 - distance) * 100 + 20, 99.9):.1f}%"
            latency_text = "0ms (Cache)"
            # mode_color = "#36a64f"
        elif distance < 0.65:
            mode_text = "🤖 Medium Path (Few-Shot)"
            confidence = f"{min((1.0 - distance) * 100, 95):.1f}%"
            latency_text = rag_info.get("latency", "N/A")
            # mode_color = "#ecb22e"
        else:
            mode_text = "🧠 Slow Path (ReAct)"
            confidence = "N/A (Reasoning)"
            latency_text = rag_info.get("latency", "N/A")
            # mode_color = "#e01e5a"

        # =========================================================
        # Attachment 1: Header + Metadata (Gray/Default)
        # =========================================================
        metadata_attachment = {
            "color": "#D3D3D3", # Light Gray
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"⚠️ 장애 감지: {service} ({occurrence_text})",
                        "emoji": True
                    }
                },
                {
                    "type": "section", # Context 대신 Section+Fields 사용 (가독성 UP)
                    "fields": [
                        {"type": "mrkdwn", "text": f"*서비스:*\n{service}"},
                        {"type": "mrkdwn", "text": f"*시간:*\n{time_str}"},
                        {"type": "mrkdwn", "text": f"*모드:*\n`{mode_text}`"},
                        {"type": "mrkdwn", "text": f"*AI 응답속도:*\n{latency_text}"}
                    ]
                }
            ]
        }

        # =========================================================
        # Attachment 2: Raw Error (Red)
        # =========================================================
        error_blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "🔍 *원본 에러 메시지*"}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{log_data.get('message')}```"
                }
            }
        ]

        # 전체 로그 (Stack Trace) 추가 - Slack이 길면 'Show more'로 접어줌 (토글 효과)
        full_log = log_data.get('log_content', '')
        if full_log and len(full_log) > 50:
            error_blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "📜 *전체 로그 (Stack Trace)*"}
            })
            # Slack Block Kit 3000자 제한 고려하여 안전하게 자름
            truncated_log = full_log[:2900] + "..." if len(full_log) > 2900 else full_log
            error_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{truncated_log}```"
                }
            })

        error_attachment = {
            "color": "#FF8888", # Soft Red
            "blocks": error_blocks
        }

        # =========================================================
        # Attachment 3: AI Analysis (Purple/Lavender)
        # =========================================================
        ai_attachment = {
            "color": "#9F7AEA", # Lavender / Purple
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "🤖 *AI 지능형 분석 결과*"}
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*추정 원인:*\n{analysis_result.get('cause', '분석 중...')}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*권고 조치:*\n{analysis_result.get('action', '수동 확인이 필요합니다.')}"
                    }
                }
            ]
        }

        # =========================================================
        # Attachment 4: Thought Process (Blue - Optional)
        # =========================================================
        thought_attachment = None
        if "thought_process" in analysis_result:
            thought_attachment = {
                "color": "#4299E1", # Blue
                "blocks": [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": "💭 *AI 추론 과정 (Summary)*"}
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"```{analysis_result['thought_process']}```"
                        }
                    }
                ]
            }

        # =========================================================
        # Attachment 5: Actions (Footer Buttons)
        # =========================================================
        action_attachment = {
            "color": "#363636", # Dark
            "blocks": [
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📈 Grafana", "emoji": True},
                            "url": "http://a4f67703ff36b4ebf8452f765ad62b07-1780094694.ap-northeast-2.elb.amazonaws.com",
                            "style": "primary"
                        },

                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "👍 정확함", "emoji": True},
                            "value": "feedback_positive"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "👎 오탐", "emoji": True},
                            "value": "feedback_negative",
                            "style": "danger"
                        }
                    ]
                }
            ]
        }

        # Assemble Attachments
        attachments = [metadata_attachment, error_attachment, ai_attachment]
        if thought_attachment:
            attachments.append(thought_attachment)
        attachments.append(action_attachment)

        return {
            "text": f"🚨 장애 감지: {service}", # Fallback text
            "attachments": attachments
        }