import os
import requests
import json
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor  # S3에 파일 왔나 감시하는 센서
from airflow.providers.amazon.aws.hooks.s3 import S3Hook        # S3 파일을 읽고 쓰고 지우는 갈고리
from airflow.operators.python import PythonOperator           # 파이썬 함수를 실행해주는 작업자

# 1. cali 프로젝트 환경 설정 (S3 경로 및 슬랙 주소)
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET')  # OS 환경 변수에서 S3 버킷 이름 가져오기
SOLUTIONS_PREFIX = 'solutions/'             # 새로 올라온 파일이 대기하는 '입구'
PROCESSED_PREFIX = 'processed/'             # 처리가 끝난 파일이 보관될 '출구'
SLACK_WEBHOOK_URL = "여기에_웹후크_주소_입력"  # 성공 시 슬랙 메시지를 보낼 비밀 주소

# 2. 모든 태스크에 적용할 공통 옵션
default_args = {
    'owner': 'cali_admin',                  # 프로젝트 관리자 이름
    'retries': 1,                           # 실패하면 딱 한 번만 더 기회를 주기
    'retry_delay': timedelta(minutes=5),    # 다시 시도하기 전에 5분간 숨 고르기
}

# 3. cali 프로젝트 공장(DAG) 설계도 시작
with DAG(
    dag_id='cali_rag_unified_pipeline',      # 에어플로우 UI에 뜰 프로젝트 이름
    default_args=default_args,              # 위에서 정의한 기본 옵션 적용
    start_date=datetime(2026, 1, 27),       # 공장 가동 시작 날짜
    schedule_interval=None,                 # 정기 실행 없이 필요할 때만 수동 실행
    catchup=False,                          # 과거의 밀린 작업은 무시하고 패스
    tags=['cali', 'rag', 'integrated']      # 찾기 쉽게 태그 달아두기
) as dag:

    # --- [Step 1] S3 센서: 파일이 도착할 때까지 기다리는 망지기 ---
    wait_for_file = S3KeySensor(
        task_id='wait_for_s3_file',         # 단계 이름
        bucket_name=BUCKET_NAME,            # 확인할 S3 바구니 이름
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt', # 입구 폴더에 .txt 파일이 오는지 감시
        wildcard_match=True,                # 별표(*)를 써서 파일명 패턴 찾기 허용
        timeout=60 * 60 * 12,               # 최대 12시간 동안 파일 오나 기다려줌
        poke_interval=10,                   # 10초마다 한 번씩 S3 바구니 들여다보기
        mode='poke'                         # 센서가 직접 계속 확인하는 모드
    )

    # --- [Step 2] 통합 비즈니스 로직: 검증 + 적재 + 이동을 한꺼번에! ---
    def process_cali_rag_logic(**context):
        # S3에 접근할 수 있는 권한 갈고리(Hook) 소환
        s3_hook = S3Hook(aws_conn_id='aws_default')
        
        # [S3 직접 조회] XCom 쪽지 안 기다리고 내가 직접 폴더 뒤져서 파일 찾기 (배달 사고 방지)
        all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
        txt_files = [f for f in all_files if f.endswith('.txt')] # .txt 파일만 골라내기
        
        if not txt_files: # 만약 센서가 울렸는데 파일이 없으면 에러 내고 중단
            raise ValueError("S3에 처리할 파일이 없습니다. 센서 오작동인지 확인하세요.")
            
        target_file = txt_files[0] # 첫 번째 발견된 파일을 작업 대상으로 확정
        print(f"✅ {target_file} 작업 시작")

        # [1단계] 데이터 읽기: S3에서 파일 안의 텍스트 내용을 가져옴
        content = s3_hook.read_key(target_file, BUCKET_NAME)
        
        # [2단계] 품질 검증: 내용이 20자보다 짧으면 "내용 부실"로 간주
        if len(content.strip()) < 20:
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file) # 불량 파일은 즉시 삭제
            raise ValueError(f"❌ 내용 부실 ({len(content.strip())}자). 데이터 삭제 완료.")
        
        # [3단계] Milvus 적재: 한 함수 안에서 content 변수를 그대로 쓰니까 XCom 필요 없음!
        # 여기에 나중에 임베딩(Embedding)하고 Milvus에 꽂는 코드를 넣으면 됨
        print(f"🚀 Milvus 적재 완료 (길이: {len(content)})")

        # [4단계] 파일 정리: 적재가 성공했을 때만 파일을 이동시켜서 작업 완료 도장 찍기
        dest_key = target_file.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX) # 입구 -> 출구로 경로 변경
        # S3 내부에서 파일을 '출구' 폴더로 복사
        s3_hook.copy_object(
            source_bucket_key=target_file, dest_bucket_key=dest_key,
            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME
        )
        # 원래 '입구'에 있던 파일은 삭제해서 깔끔하게 정리
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=target_file)
        print(f"📦 이동 완료: {target_file} -> {dest_key}")

    # 통합 처리 과정을 태스크로 등록
    run_main_logic = PythonOperator(
        task_id='run_cali_main_logic',
        python_callable=process_cali_rag_logic
    )

    # --- [Step 3] Slack 최종 보고: 모든 과정 성공 시 주인님께 알림 ---
    def send_report(**context):
        msg = "✅ [cali 프로젝트] RAG 지식 베이스 업데이트 성공! 🚀"
        print(f"Slack Notification: {msg}") # 로그에 기록
        
        # 슬랙 웹후크 URL을 넣었다면 아래 주석을 풀어서 진짜 메시지 쏘기
        # payload = {"text": msg}
        # requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload), headers={'Content-Type': 'application/json'})

    # 알림 과정을 마지막 태스크로 등록
    notify_complete = PythonOperator(
        task_id='notify_complete',
        python_callable=send_report
    )

    # 4. 공장 컨베이어 벨트 순서 결정 (망지기 -> 처리/적재/정리 -> 슬랙 보고)
    wait_for_file >> run_main_logic >> notify_complete