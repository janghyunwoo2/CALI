import os
import re
from datetime import datetime
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator

# [Git-sync 최적화 포인트 1] 
# Git-sync는 코드를 특정 경로(/dags/...)에 뿌려주기 때문에 
# 버킷명 같은 설정값은 OS 환경 변수에서 가져오되, 없을 경우를 대비한 기본값을 주는 게 좋아.
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET', 'cali-log-bucket') 
LANDING_ZONE = 'raw/'      
VAULT_ZONE = 'vault/'      

default_args = {
    'owner': 'cali_admin',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='cali_daily_organizer',
    default_args=default_args,
    schedule_interval='@daily', 
    catchup=False,
    tags=['cali', 'etl', 'classification', 'gitsync'] # Git-sync 관리 표시 추가
) as dag:

    def organize_logs_to_vault(**context):
        s3_hook = S3Hook(aws_conn_id='aws_default')
        
        # [Git-sync 최적화 포인트 2] 
        # 파일 목록을 가져올 때 폴더 경로 자체(`raw/`)가 리스트에 포함되어 에러가 나는 경우가 많아.
        # 이를 방지하기 위해 필터링을 더 꼼꼼하게 했어.
        all_keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=LANDING_ZONE)
        
        if not all_keys:
            print("📢 현재 처리할 로그 파일이 없습니다.")
            return

        clean_keys = [k for k in all_keys if k != LANDING_ZONE and not k.endswith('/')]
        
        if not clean_keys:
            print("📢 처리할 진짜 파일이 없습니다.")
            return

        for key in clean_keys:
            content = s3_hook.read_key(key, BUCKET_NAME)
            
            # 서비스명 추출
            service_match = re.search(r'\[(.*?)\]', content)
            service_name = service_match.group(1) if service_match else "unknown_service"
            
            # 로그 레벨 파악
            log_level = "ERROR" if "ERROR" in content.upper() else "INFO"
            
            # 날짜 파티셔닝
            date_partition = datetime.now().strftime('%Y-%m-%d')
            
            # 신규 경로 생성
            filename = key.split('/')[-1]
            new_key = f"{VAULT_ZONE}{service_name}/{log_level}/{date_partition}/{filename}"
            
            # S3 이동 (Copy & Delete)
            # Git-sync 환경에서도 S3 Hook은 동일하게 작동해!
            s3_hook.copy_object(
                source_bucket_key=key, 
                dest_bucket_key=new_key,
                source_bucket_name=BUCKET_NAME, 
                dest_bucket_name=BUCKET_NAME
            )
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=key)
            
            print(f"✅ [Git-sync Deploy] 이동 완료: {key} -> {new_key}")

    organize_task = PythonOperator(
        task_id='classify_and_move_logs',
        python_callable=organize_logs_to_vault
    )

    organize_task