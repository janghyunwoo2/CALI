# =====================================================
# Airflow Dockerfile
# =====================================================
# 설명: 커스텀 Airflow 이미지 빌드
# 추가: Great Expectations, AWS Provider 등
# =====================================================

FROM apache/airflow:2.10.4-python3.11

# 추가 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# DAG 및 플러그인 복사 (옵션)
# COPY dags /opt/airflow/dags
# COPY plugins /opt/airflow/plugins
