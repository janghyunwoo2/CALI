import os
import requests
import json
import sys
import subprocess
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
        # 1. 팩트 체크 (환경 검증)
        print(f"🐍 Python Executable: {sys.executable}")
        try:
            pip_list = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
            print(f"📋 Installed Packages:\n{pip_list}")
        except:
            print("⚠️ 패키지 목록 조회 실패")

        # 2. Lazy Import
        try:
            from openai import OpenAI
            from pymilvus import connections, Collection
        except ImportError as e:
            print(f"❌ 라이브러리 인식 실패: {e}")
            raise 

        # 3. 데이터 로드
        api_key = Variable.get("OPENAI_API_KEY")
        s3_hook = S3Hook()
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            return 
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        try:
            log_data = json.loads(raw_content)
        except:
            log_data = {"service": "manual", "message": raw_content[:100], "action": raw_content}

        # 4. OpenAI 임베딩
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "")
        )
        vector = response.data[0].embedding

        # 5. Milvus 적재 (문법 오류 수정 포인트)
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            # 따옴표 이스케이프 처리를 안전하게 변수로 분리 (103번줄 에러 방지)
            safe_svc = log_data.get("service", "unknown").replace("'", "\\'")
            safe_msg = log_data.get("message", "").replace("'", "\\'")
            
            # f-string 내부의 복잡한 연산을 밖으로 뺌
            delete_expr = f"service == '{safe_svc}' && error_message == '{safe_msg}'"
            collection.delete(delete_expr)
            
            # 데이터 삽입 (flush는 형이 찾은대로 제거)
            collection.insert([{
                "vector": vector,
                "service": safe_svc[:64],
                "error_message": safe_msg[:1024],
                "cause": log_data.get("cause", "N/A")[:2048],
                "action": log_data.get("action", "")[:2048],
            }])
            
            print(f"🚀 Milvus 적재 성공: {target_file}")
            
        finally:
            connections.disconnect("default")

        # 6. S3 정리
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    run_main_logic