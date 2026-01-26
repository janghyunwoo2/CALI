import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
# Slack 알림이나 Milvus 라이브러리는 필요시 임포트

# 환경 변수 가져오기 (우리가 .env에 설정한 것들)
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET')
SOLUTIONS_PREFIX = 'solutions/'

default_args = {
    'owner': 'cali',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='cali_rag_update_pipeline',
    default_args=default_args,
    start_date=datetime(2026, 1, 26),
    schedule_interval=None, # 파일이 올 때만 돌거나 센서가 감지
    catchup=False,
    tags=['cali', 'rag', 'ge']
) as dag:

    # 1. S3에 해결방안 파일이 올라오는지 감시 (3번 단계)
    wait_for_solution = S3KeySensor(
        task_id='wait_for_solution_file',
        bucket_name=BUCKET_NAME,
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt', # solutions 폴더의 txt 파일 감시
        wildcard_match=True,
        timeout=60 * 60 * 24, # 24시간 동안 대기
        poke_interval=60      # 1분마다 체크
    )

    # 2. 파일 내용을 읽고 품질 검증 (4번 단계 - 네 메인 작업)
    def validate_and_process(**context):
        s3_hook = S3Hook(aws_conn_id='aws_default')
        # 센서가 찾아낸 파일 리스트 가져오기
        file_key = context['task_instance'].xcom_pull(task_ids='wait_for_solution_file')[0]
        content = s3_hook.read_key(file_key, BUCKET_NAME)
        
        print(f"검증 시작: {file_key}")
        
        # --- [GE 로직 들어갈 자리] ---
        # 예: 텍스트가 20자 미만이면 퇴짜 놓기
        if len(content.strip()) < 20:
            raise ValueError("해결 방안 내용이 너무 부실합니다! 다시 작성해주세요.")
        
        # 검증 통과한 데이터를 다음 태스크로 전달
        context['ti'].xcom_push(key='solution_text', value=content)
        context['ti'].xcom_push(key='file_name', value=file_key)

    validate_task = PythonOperator(
        task_id='validate_solution_quality',
        python_callable=validate_and_process
    )

    # 3. RAG 업데이트 (5번 단계 - 연결 작업)
    def update_milvus(**context):
        solution_text = context['ti'].xcom_pull(key='solution_text')
        
        # TODO: RAG 담당자가 줄 임베딩 함수 호출
        # vector = rag_dev_module.get_embedding(solution_text)
        
        # TODO: Milvus Hook이나 Client로 insert
        # milvus_hook.insert(collection='error_solutions', vector=vector, payload={'text': solution_text})
        
        print("Milvus 적재 완료!")

    update_rag_task = PythonOperator(
        task_id='update_milvus_knowledge',
        python_callable=update_milvus
    )

    # 4. 완료 알림 (6번 단계)
    # (SlackWebhookOperator를 쓰면 더 좋음)
    notify_success = PythonOperator(
        task_id='notify_update_complete',
        python_callable=lambda: print("Slack 알림: 지식 베이스 업데이트 완료! 🚀")
    )

    # 순서 연결
    wait_for_solution >> validate_task >> update_rag_task >> notify_success