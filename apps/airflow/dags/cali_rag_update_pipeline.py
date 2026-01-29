import os
import requests
import json
import subprocess
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 
from airflow.models import Variable

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
    'retries': 2,                 # 리트라이 횟수 살짝 늘림
    'retry_delay': timedelta(seconds=30), # 실패 시 재시도 간격을 30초로 단축 (빨리빨리)
}

with DAG(
    dag_id='cali_rag_unified_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,
    catchup=False,
    tags=['cali', 'rag', 'milvus', 'openai']
) as dag:

    # --- [태스크 1: S3 파일 감시 - 최적화 버전] ---
    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt',
        wildcard_match=True,
        timeout=60 * 30,             # 타임아웃을 30분으로 짧게 잡음 (너무 오래 기다리지 않게)
        poke_interval=30,            # 30초마다 확인
        mode='reschedule',           # 핵심: 대기 중에는 Worker 리소스를 반환해서 효율 증가
        exponential_backoff=True     # 파일이 계속 없으면 체크 간격을 조금씩 늘림
    )

    def process_cali_rag_logic(**context):
        def install_and_import(package):
            try:
                __import__(package)
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        install_and_import('openai')
        install_and_import('pymilvus')
        
        from openai import OpenAI
        from pymilvus import connections, Collection

        try:
            api_key = Variable.get("OPENAI_API_KEY")
        except Exception as e:
            raise ValueError(f"Variable 'OPENAI_API_KEY' 누락: {e}")
        
        s3_hook = S3Hook(aws_conn_id='aws_default')
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            return # 파일 없으면 에러 내지 말고 조용히 종료
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        try:
            log_data = json.loads(raw_content)
        except:
            log_data = {
                "service": "manual",
                "message": raw_content[:100],
                "cause": "N/A",
                "action": raw_content
            }

        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "")
        )
        vector = response.data[0].embedding

        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            svc = log_data.get("service", "unknown").replace("'", "\\'")
            msg = log_data.get("message", "").replace("'", "\\'")
            delete_expr = f"service == '{svc}' && error_message == '{msg}'"
            collection.delete(delete_expr)
            collection.flush()
            
            row = {
                "vector": vector,
                "service": log_data.get("service", "unknown")[:64],
                "error_message": log_data.get("message", "")[:1024],
                "cause": log_data.get("cause", "")[:2048],
                "action": log_data.get("action", "")[:2048],
            }
            
            collection.insert([row])
            collection.flush()
            print(f"🚀 Milvus 적재 완료: {target_file}")
            
        finally:
            connections.disconnect("default")

        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    def send_report(**context):
        if SLACK_WEBHOOK_URL:
            msg = "✅ [Cali RAG] 업데이트 완료!"
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": msg}))

    notify_complete = PythonOperator(task_id='notify_complete', python_callable=send_report)

    wait_for_file >> run_main_logic >> notify_complete