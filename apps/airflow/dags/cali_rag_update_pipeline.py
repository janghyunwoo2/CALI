import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 에어플로우 기본 모듈
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 
from airflow.models import Variable

# 설정 로드
load_dotenv()

# --- [1. 상수 및 설정] ---
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET') or "cali-logs-827913617635"
COLLECTION_NAME = "cali_logs"
MILVUS_HOST = os.getenv('MILVUS_HOST') or "host.docker.internal"

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
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

    s3_hook = S3Hook()
    
    # 1. S3 파일 목록 가져오기
    all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix='solutions/')
    target_files = [f for f in all_files if f.endswith('.txt') and f != 'solutions/']
    
    if not target_files:
        print("💡 처리할 파일이 없습니다.")
        return

    # 2. Milvus 연결 및 컬렉션 체크/생성
    connections.connect("default", host=MILVUS_HOST, port="19530")
    
    try:
        if not utility.has_collection(COLLECTION_NAME):
            print(f"✨ {COLLECTION_NAME} 컬렉션이 없어 새로 생성합니다.")
            fields = [
                FieldSchema(name="pk", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=1536), # text-embedding-3-small
                FieldSchema(name="service", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="error_message", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="action", dtype=DataType.VARCHAR, max_length=100)
            ]
            schema = CollectionSchema(fields, "Cali RAG Error Logs Schema")
            col = Collection(COLLECTION_NAME, schema)
            
            index_params = {
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            col.create_index(field_name="vector", index_params=index_params)
            print("✅ 인덱스 생성 완료")
        else:
            col = Collection(COLLECTION_NAME)
        
        col.load()
        ai_client = OpenAI(api_key=api_key)

        for target_file in target_files:
            print(f"📂 파일 처리 시작: {target_file}")
            content = s3_hook.read_key(target_file, BUCKET_NAME)
            
            if len(content.strip()) < 20:
                print(f"⚠️ {target_file}: 내용이 너무 짧아 스킵합니다.")
                continue

            # 임베딩 생성
            response = ai_client.embeddings.create(
                model="text-embedding-3-small", 
                input=[content.replace("\n", " ")]
            )
            vector = response.data[0].embedding

            # 3. Milvus 적재
            data = [
                [vector],
                ["cali_service"],
                [content[:1024]],
                ["rag_updated"]
            ]
            col.insert(data)
            print(f"🚀 {target_file} Milvus 적재 성공")

            # 4. 파일 이동
            dest_key = target_file.replace('solutions/', 'processed/')
            s3_hook.copy_object(
                source_bucket_key=target_file, 
                dest_bucket_key=dest_key, 
                source_bucket_name=BUCKET_NAME, 
                dest_bucket_name=BUCKET_NAME
            )
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
            print(f"✅ {target_file} -> {dest_key} 이동 완료")

    finally:
        connections.disconnect("default")

# --- [2-2. 데이터 검증 함수] ---
def verify_milvus_data(**context):
    try:
        from pymilvus import connections, Collection
    except ImportError:
        raise
    
    connections.connect("default", host=MILVUS_HOST, port="19530")
    try:
        col = Collection(COLLECTION_NAME)
        col.load()
        
        count = col.num_entities
        print(f"📊 현재 컬렉션 내 총 데이터 개수: {count}")
        
        results = col.query(
            expr="pk > 0",
            output_fields=["pk", "service", "error_message", "action"],
            limit=10
        )
        
        print("🔍 --- [적재 데이터 샘플 확인] ---")
        for i, res in enumerate(results):
            print(f"[{i+1}] PK: {res['pk']} | Action: {res['action']}")
            print(f"    Msg: {res['error_message'][:100]}...")
        print("------------------------------------------")
        
    finally:
        connections.disconnect("default")

# --- [3. 에어플로우 DAG 정의] ---
with DAG(
    dag_id='cali_rag_update_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,
    catchup=False,
    tags=['cali', 'rag', 'milvus']
) as dag:

    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key='solutions/*.txt',
        wildcard_match=True,
        mode='reschedule',
        poke_interval=60,
        timeout=60 * 60
    )

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic,
        provide_context=True
    )

    verify_data = PythonOperator(
        task_id='verify_milvus_data',
        python_callable=verify_milvus_data,
        provide_context=True
    )

    wait_for_file >> run_main_logic >> verify_data