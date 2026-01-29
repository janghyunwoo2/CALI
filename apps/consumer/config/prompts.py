"""
=====================================================
RAG 프롬프트 템플릿 정의
=====================================================
역할: OpenAI에게 전송할 시스템 프롬프트와 유저 프롬프트 관리
목표: Incident Commander 페르소나 부여, JSON 포맷 강제, 과거 사례 우선순위 명시
=====================================================
"""

SYSTEM_PROMPT = """
당신은 대규모 마이크로서비스 플랫폼의 **장애 대응 사령관 (Incident Commander)**입니다.
당신의 목표는 **MTTR (평균 복구 시간)**을 최소화하는 것입니다.

[RULES]
1. context로 제공된 **'과거 유사 사례(Past Incidents)'를 절대적으로 신뢰**하십시오. 현재 에러가 과거 사례와 일치한다면, 동일한 해결책을 제시하세요.
2. 일치하는 과거 사례가 없다면, 당신의 SRE 지식을 활용하여 스택트레이스를 분석하십시오.
3. 답변은 간결하고 명확해야 합니다. 정중한 인사말(예: "안녕하세요")은 생략하고, 즉시 실행 가능한 **명령어(kubectl, SQL, grep)** 위주로 작성하세요.
4. 반드시 아래의 **JSON 형식**으로만 답변해야 합니다:
   {
       "cause": "근본 원인 요약 (한 문장)",
       "action_plan": ["조치 사항 1 (구체적 명령어)", "조치 사항 2 (검증 방법)"]
   }
"""

def build_user_prompt(current_log: dict, similar_cases: list) -> str:
    """
    RAG 컨텍스트를 포함한 유저 프롬프트 생성
    """
    
    # 과거 사례 포맷팅
    if similar_cases:
        formatted_cases = "다음은 현재 상황과 유사한 과거 장애 사례입니다:\n" + "\n".join([
            f"[사례 #{i+1}]\n- 원인: {case.get('cause')}\n- 조치: {case.get('action')}"
            for i, case in enumerate(similar_cases)
        ])
    else:
        formatted_cases = "참고할 만한 유사 과거 사례가 없습니다. 로그 내용을 기반으로 독립적으로 분석하십시오."

    return f"""
[현재 장애 상황]
- 서비스명: {current_log.get('service')}
- 레벨: {current_log.get('level')}
- 에러 메시지: {current_log.get('message')}
- 상세 로그 (Stack Trace):
{current_log.get('log_content')}

========================================
[지식 베이스 (과거 사례)]
{formatted_cases}
========================================

위 정보를 바탕으로 '근본 원인(cause)'과 '조치 계획(action_plan)'을 JSON으로 분석해 주세요.
"""
