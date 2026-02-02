import requests
from typing import Dict, Any
from datetime import datetime, timedelta

from config.settings import settings
# MVP 단계에서 Throttler가 미구현 상태라면 아래 줄을 주석 처리하거나 빈 클래스로 대체하세요.
from services.throttle import Throttle

from utils.logger import setup_logger

logger = setup_logger(__name__)

class SlackNotifier:
    """Slack 알림 클라이언트"""
    
    def __init__(self):
        """초기화"""
        self.webhook_url = settings.SLACK_WEBHOOK_URL
        # 설정값이 없을 경우를 대비한 기본값 처리
        window = getattr(settings, 'THROTTLE_WINDOW_SECONDS', 60)
        # max_alerts = getattr(settings, 'THROTTLE_MAX_ALERTS', 5) # Not used
        
        # [Fix] Throttle 클래스 사용 (기존 Throttler -> Throttle)
        self.throttler = Throttle()
        logger.info("Slack Notifier 초기화 완료")
    
    def send_summary_alert(
        self, 
        service: str, 
        message_sig: str, 
        count: int, 
        duration: int
    ) -> bool:
        """요약 알림 전송 (집계된 추가 발생 알림)"""
        try:
            alert_key = f"{service}_{message_sig}"
            
            # 요약 메시지 구성
            slack_msg = {
                "text": f"📊 장애 알림 요약: {service}",
                "attachments": [
                    {
                        "color": "#808080",  # Gray
                        "blocks": [
                            {
                                "type": "section",
                                "text": {
                                    "type": "mrkdwn", 
                                    "text": f"📊 *추가 발생 알림 (Aggregation)*\n지난 {duration}초간 동일한 에러가 *총 {count}건* 더 발생했습니다."
                                }
                            },
                            {
                                "type": "context",
                                "elements": [
                                    {"type": "mrkdwn", "text": f"*Service:* {service}"},
                                    {"type": "mrkdwn", "text": f"*Error:* {message_sig}..."}
                                ]
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=slack_msg,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"Slack 요약 알림 전송 성공: {alert_key} (Count: {count})")
            return True
            
        except Exception as e:
            logger.error(f"Slack 요약 알림 전송 실패: {e}")
            return False

    def send_alert(
        self, 
        log_data: Dict[str, Any], 
        analysis_result: Dict[str, str],
        rag_info: Dict[str, Any] = None
    ) -> bool:
        """장애 알림 전송 (AI 분석 결과 + RAG 정보 포함)"""
        
        # NOTE: Throttling 체크는 이제 외부(KinesisConsumer)에서 Throttle.record_occurrence()로 수행함.
        # 따라서 여기서는 무조건 보낸다고 가정하지만, 호환성을 위해 남겨둡니다.
        # 만약 KinesisConsumer가 아닌 곳에서 호출한다면 여기서 체크해야 할 수도 있음.
        
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
            
            logger.info(f"Slack 알림 전송 성공: {log_data.get('service')}")
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
        if isinstance(ts, datetime):
            ts = ts + timedelta(hours=9) # KST 강제 보정 (User Request)
            time_str = ts.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = str(ts)
        
        service = log_data.get('service', 'unknown')
        
        # Occurrence
        occurrence_count = rag_info.get("occurrence_count", 1) 
        occurrence_text = f"최근 1분간 {occurrence_count}건 발생" if occurrence_count > 1 else "신규 발생"

        # RAG Mode & Metric (Re-designed)
        source = rag_info.get("source", "Unknown")
        distance = rag_info.get("distance", 1.0)
        
        # 신뢰도 및 모드 결정 로직
        # Milvus L2 Distance -> Cosine Similarity 변환
        # OpenAI 임베딩은 Normalized이므로: Distance^2 = 2 * (1 - Similarity)
        # Similarity = 1 - (Distance^2 / 2)
        similarity = 1.0 - (distance ** 2 / 2.0)
        confidence_val = max(0.0, similarity * 100.0)

        if source == "Cache Hit":
            mode_text = "지식 기반 (Cached)" 
            badge = "📚" 
            latency_text = "0ms (Cache)"
            confidence_val = 99.9 # Cache는 100% 가정
        elif confidence_val >= 80.0: # Sim 0.8 이상 (Standard/Few-Shot)
            mode_text = "지식 기반 (Standard)"
            badge = "🔍" 
            latency_text = rag_info.get("latency", "N/A")
        else:
            mode_text = "심층 추론 (Advanced)"
            badge = "❓"
            latency_text = rag_info.get("latency", "N/A")

        confidence_str = f"{confidence_val:.1f}%"
        
        # 4. Similarity Bar 생성 (ASCII Art)
        # [▮▮▮▮▯▯▯▯▯▯] 10칸 (Thinner/Sleeker style)
        if confidence_val >= 99.0:
            fill_count = 10
        else:
            fill_count = int(confidence_val / 10)
            
        empty_count = 10 - fill_count
        bar_graph = "▮" * fill_count + "▯" * empty_count
        
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
                        "text": f"💡 분석 결과: {service}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*발생 시각:*\n{time_str}"},
                        {"type": "mrkdwn", "text": f"*분석 모드:*\n{badge} {mode_text}"},
                        {"type": "mrkdwn", "text": f"*지식 일치율:*\n`[{bar_graph}]` {confidence_str}"},
                        {"type": "mrkdwn", "text": f"*AI 응답속도:*\n{latency_text}"},
                        {"type": "mrkdwn", "text": f"*발생 빈도:*\n{occurrence_text}"}
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