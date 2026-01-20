"""
=====================================================
로그 집계 배치 DAG
=====================================================
설명: S3 로그 데이터를 집계하여 통계 생성
스케줄: 매 시간
역할: 에러 빈도, 서비스별 통계 등 집계
=====================================================
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    'owner': 'cali',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 19),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'log_aggregation',
    default_args=default_args,
    description='로그 데이터 집계 및 통계 생성',
    schedule_interval='0 * * * *',  # 매 시간
    catchup=False,
    tags=['aggregation', 'batch'],
)


def aggregate_logs(**context):
    """로그 집계 실행"""
    # TODO: S3 로그 집계 로직 구현
    # 1. S3에서 지난 1시간 로그 로드
    # 2. 에러 빈도, 서비스별 통계 계산
    # 3. 결과를 OpenSearch 또는 S3에 저장
    pass


aggregation_task = PythonOperator(
    task_id='aggregate_logs',
    python_callable=aggregate_logs,
    dag=dag,
)

# TODO: 추가 태스크 (통계 저장, 알림 등)
