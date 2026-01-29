import os
import requests
import json
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 

# 1. 환경 설정
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET')
SOLUTIONS_PREFIX = 'solutions/'
PROCESSED_PREFIX = 'processed/'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

MILVUS_HOST = os.getenv('MILVUS_HOST', 'milvus-standalone')
MILVUS_PORT = '19530'
COLLECTION_NAME = 'cali_rag_collection'
SIMILARITY_THRESHOLD = 0.1  # L2 거리 기준 (0에 가까울수록 똑같음)

default_args = {
    'owner': 'cali_admin',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='cali_rag_unified_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,
    catchup=False,
    tags=['cali', 'rag', 'milvus']
) as dag:

    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt',
        wildcard_match=True,
        timeout=60 * 60 * 12,
        poke_interval=10,
        mode='poke'
    )

    def process_cali_rag_logic(**context):
        # --- [중요] 라이브러리가 없을 때 스케줄러가 죽는 것을 방지하기 위해 함수 내부에서 import ---
        from pymilvus import connections, Collection, utility
        from sentence_transformers import SentenceTransformer
        
        s3_hook = S3Hook(aws_conn_id='aws_default')
        
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            raise ValueError("S3에 처리할 파일이 없습니다.")
            
        target_file = txt_files[0]
        content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        if len(content.strip()) < 20:
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
            raise ValueError(f"❌ 내용 부실 데이터 삭제 완료: {target_file}")

        try:
            # 1. Milvus 연결 및 모델 로드
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-aug')
            vector = model.encode(content).tolist()
            
            collection = Collection(COLLECTION_NAME)
            collection.load() # 검색을 위해 메모리 로드

            # 2. [추가] 유사도 검색을 통한 중복 체크
            search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            results = collection.search(
                data=[vector], 
                anns_field="vector", 
                param=search_params, 
                limit=1,
                output_fields=["raw_text"]
            )

            is_duplicate = False
            if results and len(results[0]) > 0:
                hit = results[0][0]
                # L2 거리가 너무 가까우면 중복으로 간주
                if hit.distance < SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    print(f"⚠️ 중복 감지: 이미 존재하는 지식입니다. (Distance: {hit.distance})")

            # 3. 중복이 아닐 때만 적재
            if not is_duplicate:
                data = [[vector], [content]]
                collection.insert(data)
                collection.flush()
                print(f"🚀 Milvus 적재 성공: {target_file}")
            else:
                print(f"⏭ 중복 데이터라 적재를 건너뜁니다.")
            
        except Exception as e:
            print(f"❌ 작업 중 오류 발생: {str(e)}")
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

    def send_report(**context):
        msg = "✅ [cali 프로젝트] RAG 지식 베이스 업데이트 완료! (중복 체크 포함) 🚀"
        if SLACK_WEBHOOK_URL:
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": msg}))

    notify_complete = PythonOperator(
        task_id='notify_complete',
        python_callable=send_report
    )

    wait_for_file >> run_main_logic >> notify_complete