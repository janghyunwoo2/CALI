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
# Airflow Connection 정보를 가져오기 위한 Hook 임포트
from airflow.hooks.base import BaseHook

# --- [1. 상수 설정] ---
BUCKET_NAME = "cali-logs-827913617635" 
MILVUS_HOST = "milvus-standalone.milvus.svc.cluster.local"
MILVUS_PORT = "19530"
COLLECTION_NAME = "cali_rag_collection" # MilvusClient와 동일하게 맞춤
SLACK_WEBHOOK_URL = ""                  # 필요시 Airflow Variable 등으로 관리 추천

SOLUTIONS_PREFIX = 'solutions/'        # 감시할 S3 폴더
PROCESSED_PREFIX = 'processed/'        # 완료 후 이동할 폴더

default_args = {
    'owner': 'cali_admin',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='cali_rag_unified_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,            # 수동 실행 혹은 파일 감지 시 실행
    catchup=False,
    tags=['cali', 'rag', 'milvus', 'openai']
) as dag:

    # --- [태스크 1: S3 파일 감시] ---
    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt', # solutions 폴더의 모든 txt 파일 감시
        wildcard_match=True,                  # 와일드카드 사용 허용
        timeout=60 * 60 * 12,                 # 12시간 동안 대기
        poke_interval=10,                     # 10초마다 체크
        mode='poke'                           # 리소스 점유 상태로 대기 (K8s 사양 충분할 때)
    )

    def process_cali_rag_logic(**context):
        # --- [내부 유틸: 라이브러리 자동 설치] ---
        def install_and_import(package):
            try:
                __import__(package)
            except ImportError:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # 잇몸(직접 설치) 대신 OpenAI와 Milvus 통신 라이브러리 준비
        install_and_import('openai')
        install_and_import('pymilvus')
        
        from openai import OpenAI
        from pymilvus import connections, Collection

        # --- [수정: Airflow Connection에서 API Key 가져오기] ---
        # Airflow UI -> Admin -> Connections에서 Conn ID 'openai_default'의 Password 항목 활용
        try:
            openai_conn = BaseHook.get_connection('openai_default')
            api_key = openai_conn.password 
        except Exception as e:
            raise ValueError(f"Airflow Connection 'openai_default'를 찾을 수 없습니다. UI 설정을 확인하세요: {e}")
        
        # --- [S3 파일 읽기] ---
        s3_hook = S3Hook(aws_conn_id='aws_default')
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            raise ValueError("S3에 처리할 수 있는 txt 파일이 없습니다.")
            
        target_file = txt_files[0]
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME) # 파일 내용 가져오기
        
        # --- [데이터 파싱] ---
        try:
            log_data = json.loads(raw_content) # JSON 형식이면 파싱
        except:
            # 줄글일 경우 MilvusClient 스키마 필드에 맞춰 기본 데이터 구성
            log_data = {
                "service": "manual",
                "message": raw_content[:100],  # 요약용
                "cause": "N/A",
                "action": raw_content          # 전체 내용
            }

        # --- [OpenAI 임베딩 생성] ---
        # Connection에서 가져온 api_key 적용
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "") # 에러 메시지 기준으로 벡터 생성
        )
        vector = response.data[0].embedding

        try:
            # --- [Milvus 연결 및 적재] ---
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            # [중복 제거 로직] MilvusClient의 delete_log_case 반영
            # 동일 서비스의 동일 에러 메시지가 있으면 삭제 후 다시 넣기(Upsert)
            svc = log_data.get("service", "unknown").replace("'", "\\'")
            msg = log_data.get("message", "").replace("'", "\\'")
            delete_expr = f"service == '{svc}' && error_message == '{msg}'"
            collection.delete(delete_expr)
            collection.flush() # 삭제 즉시 반영
            
            # [데이터 삽입] MilvusClient의 insert_log_case 방식 (row 기반)
            row = {
                "vector": vector,                                # OpenAI가 만든 벡터
                "service": log_data.get("service", "unknown")[:64],
                "error_message": log_data.get("message", "")[:1024],
                "cause": log_data.get("cause", "")[:2048],
                "action": log_data.get("action", "")[:2048],
            }
            
            collection.insert([row]) # 행 단위 리스트로 삽입
            collection.flush()       # 저장 즉시 반영
            print(f"🚀 Milvus 적재 완료: {target_file}")
            
        finally:
            connections.disconnect("default") # 연결 해제 (세션 관리)

        # --- [파일 정리] ---
        # 처리가 끝난 파일은 processed/ 폴더로 이동하여 센서 무한 루프 방지
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)

    # --- [태스크 2: 메인 로직 실행] ---
    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    # --- [태스크 3: 슬랙 결과 보고] ---
    def send_report(**context):
        if SLACK_WEBHOOK_URL:
            msg = "✅ [Cali RAG] OpenAI 임베딩 및 지식 베이스 업데이트 완료! (Upsert 적용)"
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": msg}))

    notify_complete = PythonOperator(task_id='notify_complete', python_callable=send_report)

    # 파이프라인 순서: 감시 -> 실행 -> 알림
    wait_for_file >> run_main_logic >> notify_complete