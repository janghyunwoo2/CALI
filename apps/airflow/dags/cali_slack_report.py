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

# [중요] 상단에 있던 from openai..., from pymilvus... 를 싹 지워야 함!
# 그래야 에어플로우가 DAG 파일을 읽을 때 에러가 안 남.

# --- [상수 설정] ---
BUCKET_NAME = "cali-logs-827913617635" 
MILVUS_HOST = "milvus-standalone.milvus.svc.cluster.local"
MILVUS_PORT = "19530"
COLLECTION_NAME = "cali_rag_collection"

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
        bucket_key='solutions/*.txt',
        wildcard_match=True,
        mode='reschedule',
        aws_conn_id=None
    )

    def process_cali_rag_logic(**context):
        # --- [실행 시점에만 임포트 (Lazy Import)] ---
        # 이렇게 하면 DAG 스캔 단계에서의 Broken DAG 에러를 피할 수 있음
        try:
            from openai import OpenAI
            from pymilvus import connections, Collection
        except ImportError as e:
            print(f"❌ 라이브러리 임포트 실패: {e}")
            raise # 실행 단계에서 에러를 내서 담당자가 인지하게 함

        api_key = Variable.get("OPENAI_API_KEY")
        s3_hook = S3Hook()
        
        # 파일 리스트 확보 및 읽기
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix='solutions/')
        txt_files = [f for f in all_files if f.endswith('.txt') and f != 'solutions/']
        if not txt_files: return
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        # 데이터 가공
        try:
            log_data = json.loads(raw_content)
        except:
            log_data = {"service": "manual", "message": raw_content[:100], "action": raw_content}

        # OpenAI 임베딩
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(model="text-embedding-3-small", input=log_data.get("message", ""))
        vector = response.data[0].embedding

        # Milvus 적재 (형이 말한대로 flush 제거)
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            col = Collection(COLLECTION_NAME)
            
            # 데이터 삽입
            col.insert([{
                "vector": vector,
                "service": log_data.get("service", "unknown")[:64],
                "error_message": log_data.get("message", "")[:1024],
                "action": log_data.get("action", "")[:2048],
            }])
            # col.flush() # 형이 찾은대로 제거!
            print(f"🚀 적재 완료: {target_file}")
        finally:
            connections.disconnect("default")

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    wait_for_file >> run_main_logic