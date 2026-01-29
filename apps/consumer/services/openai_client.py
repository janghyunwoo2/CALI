from openai import OpenAI
from config.settings import settings
from config.prompts import build_user_prompt
from utils.logger import setup_logger
import json

logger = setup_logger(__name__)

class OpenAIClient:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o" # MVP 모델 고정

    
    def create_embedding(self, text: str) -> list:
        """텍스트 임베딩 생성 (text-embedding-3-small)"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return []

    def analyze_log(self, current_log: dict, similar_cases: list = None) -> dict:
        try:
            # 전략 결정 로직 (Selector)
            # Tier 1 (Fast Path)은 여기서 처리되지 않음 (KinesisConsumer에서 처리)
            # Tier 2 (Few-Shot): 유사 사례가 있고, 유사도가 일정 수준 이상일 때 (Distance < 0.65)
            # Tier 3 (ReAct): 유사 사례가 없거나, 매우 다를 때 (Distance >= 0.65)
            
            mode = "react"
            temperature = 0.5
            
            if similar_cases:
                # 가장 유사한 사례의 거리값 확인
                # Milvus L2: 0에 가까울수록 유사함
                best_score = similar_cases[0].get('score', 1.0)
                
                if best_score < 0.65:
                    mode = "few_shot"
                    temperature = 0.3 # 사실 기반 응답
                    logger.info(f"🤖 AI 모드: Few-Shot (유사도 양호: {best_score:.4f})")
                else:
                    mode = "react"
                    temperature = 0.7 # 추론을 위해 창의성 허용
                    logger.info(f"🧠 AI 모드: ReAct (유사도 낮음: {best_score:.4f})")
            else:
                mode = "react"
                temperature = 0.7
                logger.info("🧠 AI 모드: ReAct (유사 사례 없음)")

            # prompts.py에서 프롬프트 생성
            from config.prompts import get_system_prompt, build_user_prompt # 늦은 import (순환 참조 방지 등)
            
            system_prompt = get_system_prompt(mode)
            user_prompt = build_user_prompt(current_log, similar_cases or [])
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=temperature,
                timeout=10.0 # 10초 타임아웃 강제 (SRE 안정성)
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 응답 포맷 정규화 (action_plan -> action 문자열 변환 등)
            if "action_plan" in result and isinstance(result["action_plan"], list):
                result["action"] = "\n".join(result["action_plan"])
            
            # ReAct 추론 과정이 있다면 메타데이터에 포함할 수도 있음 (현재는 리턴값에 포함됨)
            
            return result
            
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            return {"cause": "AI Analysis Failed", "action": "Please check raw logs manually."}
