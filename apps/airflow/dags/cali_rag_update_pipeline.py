import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 
from airflow.models import Variable

# EKS 환경 재귀 에러 방어
sys.setrecursionlimit(3000)

# --- [1. 상수 및 설정] ---
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET') or "cali-logs-827913617635"
COLLECTION_NAME = "cali_logs_test"
MILVUS_HOST = os.getenv('MILVUS_HOST') or "milvus.milvus.svc.cluster.local"
AWS_REGION = "ap-northeast-2" 

default_args = {
    'owner': 'cali_admin',
    'retries': 1,
    'retry_delay': timedelta(seconds=30),
}

# --- [2. 메인 비즈니스 로직 함수] ---
def process_cali_rag_logic(**context):
    try:
        from openai import OpenAI
        from pymilvus import connections, Collection, utility, FieldSchema, CollectionSchema, DataType
    except ImportError as e:
        print(f"❌ 라이브러리 인식 실패: {e}")
        raise 

    api_key = os.getenv('OPENAI_API_KEY') or Variable.get("OPENAI_API_KEY", default_var=None)
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 없습니다.")

    # S3Hook은 region_name을 직접 받을 수 있음
    s3_hook = S3Hook(aws_conn_id=None, region_name=AWS_REGION) 
    
    all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix='solutions/')
    target_files = [f for f in (all_files or []) if f.endswith('.txt') and f != 'solutions/']
    
    if not target_files:
        print("💡 처리할 파일이 없습니다.")
        return

    print(f"📡 Milvus 연결 시도: {MILVUS_HOST}")
    connections.connect("default", host=MILVUS_HOST, port="19530")
    
    try:
        if not utility.has_collection(COLLECTION_NAME):
            fields = [
                FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536), 
                FieldSchema(name="service", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="error_message", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="action", dtype=DataType.VARCHAR, max_length=100)
            ]
            schema = CollectionSchema(fields, "Cali RAG Knowledge Base")
            col = Collection(COLLECTION_NAME, schema)
            col.create_index("vector", {"metric_type": "L2", "index_type": "IVF_FLAT", "params": {"nlist": 128}})
        else:
            col = Collection(COLLECTION_NAME)
        
        col.load()
        ai_client = OpenAI(api_key=api_key)

        for target_file in target_files:
            print(f"📂 파일 분석 중: {target_file}")
            content = s3_hook.read_key(target_file, BUCKET_NAME)
            
            if len(content.strip()) < 10: continue

            response = ai_client.embeddings.create(
                model="text-embedding-3-small", 
                input=[content.replace("\n", " ")]
            )
            vector = response.data[0].embedding

            col.insert([[vector], ["cali_knowledge"], [content[:1024]], ["updated"]])
            col.flush()

            # [파일 이동 로직]
            dest_key = target_file.replace('solutions/', 'processed/')
            s3_hook.copy_object(
                source_bucket_key=target_file, 
                dest_bucket_key=dest_key, 
                source_bucket_name=BUCKET_NAME, 
                dest_bucket_name=BUCKET_NAME
            )
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
            print(f"✅ 처리 완료 및 이동: {target_file} -> {dest_key}")

    finally:
        connections.disconnect("default")

# --- [3. 에어플로우 DAG 정의] ---
with DAG(
    dag_id='cali_rag_update_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,
    catchup=False,
    tags=['cali', 'rag', 'eks', 'milvus']
) as dag:

    # 🌟 [에러 수정 핵심 포인트] 
    # S3KeySensor는 region_name을 직접 받지 않고 hook_params에 넣어야 함
    wait_for_file = S3KeySensor(
        task_id='wait_for_solution_file',
        bucket_name=BUCKET_NAME,
        bucket_key='solutions/*.txt',
        wildcard_match=True,
        mode='reschedule',
        poke_interval=30,
        timeout=600,
        aws_conn_id=None,
        verify=False,
        hook_params={
            "region_name": AWS_REGION  # <-- 요렇게 주머니에 담아줘야 함!
        }
    )

    run_main_logic = PythonOperator(
        task_id='run_cali_rag_ingestion',
        python_callable=process_cali_rag_logic
    )

    wait_for_file >> run_main_logic