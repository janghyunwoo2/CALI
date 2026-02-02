import os
import json
import requests
import gzip
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.operators.python import PythonOperator
from airflow.models import Variable

sys.setrecursionlimit(3000)

# --- [1. 설정] ---
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET') or "cali-logs-827913617635"
LANDING_ZONE = 'raw/'
STATS_ZONE = 'daily_stats/'
AWS_REGION = "ap-northeast-2" 

default_args = {
    'owner': 'cali_admin',
    'start_date': datetime(2026, 1, 28),
    'retries': 1,
    'retry_delay': timedelta(seconds=10),
}

# --- [2. 에러 분류기 보강] ---
def classify_error_type(content):
    c = content.lower()
    # 그라파나에서 확인된 키워드들을 더 포괄적으로 추가함
    if any(k in c for k in ['db', 'database', 'sql', 'query', 'cache', 'redis', 'connection_pool']): 
        return 'Database'
    if any(k in c for k in ['infra', 'eks', 'kubernetes', 'node', 'pod', 'cluster', 'ingress']): 
        return 'Infra_EKS'
    if any(k in c for k in ['payment', 'pg', 'toss', 'kakaopay', 'billing', 'order_pay']): 
        return 'Payment'
    if any(k in c for k in ['auth', 'security', 'token', 'jwt', 'login', 'permission', 'forbidden']): 
        return 'Auth_Security'
    if any(k in c for k in ['business', 'logic', 'microservice', 'app', 'service', 'module']): 
        return 'BusinessLogic'
    return 'Other_Errors'

# --- [3. 슬랙 전송 함수 (0건도 표시)] ---
def send_slack_report(date_str, total, errors, counts):
    webhook_url = Variable.get("SLACK_WEBHOOK_URL", default_var=os.getenv('SLACK_WEBHOOK_URL'))
    
    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL 설정 확인 필요")
        return

    # [수정] counts에 없는 카테고리도 0건으로 표시하도록 변경
    all_categories = ["Database", "Infra_EKS", "Payment", "Auth_Security", "BusinessLogic"]
    detail_msg = "\n".join([f"• {cat}: {counts.get(cat, 0)}건" for cat in all_categories])
    
    payload = {
        "text": f"📅 *{date_str} Cali 시스템 분석 리포트 (5-Tier 전수조사)*",
        "attachments": [{
            "color": "#FF0000" if errors > 0 else "#36a64f",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*📊 전체 통계*\n• 분석 파일: {total}개\n• 총 에러 라인: {errors}건"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*🚨 카테고리별 현황 (전체)*\n{detail_msg}"}
                }
            ]
        }]
    }
    
    requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})

# --- [4. 메인 분석 로직] ---
def daily_analysis_and_slack(**context):
    s3_hook = S3Hook(aws_conn_id=None, region_name=AWS_REGION)
    
    all_keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=LANDING_ZONE)
    clean_keys = [k for k in (all_keys or []) if k != LANDING_ZONE and not k.endswith('/')]
    
    # 5개 카테고리 초기화
    category_counts = {
        "Database": 0, "Infra_EKS": 0, "Payment": 0, 
        "Auth_Security": 0, "BusinessLogic": 0
    }
    total_files = 0
    total_errors = 0
    date_str = datetime.now().strftime('%Y-%m-%d')

    for key in clean_keys:
        print(f"🔍 파일 스캔: {key}")
        file_obj = s3_hook.get_key(key, BUCKET_NAME)
        raw_content = file_obj.get()['Body'].read()
        total_files += 1

        try:
            if raw_content.startswith(b'\x1f\x8b'):
                content = gzip.decompress(raw_content).decode('utf-8')
            else:
                content = raw_content.decode('utf-8')
        except:
            continue
        
        # 라인별로 정밀 분석
        lines = content.split('\n')
        for line in lines:
            if "ERROR" in line.upper() or "CRITICAL" in line.upper():
                total_errors += 1
                category = classify_error_type(line)
                # 분류된 결과가 우리 5대 카테고리에 속할 때만 카운트
                if category in category_counts:
                    category_counts[category] += 1

    # 결과 저장 및 슬랙 전송
    send_slack_report(date_str, total_files, total_errors, category_counts)

# --- [5. DAG 정의] ---
with DAG(
    dag_id='cali_daily_stats_reporter_eks',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['eks', 'analysis', 'slack']
) as dag:

    run_analysis = PythonOperator(
        task_id='process_logs_and_report',
        python_callable=daily_analysis_and_slack
    )