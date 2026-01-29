import os
import requests
import json
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor 
from airflow.providers.amazon.aws.hooks.s3 import S3Hook 
from airflow.operators.python import PythonOperator 

BUCKET_NAME = "cali-logs-827913617635"       # 네 실제 S3 버킷 이름으로 수정
MILVUS_HOST = "milvus-standalone"     # Milvus 서비스 주소
MILVUS_PORT = "19530"
COLLECTION_NAME = "cali_rag_collection"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..." # 슬랙 주소 직접 입력

SOLUTIONS_PREFIX = 'solutions/'
PROCESSED_PREFIX = 'processed/'
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

    # 1. S3 센서: 하드코딩된 BUCKET_NAME을 사용하여 에러 방지
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
        # [중요] 라이브러리 부재 시 스케줄러가 죽는 것을 방지
        from pymilvus import connections, Collection
        from sentence_transformers import SentenceTransformer
        
        s3_hook = S3Hook(aws_conn_id='aws_default')
        
        # 파일 리스트 조회
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            raise ValueError("S3에 처리할 파일이 없습니다.")
            
        target_file = txt_files[0]
        content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        # 데이터 품질 검증
        if len(content.strip()) < 20:
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
            print(f"⚠️ 내용 부실로 삭제 완료: {target_file}")
            return

        try:
            # Milvus 연결 및 임베딩
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            model = SentenceTransformer('snunlp/KR-SBERT-V40K-klueNLI-aug')
            vector = model.encode(content).tolist()
            
            collection = Collection(COLLECTION_NAME)
            collection.load() # 검색을 위해 메모리 로드

            # 유사도 검색 (중복 방지)
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
                if hit.distance < SIMILARITY_THRESHOLD:
                    is_duplicate = True
                    print(f"⚠️ 중복 감지 (Distance: {hit.distance:.4f})")

            # 중복이 아닐 때만 적재
            if not is_duplicate:
                # 스키마에 따라 [vector], [content] 순서 확인 필요
                data = [[vector], [content]]
                collection.insert(data)
                collection.flush()
                print(f"🚀 Milvus 적재 성공: {target_file}")
            else:
                print(f"⏭ 중복 데이터 적재 스킵: {target_file}")
            
        except Exception as e:
            print(f"❌ Milvus 작업 중 오류: {str(e)}")
            raise e
        finally:
            connections.disconnect("default")

        # 파일 정리 (이동)
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(
            source_bucket_key=target_file, dest_bucket_key=dest_key,
            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME
        )
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
        print(f"📦 정리 완료: {target_file} -> {dest_key}")

    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    def send_report(**context):
        if SLACK_WEBHOOK_URL and "https" in SLACK_WEBHOOK_URL:
            msg = "✅ [Cali RAG] 지식 베이스 업데이트 완료! (중복 체크 포함) 🚀"
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": msg}))

    notify_complete = PythonOperator(
        task_id='notify_complete',
        python_callable=send_report
    )

    wait_for_file >> run_main_logic >> notify_complete