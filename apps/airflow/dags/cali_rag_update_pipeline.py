import os
import requests
import json
import sys
import subprocess  # 패키지 목록 확인용
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 
from airflow.models import Variable

# --- [상수 설정] ---
BUCKET_NAME = "cali-logs-827913617635" 
MILVUS_HOST = "milvus-standalone.milvus.svc.cluster.local"
MILVUS_PORT = "19530"
COLLECTION_NAME = "cali_rag_collection"
SLACK_WEBHOOK_URL = ""

SOLUTIONS_PREFIX = 'solutions/'
PROCESSED_PREFIX = 'processed/'

default_args = {
    'owner': 'cali_admin',
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}

with DAG(
    dag_id='cali_rag_unified_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,
    catchup=False,
    tags=['cali', 'rag', 'milvus', 'openai']
) as dag:

    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt',
        wildcard_match=True,
        timeout=60 * 30,
        poke_interval=30,
        mode='reschedule',
        aws_conn_id=None,
        exponential_backoff=True
    )

    def process_cali_rag_logic(**context):
        # --- [1. 환경 검증 로직 추가] ---
        print(f"🐍 Python Executable: {sys.executable}")
        print(f"📂 Python Path: {sys.path}")
        
        try:
            # pip list 명령어로 설치된 패키지 강제 확인
            pip_list = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
            print(f"📋 Installed Packages:\n{pip_list}")
        except Exception as e:
            print(f"⚠️ 패키지 목록을 가져오지 못했습니다: {e}")

        # --- [2. Lazy Import (Broken DAG 방지)] ---
        try:
            from openai import OpenAI
            from pymilvus import connections, Collection
        except