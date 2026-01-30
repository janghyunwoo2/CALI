import os
import requests
import json
import sys
from datetime import datetime, timedelta

# 에어플로우 기본 모듈
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 
from airflow.models import Variable

# 담당자가 설치해준 외부 라이브러리 (이제 바로 사용 가능!)
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

    # --- [태스크 1: S3 파일 감시] ---
    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt',
        wildcard_match=True,
        timeout=60 * 30,
        poke_interval=30,
        mode='reschedule',
        aws_conn_id=None, # 노드 권한(IAM Role)을 사용하도록 설정
        exponential_backoff=True
    )

    # --- [태스크 2: 메인 로직 (임베딩 & Milvus 적재)] ---
    def process_cali_rag_logic(**context):
        # 1. API 키 로드
        try:
            api_key = Variable.get("OPENAI_API_KEY")
        except Exception as e:
            raise ValueError(f"Airflow Variable 'OPENAI_API_KEY'가 설정되지 않았습니다: {e}")
        
        # 2. S3Hook으로 대상 파일 찾기
        s3_hook = S3Hook()
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            print("처리할 파일이 없습니다.")
            return 
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        print(f"📄 대상 파일 읽기 완료: {target_file}")
        
        # 3. 데이터 파싱 (JSON 우선, 실패 시 Raw Text)
        try:
            log_data = json.loads(raw_content)
        except:
            log_data = {
                "service": "manual",
                "message": raw_content[:100],
                "cause": "N/A",
                "action": raw_content
            }

        # 4. OpenAI 임베딩 생성
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "")
        )
        vector = response.data[0].embedding

        # 5. Milvus 연결 및 데이터 적재
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            # 중복 데이터 제거 (Upsert 로직)
            svc = log_data.get("service", "unknown").replace("'", "\\'")
            msg = log_data.get("message", "").replace("'", "\\'")
            delete_expr = f"service == '{svc}' && error_message == '{msg}'"
            collection.delete(delete_expr)
            collection.flush()
            
            # 신규 데이터 삽입
            row = {
                "vector": vector,
                "service": log_data.get("service", "unknown")[:64],
                "error_message": log_data.get("message", "")[:1024],
                "cause": log_data.get("cause", "")[:2048],
                "action": log_data.get("action", "")[:2048],
            }
            collection.insert([row])
            collection.flush()
            print(f"🚀 Milvus 적재 성공: {target_file}")
            
        finally:
            connections.disconnect("default")

        # 6. S3 파일 정리 (처리 완료 폴더로 이동)
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
        print(f"📁 파일 이동 완료: {SOLUTIONS_PREFIX} -> {PROCESSED_PREFIX}")

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    # --- [태스크 3: 완료 알림] ---
    def send_report(**context):
        if SLACK_WEBHOOK_URL:
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": "✅ Cali RAG 지식 베이스 업데이트 완료!"}))

    notify_complete = PythonOperator(task_id='notify_complete', python_callable=send_report)

    # 파이프라인 흐름: 감시 -> 실행 -> 알림
    wait_for_file >> run_main_logic >> notify_complete