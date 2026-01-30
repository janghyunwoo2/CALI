import os
import requests
import json
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 
from airflow.models import Variable

# 담당자가 설치해준 최신 라이브러리 사용
from openai import OpenAI
from pymilvus import connections, Collection

# --- [1. 상수 설정] ---
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

    # 1. S3 파일 감시
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

    # 2. 메인 로직 (Milvus 2.6+ 대응)
    def process_cali_rag_logic(**context):
        # API 키 로드
        api_key = Variable.get("OPENAI_API_KEY")
        
        # S3 데이터 로드
        s3_hook = S3Hook()
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            return 
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        # 데이터 파싱
        try:
            log_data = json.loads(raw_content)
        except:
            log_data = {
                "service": "manual",
                "message": raw_content[:100],
                "cause": "N/A",
                "action": raw_content
            }

        # OpenAI 임베딩 생성
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "")
        )
        vector = response.data[0].embedding

        # Milvus 적재 (에러 원인 flush() 제거 버전)
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            # [중복 제거]
            svc = log_data.get("service", "unknown").replace("'", "\\'")
            msg = log_data.get("message", "").replace("'", "\\'")
            delete_expr = f"service == '{svc}' && error_message == '{msg}'"
            
            # Milvus 최신 버전은 delete 후 굳이 flush 안 해도 됨
            collection.delete(delete_expr)
            
            # [데이터 삽입]
            row = {
                "vector": vector,
                "service": svc[:64],
                "error_message": msg[:1024],
                "cause": log_data.get("cause", "")[:2048],
                "action": log_data.get("action", "")[:2048],
            }
            
            # insert만 해도 Milvus가 알아서 저장함 (flush() 호출 시 TypeError 발생 방지)
            collection.insert([row])
            
            print(f"🚀 Milvus 적재 성공 (Auto-flush): {target_file}")
            
        finally:
            connections.disconnect("default")

        # S3 정리
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    wait_for_file >> run_main_logic