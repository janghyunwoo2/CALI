from openai import OpenAI
from config.settings import settings
from config.prompts import SYSTEM_PROMPT, build_user_prompt
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
            # prompts.py에서 프롬프트 생성
            prompt = build_user_prompt(current_log, similar_cases or [])
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3 # 사실 기반 응답을 위해 낮춤
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # 응답 포맷 정규화 (action_plan -> action 문자열 변환 등)
            if "action_plan" in result and isinstance(result["action_plan"], list):
                result["action"] = "\n".join(result["action_plan"])
            
            return result
            
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            return {"cause": "AI Analysis Failed", "action": "Please check raw logs manually."}