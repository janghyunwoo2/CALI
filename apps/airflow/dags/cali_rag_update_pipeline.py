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

# --- [1. 상수 설정] ---
BUCKET_NAME = "cali-logs-827913617635" 
MILVUS_HOST = "milvus-standalone.milvus.svc.cluster.local"
MILVUS_PORT = "19530"
COLLECTION_NAME = "cali_rag_collection"
SLACK_WEBHOOK_URL = "" # 필요시 입력

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

    # 1. S3 파일 감시 (solutions/ 폴더에 .txt 파일이 들어오는지 체크)
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

    # 2. 메인 로직 (임베딩 및 Milvus 적재)
    def process_cali_rag_logic(**context):
        # [A] 환경 검증 및 패키지 리스트 확인 (담당자 압박용 로그)
        print(f"🐍 Python Executable: {sys.executable}")
        try:
            pip_list = subprocess.check_output([sys.executable, "-m", "pip", "list"]).decode()
            print(f"📋 Installed Packages:\n{pip_list}")
        except:
            print("⚠️ 패키지 목록 조회 실패")

        # [B] Lazy Import (서버 환경 미비 시 DAG 깨짐 방지)
        try:
            from openai import OpenAI
            from pymilvus import connections, Collection
        except ImportError as e:
            print(f"❌ 라이브러리 인식 실패: {e}")
            raise 

        # [C] 데이터 로드 로직
        api_key = Variable.get("OPENAI_API_KEY")
        s3_hook = S3Hook()
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            print("처리할 파일이 없습니다.")
            return 
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        print(f"📄 파일 로드 완료: {target_file}")
        
        try:
            log_data = json.loads(raw_content)
        except:
            log_data = {"service": "manual", "message": raw_content[:100], "action": raw_content}

        # [D] OpenAI 임베딩 생성
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "")
        )
        vector = response.data[0].embedding
        print("✅ OpenAI 임베딩 생성 완료")

        # [E] Milvus 적재 (문법 오류 수정 및 flush 제거)
        try:
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            # 따옴표 처리를 f-string 밖에서 미리 수행 (TypeError/SyntaxError 방지)
            svc_name = str(log_data.get("service", "unknown")).replace("'", "\\'")
            err_msg = str(log_data.get("message", "")).replace("'", "\\'")
            
            # 기존 데이터 삭제 (Upsert 효과)
            delete_expr = f"service == '{svc_name}' && error_message == '{err_msg}'"
            collection.delete(delete_expr)
            
            # 데이터 삽입 (Milvus 2.6+ 권장 사항: flush() 호출 생략)
            collection.insert([{
                "vector": vector,
                "service": svc_name[:64],
                "error_message": err_msg[:1024],
                "cause": str(log_data.get("cause", "N/A"))[:2048],
                "action": str(log_data.get("action", ""))[:2048],
            }])
            
            print(f"🚀 Milvus 적재 성공: {target_file}")
            
        finally:
            connections.disconnect("default")

        # [F] S3 파일 정리 (처리 완료 폴더로 이동)
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
        print(f"📁 파일 이동 완료: {target_file} -> {dest_key}")

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    # 알림 로직 (선택 사항)
    def send_report(**context):
        if SLACK_WEBHOOK_URL:
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": "✅ RAG 업데이트 완료!"}))

    notify_complete = PythonOperator(task_id='notify_complete', python_callable=send_report)

    # 파이프라인 흐름
    wait_for_file >> run_main_logic >> notify_complete