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

# EKS 환경에서 Boto3의 내부 호출 루프를 방지하기 위해 재귀 제한을 늘림
sys.setrecursionlimit(3000)

# --- [1. 설정] ---
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET') or "cali-logs-827913617635"
LANDING_ZONE = 'raw/'
STATS_ZONE = 'daily_stats/'
# [추가] 리전 명시는 EKS 환경에서 엔드포인트 탐색 루프를 막는 핵심이야!
AWS_REGION = "ap-northeast-2" 

default_args = {
    'owner': 'cali_admin',
    'start_date': datetime(2026, 1, 28),
    'retries': 1,
    'retry_delay': timedelta(seconds=10),
}

# --- [2. 에러 분류기] ---
def classify_error_type(content):
    c = content.lower()
    if any(k in c for k in ['db_cache', 'db_issue', 'database']): return 'Database'
    if any(k in c for k in ['infra', 'eks', 'kubernetes']): return 'Infra_EKS'
    if any(k in c for k in ['payment', 'pg']): return 'Payment'
    if any(k in c for k in ['auth', 'security']): return 'Auth_Security'
    if any(k in c for k in ['business', 'logic', 'microservice']): return 'BusinessLogic'
    return 'Other_Errors'

# --- [3. 슬랙 전송 함수 (EKS 안정화 버전)] ---
def send_slack_report(date_str, total, errors, counts):
    # EKS에서는 전역 변수보다 함수 실행 시점에 직접 가져오는 게 제일 확실해
    webhook_url = Variable.get("SLACK_WEBHOOK_URL", default_var=os.getenv('SLACK_WEBHOOK_URL'))
    
    if not webhook_url:
        print("⚠️ SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
        return

    detail_msg = "\n".join([f"• {cat}: {cnt}건" for cat, cnt in counts.items() if cnt > 0])
    if not detail_msg: detail_msg = "• 탐지된 특이 에러 없음"
    
    payload = {
        "text": f"📅 *{date_str} Cali 시스템 로그 분석 리포트 (EKS)*",
        "attachments": [{
            "color": "#FF0000" if errors > 0 else "#36a64f",
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*📊 전체 통계*\n• 총 로그: {total}건\n• 에러 탐지: {errors}건"}
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*🚨 카테고리별 상세*\n{detail_msg}"}
                }
            ]
        }]
    }
    
    try:
        response = requests.post(webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
        if response.status_code == 200:
            print("✅ 슬랙 리포트 전송 성공!")
        else:
            print(f"❌ 슬랙 전송 실패: {response.status_code}")
    except Exception as e:
        print(f"❌ 슬랙 예외 발생: {e}")

# --- [4. 메인 분석 로직] ---
def daily_analysis_and_slack(**context):
    # [핵심 수정] aws_conn_id=None 설정으로 포드의 IAM Role을 직접 사용하게 함
    s3_hook = S3Hook(aws_conn_id=None, region_name=AWS_REGION)
    
    all_keys = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=LANDING_ZONE)
    if not all_keys:
        print("📢 분석할 로그가 S3에 없습니다.")
        return

    clean_keys = [k for k in all_keys if k != LANDING_ZONE and not k.endswith('/')]
    
    category_counts = {
        "Database": 0, "Infra_EKS": 0, "Payment": 0, 
        "Auth_Security": 0, "BusinessLogic": 0, "Other_Errors": 0
    }
    total_logs = 0
    total_errors = 0
    date_str = datetime.now().strftime('%Y-%m-%d')

    for key in clean_keys:
        # EKS 내부에서는 get_key 호출 시 리소스 최적화를 위해 직접 바이트를 긁어옴
        file_obj = s3_hook.get_key(key, BUCKET_NAME)
        raw_content = file_obj.get()['Body'].read()
        total_logs += 1

        try:
            if raw_content.startswith(b'\x1f\x8b'):
                content = gzip.decompress(raw_content).decode('utf-8')
            else:
                content = raw_content.decode('utf-8')
        except Exception as e:
            print(f"❌ {key} 파싱 실패: {e}")
            continue
        
        if "ERROR" in content.upper():
            total_errors += 1
            category = classify_error_type(content)
            category_counts[category] += 1

    # 결과 저장 (S3)
    for category, count in category_counts.items():
        if count == 0: continue
        summary_data = {"date": date_str, "category": category, "error_count": count}
        s3_hook.load_string(
            string_data=json.dumps(summary_data, ensure_ascii=False),
            key=f"{STATS_ZONE}{category}/{date_str}_stats.json",
            bucket_name=BUCKET_NAME,
            replace=True
        )

    send_slack_report(date_str, total_logs, total_errors, category_counts)

# --- [5. DAG 정의] ---
with DAG(
    dag_id='cali_daily_stats_reporter_eks',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    tags=['eks', 'analysis', 'slack']
) as dag:

    run_analysis = PythonOperator(
        task_id='process_logs_and_report',
        python_callable=daily_analysis_and_slack
    )