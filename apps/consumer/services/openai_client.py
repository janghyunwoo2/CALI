from openai import OpenAI
from config.settings import settings
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
            prompt = self._build_rag_prompt(current_log, similar_cases or [])
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 SRE 전문가입니다. 로그를 분석하여 원인과 조치법을 JSON으로 답하세요. 필드: cause, action"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"분석 실패: {e}")
            return {"cause": "분석 엔진 오류", "action": "로그 전문 수동 확인 요망"}

    def _build_rag_prompt(self, current_log: dict, similar_cases: list) -> str:
        # 지식 베이스가 없을 때는 로그 정보에 집중하도록 구성
        case_text = f"참고 사례: {similar_cases}" if similar_cases else "참고할 과거 사례 없음."
        return f"""
        분석할 로그:
        - 서비스: {current_log.get('service')}
        - 에러: {current_log.get('message')}
        - 상세내용: {current_log.get('log_content')}
        
        {case_text}
        
        위 내용을 바탕으로 장애 원인(cause)과 운영자가 즉시 취해야 할 조치(action)를 한글로 작성하세요.
        """