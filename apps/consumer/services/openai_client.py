import json
import re
from openai import OpenAI
from config.settings import settings
from config.prompts import build_user_prompt
from utils.logger import setup_logger
import json
import re

logger = setup_logger(__name__)

class AIClient:
    def __init__(self):
        # Embeddings 및 Generation 모두 OpenAI 사용
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        logger.info(f"🤖 AI Provider: OpenAI (Model: {self.model})")

    
    def create_embedding(self, text: str) -> list:
        """텍스트 임베딩 생성 (text-embedding-3-small) - Always OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
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
            mode = "react"
            temperature = 0.5
            
            if similar_cases:
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

            # 프롬프트 생성
            from config.prompts import get_system_prompt, build_user_prompt
            system_prompt = get_system_prompt(mode)
            user_prompt = build_user_prompt(current_log, similar_cases or [])
            
            # Provider별 요청 분기
            return self._analyze_with_openai(system_prompt, user_prompt, temperature)
            
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            return {"cause": "AI Analysis Failed", "action": "Please check raw logs manually."}

    def _analyze_with_openai(self, system_prompt, user_prompt, temperature):
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
            timeout=10.0
        )
        return self._parse_result(response.choices[0].message.content)


    def _parse_result(self, content_str: str) -> dict:
        """JSON 파싱 및 포맷팅 공통 로직"""
        try:
            # JSON 마커가 있는 경우 제거 (```json ... ```)
            if "```json" in content_str:
                content_str = content_str.split("```json")[1].split("```")[0].strip()
            elif "```" in content_str:
                content_str = content_str.split("```")[1].split("```")[0].strip()
                
            result = json.loads(content_str)
            
            def format_list(items):
                if isinstance(items, list):
                    cleaned_items = [re.sub(r'^\d+\s*[\.\)]\s*', '', item) for item in items]
                    return "\n\n".join([f"{i+1}. {item}" for i, item in enumerate(cleaned_items)])
                return str(items)

            if "cause" in result:
                result["cause"] = format_list(result["cause"])
            if "action_plan" in result:
                result["action"] = format_list(result["action_plan"])
            
            # ReAct 추론 과정이 있다면 메타데이터에 포함할 수도 있음 (현재는 리턴값에 포함됨)
            
            # ReAct 추론 과정이 있다면 메타데이터에 포함할 수도 있음 (현재는 리턴값에 포함됨)
            
            return result
        except json.JSONDecodeError:
            logger.error(f"JSON 파싱 실패. 원본 응답: {content_str}")
            return {"cause": "Parsing Error", "action": content_str[:200]}
