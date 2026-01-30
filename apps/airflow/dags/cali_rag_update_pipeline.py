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
# S3 버킷 이름 (실제 리소스 이름과 일치해야 함)
BUCKET_NAME = "cali-logs-827913617635" 
# Milvus 서버 주소 (K8s 내부 DNS 풀네임 사용으로 네임스페이스 간 통신 보장)
MILVUS_HOST = "milvus-standalone.milvus.svc.cluster.local"
MILVUS_PORT = "19530"
# 저장할 Milvus 컬렉션 이름 (기존 MilvusClient와 싱크 맞춤)
COLLECTION_NAME = "cali_rag_collection"
# 알림용 슬랙 웹훅 (현재는 비어있음)
SLACK_WEBHOOK_URL = ""

# S3 내 파일 경로 관리 (감시 폴더 vs 완료 폴더)
SOLUTIONS_PREFIX = 'solutions/'
PROCESSED_PREFIX = 'processed/'

# DAG의 기본 설정 (실패 시 대응 로직)
default_args = {
    'owner': 'cali_admin',
    'retries': 2,                  # 실패하면 딱 2번만 더 해보자 (리트라이)
    'retry_delay': timedelta(seconds=30), # 실패 시 30초 대기 후 바로 재시도 (스피드가 생명)
}

# DAG 정의 (ID, 시작일, 스케줄 등)
with DAG(
    dag_id='cali_rag_unified_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 27),
    schedule_interval=None,         # 수동으로 트리거하거나 센서가 잡을 때만 실행
    catchup=False,                  # 과거 미실행분 무시
    tags=['cali', 'rag', 'milvus', 'openai'] # UI에서 찾기 편하게 태그 달기
) as dag:

    # --- [태스크 1: S3 파일 감시] ---
    # 지정된 버킷의 solutions/ 폴더에 .txt 파일이 들어오는지 감시
    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt', # 와일드카드 매칭으로 모든 txt 감시
        wildcard_match=True,
        timeout=60 * 30,              # 30분 동안 안 오면 "파일 안 왔음" 실패 처리
        poke_interval=30,             # 30초마다 한 번씩 S3 문 두드리기
        mode='reschedule',            # 핵심! 대기 중에는 Worker를 비워줘서 다른 작업 가능하게 함
        exponential_backoff=True      # 계속 없으면 확인 간격을 조금씩 늘려가는 지능형 센서
    )

    # --- [핵심 로직: 데이터 가공 및 Milvus 적재] ---
    def process_cali_rag_logic(**context):
        # 런타임 중에 필요한 라이브러리 자동 설치 유틸리티
        def install_and_import(package):
            try:
                __import__(package)
            except ImportError:
                # 에어플로우 이미지에 없으면 pip로 즉시 설치 (유연성 확보)
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # OpenAI 통신 및 Milvus 핸들링 라이브러리 설치
        install_and_import('openai')
        install_and_import('pymilvus')
        
        from openai import OpenAI
        from pymilvus import connections, Collection

        # Airflow UI에 숨겨둔 OpenAI API 키 안전하게 가져오기
        try:
            api_key = Variable.get("OPENAI_API_KEY")
        except Exception as e:
            raise ValueError(f"Variable 'OPENAI_API_KEY' 누락: {e}")
        
        # S3 조작을 위한 Hook (신분증 역할)
        s3_hook = S3Hook()
        # solutions/ 폴더 내 파일 리스트 확보
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt') and f != SOLUTIONS_PREFIX]
        
        if not txt_files:
            return # 파일 없으면 그냥 종료 (센서 오작동 방지)
            
        target_file = txt_files[0]
        # S3에서 파일 내용 읽어오기
        raw_content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        # 데이터가 JSON이면 파싱, 아니면 텍스트를 적절히 쪼개기
        try:
            log_data = json.loads(raw_content)
        except:
            # 줄글일 경우 Milvus 스키마(service, message, cause, action)에 맞춰 가공
            log_data = {
                "service": "manual",
                "message": raw_content[:100], # 제목처럼 쓸 100자
                "cause": "N/A",
                "action": raw_content         # 전체 내용을 action에 저장
            }

        # OpenAI API 호출: 텍스트를 1536차원 벡터 숫자로 변환
        ai_client = OpenAI(api_key=api_key)
        response = ai_client.embeddings.create(
            model="text-embedding-3-small",
            input=log_data.get("message", "") # 에러 요약본을 벡터로 만듦
        )
        vector = response.data[0].embedding

        try:
            # Milvus 서버 연결
            connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
            collection = Collection(COLLECTION_NAME)
            
            # [중복 제거 단계] 동일 서비스 + 동일 메시지가 있으면 기존 거 삭제
            svc = log_data.get("service", "unknown").replace("'", "\\'")
            msg = log_data.get("message", "").replace("'", "\\'")
            delete_expr = f"service == '{svc}' && error_message == '{msg}'"
            collection.delete(delete_expr)
            collection.flush() # 삭제 완료 확정
            
            # [적재 단계] MilvusClient 스키마에 맞춰 데이터 구성
            row = {
                "vector": vector,                                # 변환된 벡터값
                "service": log_data.get("service", "unknown")[:64],
                "error_message": log_data.get("message", "")[:1024],
                "cause": log_data.get("cause", "")[:2048],
                "action": log_data.get("action", "")[:2048],
            }
            
            collection.insert([row]) # 행 단위 삽입
            collection.flush()       # 저장 완료 확정
            print(f"🚀 Milvus 적재 완료: {target_file}")
            
        finally:
            connections.disconnect("default") # 통신 끝났으면 매너 있게 끊기

        # [마무리 단계] 처리 완료된 파일을 processed/ 폴더로 이동 (S3 정리)
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        s3_hook.copy_object(source_bucket_key=target_file, dest_bucket_key=dest_key, 
                            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file) # 원본 삭제

    # 실제 파이썬 로직 실행 태스크
    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    # 슬랙 알림 전송 (선택 사항)
    def send_report(**context):
        if SLACK_WEBHOOK_URL:
            msg = "✅ [Cali RAG] 업데이트 완료!"
            requests.post(SLACK_WEBHOOK_URL, data=json.dumps({"text": msg}))

    notify_complete = PythonOperator(task_id='notify_complete', python_callable=send_report)

    # 태스크 순서 결정: 감시 -> 로직 실행 -> 알림
    wait_for_file >> run_main_logic >> notify_complete