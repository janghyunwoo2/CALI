import os
import re
import json
from datetime import datetime
from collections import Counter

from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator

# [Git-sync 최적화 포인트 1] 
# ConfigMap이나 Secret을 통해 들어올 환경 변수가 없을 때를 대비해 기본값(Default)을 설정해주는 게 안전해.
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET', 'cali-log-storage')
LANDING_ZONE = 'raw/'      
VAULT_ZONE = 'vault/'      

default_args = {
    'owner': 'cali_admin',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='cali_daily_management',
    default_args=default_args,
    schedule_interval='@daily', 
    catchup=False,
    tags=['cali', 'daily_report', 'etl', 'gitsync'] # Git-sync로 관리됨을 표시
) as dag:

    def process_logs_and_send_report(**context):
        """
        데이터 분류(ETL)와 데일리 통계 리포팅을 한 번에 수행합니다.
        """
        # AWS 커넥션(aws_default)은 Airflow UI -> Admin -> Connections에서 설정해둬야 해!
        s3_hook = S3Hook(aws_conn_id='aws_default')
        
        # 1. raw/ 폴더 파일 목록 가져오기
        all_keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=LANDING_ZONE)
        
        # [Git-sync 최적화 포인트 2] 폴더 경로 자체(`raw/`)가 리스트에 포함되지 않도록 필터링 강화
        if not all_keys:
            print("📢 처리할 새로운 로그가 없습니다.")
            return

        clean_keys = [k for k in all_keys if k != LANDING_ZONE and not k.endswith('/')]
        
        if not clean_keys:
            print("📢 처리할 진짜 파일이 없습니다.")
            return

        # 통계 집계를 위한 변수
        stats = Counter()
        error_samples = []
        total_count = len(clean_keys)

        # 2. 파일 순회 및 분류 작업
        for key in clean_keys:
            content = s3_hook.read_key(key, BUCKET_NAME)
            
            # 서비스명 추출 ([auth-service] 등)
            service_match = re.search(r'\[(.*?)\]', content)
            service = service_match.group(1) if service_match else "unknown"
            
            # 로그 레벨 파악 (ERROR 여부)
            level = "ERROR" if "ERROR" in content.upper() else "INFO"
            
            # 통계 업데이트
            stats[f"{service} | {level}"] += 1
            if level == "ERROR":
                # 에러 메시지 앞부분 40자만 샘플링
                err_match = re.search(r'ERROR\s+(.*)', content)
                if err_match:
                    error_samples.append(f"[{service}] {err_match.group(1)[:40]}...")

            # S3 경로 이동 (vault/서비스/레벨/날짜/파일명)
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = key.split('/')[-1]
            new_key = f"{VAULT_ZONE}{service}/{level}/{date_str}/{filename}"
            
            # S3는 Move가 없으니 Copy 후 Delete
            s3_hook.copy_object(source_bucket_key=key, dest_bucket_key=new_key,
                                source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME)
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=key)

        # 3. 데일리 슬랙 리포트 메시지 생성
        report_date = datetime.now().strftime('%Y-%m-%d')
        report_msg = (
            f"📅 *CALI 데일리 운영 리포트 ({report_date})*\n"
            f"✅ [Git-sync 배포 버전] 총 {total_count}개의 로그를 분류 완료했습니다.\n\n"
            f"📊 *서비스별 요약:*\n"
        )
        
        for label, count in stats.items():
            report_msg += f"• {label}: {count}건\n"

        if error_samples:
            report_msg += "\n🚨 *주요 에러 내역 (최신 5건):*\n"
            # 중복 제거 후 최대 5개만 노출
            for err in list(dict.fromkeys(error_samples))[:5]:
                report_msg += f"• `{err}`\n"
        else:
            report_msg += "\n✅ 어제는 모든 서비스가 평온했습니다!"

        # 4. 슬랙 전송 (로그 출력 및 나중에 Webhook 연동 가능)
        print(f"🚀 [SLACK REPORT]\n{report_msg}")

    # 태스크 정의
    daily_task = PythonOperator(
        task_id='daily_organize_and_report',
        python_callable=process_logs_and_send_report
    )

    daily_task