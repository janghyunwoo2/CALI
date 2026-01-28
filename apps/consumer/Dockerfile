# =====================================================
# Consumer Dockerfile
# =====================================================
# 설명: Python Consumer 애플리케이션 이미지 빌드
# 역할: Kinesis 구독 → Pydantic 검증 → RAG 분석 → Slack 알림
# =====================================================

FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "print('healthy')" || exit 1

# 실행
CMD ["python", "main2.py"]
