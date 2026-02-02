import os
import json
import requests
import gzip
import sys
import re
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

# --- [2. 에러 분류기 (제너레이터 SVC 이름 기준)] ---
def classify_error_by_svc(line):
    # 제너레이터 포맷: [LEVEL] TS svc/ver [TID]: MSG
    # 정규식으로 서비스 이름만 추출 (예: payment-gateway)
    match = re.search(r'\]\s\d{4}-\d{2}-\d{2}T\S+\s([^/]+)/', line)
    if not match:
        return 'Other_Errors'
    
    svc_name = match.group(1).lower()
    
    if 'db-cache' in svc_name: return 'Database'
    if 'infra-eks' in svc_name: return 'Infra_EKS'
    if 'payment' in svc_name: return 'Payment'
    if 'auth-security' in svc_name: return 'Auth_Security'
    if 'biz-logic' in svc_name: return 'BusinessLogic'
    
    return 'Other_Errors'

# --- [3. 슬랙 전송 함수 (정합성 100% 버전)] ---
def send_slack_report(date_str, total_files, total_errors, counts):
    webhook_url = Variable.get("SLACK_WEBHOOK_URL", default_var=os.getenv('SLACK_WEBHOOK_URL'))
    if not webhook_url: return

    all_categories = ["Database", "Infra_EKS", "Payment", "Auth_Security", "BusinessLogic", "Other_Errors"]
    
    # 카테고리별 메시지 생성
    detail_msg = "\n".join([f"• {cat}: {counts.get(cat, 0):,}건" for cat in all_categories])
    
    # 분류된 에러 합계 계산 (검증용)
    classified_sum = sum(counts.values())
    
    payload = {
        "text": f"📅 *{date_str} Cali 시스템 분석 리포트*",
        "attachments": [{
            "color": "#FF0000" if total_errors > 0 else "#36a64f",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*📊 전체 통계*\n• 분석 파일: {total_files:,}개\n• 총 에러 라인: {total_errors:,}건 (분류율: {(classified_sum/total_errors)*100:.1f}%)"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*🚨 5-Tier 분석 현황*\n{detail_msg}"}
                }
            ]
        }]
    }
    requests.post(webhook_url, json=payload)

# --- [4. 메인 분석 로직] ---
def daily_analysis_and_slack(**context):
    s3_hook = S3Hook(aws_conn_id=None, region_name=AWS_REGION)
    all_keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=LANDING_ZONE)
    clean_keys = [k for k in (all_keys or []) if k != LANDING_ZONE and not k.endswith('/')]
    
    counts = {cat: 0 for cat in ["Database", "Infra_EKS", "Payment", "Auth_Security", "BusinessLogic", "Other_Errors"]}
    total_files = 0
    total_errors = 0
    date_str = datetime.now().strftime('%Y-%m-%d')

    for key in clean_keys:
        raw_content = s3_hook.get_key(key, BUCKET_NAME).get()['Body'].read()
        total_files += 1
        try:
            content = gzip.decompress(raw_content).decode('utf-8') if raw_content.startswith(b'\x1f\x8b') else raw_content.decode('utf-8')
        except: continue
        
        for line in content.split('\n'):
            if not line.strip(): continue
            # ERROR, CRITICAL, WARN 모두 에러로 집계 (제너레이터 특성 반영)
            if any(lvl in line.upper() for lvl in ["ERROR", "CRITICAL", "WARN"]):
                total_errors += 1
                category = classify_error_by_svc(line)
                counts[category] += 1

    send_slack_report(date_str, total_files, total_errors, counts)

# --- [5. DAG 정의] ---
with DAG(
    dag_id='cali_daily_stats_reporter_eks',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
    tags=['eks', 'analysis', 'slack']
) as dag:
    
    PythonOperator(task_id='process_logs_and_report', python_callable=daily_analysis_and_slack)