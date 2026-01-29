import re

def clean_log_for_embedding(service: str, message: str, log_content: str = "") -> str:
    """
    임베딩 정확도 향상을 위한 로그 텍스트 정제 (Denoising)
    
    1. 타임스탬프, IP주소, UUID 등 변동성이 큰 값 제거
    2. 에러 메시지의 핵심 의미만 남김
    3. 서비스명과 결합하여 컨텍스트 강화
    """
    
    # 전체 텍스트 조합
    full_text = f"{service} {message} {log_content}"
    
    # 1. 타임스탬프 제거 (ISO8601 등)
    # 예: 2026-01-29 10:00:59, 2024-01-01T12:00:00...
    full_text = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?', '', full_text)
    
    # 2. IP 주소 제거 (IP는 매번 바뀌므로 의미적 유사도에 방해됨)
    full_text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>', full_text)
    
    # 3. UUID/Hash 값 제거 (긴 16진수 문자열)
    full_text = re.sub(r'\b[a-fA-F0-9]{32}\b', '<UUID>', full_text)
    full_text = re.sub(r'\b[a-fA-F0-9-]{36}\b', '<UUID>', full_text)
    
    # 4. 불필요한 공백 정리
    clean_text = " ".join(full_text.split())
    
    # 5. 길이 제한 (너무 길면 앞부분 핵심만)
    return clean_text[:2000]
