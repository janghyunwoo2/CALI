import os
import re
import json
import requests
import gzip  # [추가] 압축 해제용
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator

# --- [1. 설정] ---
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET') or "cali-logs-827913617635"
LANDING_ZONE = 'raw/'
STATS_ZONE = 'daily_stats/'
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

default_args = {
    'owner': 'cali_admin',
    'start_date': datetime(2026, 1, 28),
    'retries': 1,
}

# --- [2. 에러 분류기] ---
def classify_error_type(content):
    c = content.lower()
    if any(k in c for k in ['db_cache', 'db_issue', 'database']):
        return 'Database'
    elif any(k in c for k in ['infra', 'eks', 'kubernetes']):
        return 'Infra_EKS'
    elif any(k in c for k in ['payment', 'pg']):
        return 'Payment'
    elif any(k in c for k in ['auth', 'security']):
        return 'Auth_Security'
    elif any(k in c for k in ['business', 'logic', 'microservice']):
        return 'BusinessLogic'
    return 'Other_Errors'

# --- [3. 메인 분석 및 슬랙 전송 함수] ---
def daily_analysis_and_slack(**context):
    s3_hook = S3Hook(aws_conn_id='aws_default')
    all_keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=LANDING_ZONE)
    
    if not all_keys:
        print("📢 분석할 로그가 없습니다.")
        return

    clean_keys = [k for k in all_keys if k != LANDING_ZONE and not k.endswith('/')]
    
    category_counts = {
        "Database": 0, "Infra_EKS": 0, "Payment": 0, 
        "Auth_Security": 0, "BusinessLogic": 0
    }
    total_logs = 0
    total_errors = 0
    date_str = datetime.now().strftime('%Y-%m-%d')

    for key in clean_keys:
        # [수정] read_key 대신 직접 바이트를 가져와서 압축 여부 판단
        file_obj = s3_hook.get_key(key, BUCKET_NAME)
        raw_content = file_obj.get()['Body'].read()
        total_logs += 1

        try:
            # Gzip 파일인 경우 해제 시도 (0x1f 0x8b 헤더 확인)
            if raw_content.startswith(b'\x1f\x8b'):
                content = gzip.decompress(raw_content).decode('utf-8')
            else:
                content = raw_content.decode('utf-8')
        except Exception as e:
            print(f"❌ {key} 디코딩 실패: {e}")
            continue
        
        if "ERROR" in content.upper():
            total_errors += 1
            category = classify_error_type(content)
            if category in category_counts:
                category_counts[category] += 1

    # [파일 저장]
    for category, count in category_counts.items():
        summary_data = {"date": date_str, "category": category, "error_count": count}
        target_key = f"{STATS_ZONE}{category}/{date_str}_stats.json"
        
        s3_hook.load_string(
            string_data=json.dumps(summary_data, ensure_ascii=False),
            key=target_key,
            bucket_name=BUCKET_NAME,
            replace=True
        )

    send_daily_slack_report(date_str, total_logs, total_errors, category_counts)

def send_daily_slack_report(date_str, total, errors, counts):
    if not SLACK_WEBHOOK_URL: return

    detail_msg = "\n".join([f"• {cat}: {cnt}건" for cat, cnt in counts.items()])
    
    payload = {
        "text": f"📅 *{date_str} 일일 로그 분석 요약*",
        "attachments": [{
            "color": "#FF0000" if errors > 0 else "#00FF00",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*총 로그 수:* {total}건\n*총 에러 발생:* {errors}건"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*카테고리별 에러 상세:*\n{detail_msg}"}
                }
            ]
        }]
    }
    requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))

# --- [4. DAG 정의] ---
with DAG(
    dag_id='cali_daily_stats_reporter',
    default_args=default_args,
    schedule='@daily', 
    catchup=False,
    tags=['report', 'daily', 'slack']
) as dag:

    run_analysis = PythonOperator(
        task_id='daily_safe_analysis_task',
        python_callable=daily_analysis_and_slack
    )