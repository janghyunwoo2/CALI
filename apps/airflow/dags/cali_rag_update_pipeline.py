import os
import requests
import json
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 

# --- [추가] Milvus 및 임베딩 라이브러리 ---
# 주의: 이 라이브러리들이 Airflow Worker 환경에 설치되어 있어야 함
from pymilvus import connections, Collection, utility
from sentence_transformers import SentenceTransformer

# 1. cali 프로젝트 환경 설정
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET')
SOLUTIONS_PREFIX = 'solutions/'
PROCESSED_PREFIX = 'processed/'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

# --- [추가] Milvus 설정 ---
MILVUS_HOST = os.getenv('MILVUS_HOST', 'milvus-standalone') # EKS 내부 서비스 도메인
MILVUS_PORT = '19530'
COLLECTION_NAME = 'cali_rag_collection' # 미리 생성해둔 컬렉션 이름

# 2. 모든 태스크에 적용할 공통 옵션
default_args = {
    'owner': 'cali_admin',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 3. cali 프로젝트 공장(DAG) 설계도 시작
with DAG(
    dag_id='cali_rag_unified_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,
    catchup=False,
    tags=['cali', 'rag', 'milvus']
) as dag:

    # --- [Step 1] S3 센서 (생략) ---
    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt',
        wildcard_match=True,
        timeout=60 * 60 * 12,
        poke_interval=10,
        mode='poke'
    )

    # --- [Step 2] 통합 비즈니스 로직 (수정됨) ---
    def process_cali_rag_logic(**context):
        s3_hook = S3Hook(aws_conn_id='aws_default')
        
        # [S3 조회]
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            raise ValueError("S3에 처리할 파일이 없습니다.")
            
        target_file = txt_files[0]
        content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        # [품질 검증]
        if len(content.strip()) < 20:
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
            raise ValueError(f"❌ 내용 부실 데이터 삭제 완료: {target_file}")

        # --- [신규 추가] Milvus 적재 로직 ---
        try:
            # 1. Milvus 연결
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            
            # 2. 임베딩 모델 로드 (한국어 성능 위주 모델)
            # Worker 메모리 상황에 따라 모델명 조절 가능
            model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-aug')
            vector = model.encode(content).tolist()
            
            # 3. 컬렉션 로드
            collection = Collection(COLLECTION_NAME)
            
            # 4. 데이터 삽입 (스키마 구조: id, vector, raw_text)
            # id를 자동생성(auto_id)으로 설정했다면 vector와 text만 넣으면 됨
            data = [
                [vector],
                [content]
            ]
            collection.insert(data)
            collection.flush() # 즉시 반영
            print(f"🚀 Milvus 적재 완료: {target_file} (Vector Dim: {len(vector)})")
            
        except Exception as e:
            print(f"❌ Milvus 적재 실패: {str(e)}")
            raise e
        finally:
            connections.disconnect("default")

        # [파일 정리]
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(
            source_bucket_key=target_file, dest_bucket_key=dest_key,
            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME
        )
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
        print(f"📦 이동 완료: {target_file} -> {dest_key}")

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    # --- [Step 3] Slack 보고 ---
    def send_report(**context):
        msg = "✅ [cali 프로젝트] RAG 지식 베이스 업데이트 성공! 🚀"
        print(f"Slack Notification: {msg}")
        if SLACK_WEBHOOK_URL:
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": msg}))

    notify_complete = PythonOperator(
        task_id='notify_complete',
        python_callable=send_report
    )

    wait_for_file >> run_main_logic >> notify_complete