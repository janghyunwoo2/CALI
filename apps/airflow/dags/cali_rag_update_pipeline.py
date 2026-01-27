import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor  # S3 파일 감시용 센서
from airflow.providers.amazon.aws.hooks.s3 import S3Hook        # S3 조작용 갈고리(Hook)
from airflow.operators.python import PythonOperator           # 파이썬 함수 실행용 오퍼레이터

# 1. 환경 설정 단계
BUCKET_NAME = os.getenv('S3_BACKUP_BUCKET')  # OS 환경 변수에서 S3 버킷 이름 가져오기
SOLUTIONS_PREFIX = 'solutions/'             # 파일이 들어올 입구 경로
PROCESSED_PREFIX = 'processed/'             # 처리가 끝난 파일이 이동할 출구 경로

# 2. 모든 작업에 공통으로 적용될 기본 설정
default_args = {
    'owner': 'cali',                        # 이 작업의 주인 이름
    'retries': 1,                           # 실패 시 딱 한 번 더 시도하기
    'retry_delay': timedelta(minutes=5),    # 재시도 전 5분 동안 휴식하기
}

# 3. DAG(작업 흐름) 설계 시작
with DAG(
    dag_id='cali_rag_update_pipeline',      # 에어플로우 UI에서 보일 공장 이름
    default_args=default_args,              # 위에서 만든 기본 설정 적용
    start_date=datetime(2026, 1, 27),       # 이 공장이 가동을 시작하는 날짜
    schedule_interval=None,                 # 정기 실행 없이 수동으로만 돌리기
    catchup=False,                          # 과거의 기록은 신경 쓰지 않기
    tags=['cali', 'rag', 'ge']              # 검색하기 편하게 태그 달기
) as dag:

    # --- [Step 1] S3 센서: 파일이 올 때까지 기다리는 망지기 ---
    wait_for_solution = S3KeySensor(
        task_id='wait_for_solution_file',   # 이 단계의 이름
        bucket_name=BUCKET_NAME,            # 감시할 S3 바구니 이름
        bucket_key=f'{SOLUTIONS_PREFIX}*.txt', # .txt로 끝나는 파일이 오는지 감시
        wildcard_match=True,                # 별표(*)를 사용해서 패턴 찾기 허용
        do_xcom_push=True,                  # 찾은 파일 이름을 쪽지(XCom)에 적어두기
        timeout=60 * 60 * 24,               # 최대 24시간 동안 기다려보기
        poke_interval=10,                   # 10초마다 한 번씩 S3 들여다보기
        mode='poke'                         # 센서가 직접 계속 확인하는 방식
    )

    # --- [Step 2] 검증 함수: 파일 내용을 읽고 불량 골라내기 ---
    def validate_and_process(**context):
        ti = context['task_instance']       # 현재 돌아가는 작업의 정보(쪽지 가방) 가져오기
        s3_hook = S3Hook(aws_conn_id='aws_default') # S3에 접근할 수 있는 권한 갈고리 생성
        
        # [Pull] 앞 단계(망지기)가 적어준 파일 경로 쪽지에서 꺼내기
        pushed_value = ti.xcom_pull(task_ids='wait_for_solution_file')
        
        # 로그에 현재 어떤 형태의 데이터가 들어왔는지 출력 (디버깅용)
        print(f"DEBUG: Pushed Value Type: {type(pushed_value)}, Value: {pushed_value}")
        
        # 만약 쪽지가 비어있다면 (배달 사고 시 대비책)
        if not pushed_value:
            print("⚠️ XCom Pull 실패. 직접 S3 폴더를 리스트업합니다.")
            all_files = s3_hook.list_keys(bucket_name=BUCKET_NAME, prefix=SOLUTIONS_PREFIX)
            pushed_value = [f for f in all_files if f.endswith('.txt')]
            if not pushed_value: # 진짜 파일이 없으면 에러 내고 중단
                raise ValueError("S3에 처리할 파일이 없습니다.")

        # 리스트 형태면 첫 번째 파일 선택, 아니면 그대로 사용
        file_key = pushed_value[0] if isinstance(pushed_value, list) else pushed_value
        print(f"✅ 대상 파일 확정: {file_key}")

        # S3에서 실제 파일 안의 텍스트 내용 읽어오기
        content = s3_hook.read_key(file_key, BUCKET_NAME)
        
        # 품질 검사: 텍스트가 20자보다 짧으면 불량으로 간주
        if len(content.strip()) < 20:
            s3_hook.delete_objects(bucket=BUCKET_NAME, keys=file_key) # 불량 파일 삭제
            raise ValueError(f"내용 부실 ({len(content.strip())}자). 파일 삭제 처리.")
        
        # [성공 시 파일 이동] solutions 폴더에서 processed 폴더로 경로 변경
        new_key = file_key.replace(SOLUTIONS_PREFIX, PROCESSED_PREFIX)
        # S3 내부에서 파일 복사하기
        s3_hook.copy_object(
            source_bucket_key=file_key, dest_bucket_key=new_key,
            source_bucket_name=BUCKET_NAME, dest_bucket_name=BUCKET_NAME
        )
        # 원래 위치에 있던 파일 삭제하기 (이동 완료)
        s3_hook.delete_objects(bucket=BUCKET_NAME, keys=file_key)
        
        # [Push] 검사 끝난 깨끗한 내용을 'final_content'라는 이름표 붙여서 쪽지에 적기
        ti.xcom_push(key='final_content', value=content)

    # 파이썬 함수를 태스크로 등록
    validate_task = PythonOperator(
        task_id='validate_solution_quality',
        python_callable=validate_and_process
    )

    # --- [Step 3] RAG 업데이트: Milvus에 데이터 넣기 ---
    def update_milvus(**context):
        ti = context['task_instance']       # 작업 정보 가져오기
        # [Pull] 앞 단계(검사원)가 적어준 'final_content' 쪽지 꺼내기
        solution_text = ti.xcom_pull(key='final_content', task_ids='validate_solution_quality')
        
        # 만약 쪽지에 내용이 없으면 에러 내기
        if not solution_text:
            raise ValueError("검증된 텍스트 데이터를 XCom에서 찾을 수 없습니다.")
            
        # 실제 업데이트가 일어날 지점 (현재는 로그만 출력)
        print(f"🚀 Milvus 적재 준비 완료! 데이터 길이: {len(solution_text)}")

    # 파이썬 함수를 태스크로 등록
    update_rag_task = PythonOperator(
        task_id='update_milvus_knowledge',
        python_callable=update_milvus
    )

    # --- [Step 4] 완료 알림: 마지막 보고 ---
    notify_success = PythonOperator(
        task_id='notify_update_complete',
        python_callable=lambda: print("Slack 알림: 지식 베이스 업데이트 완료! 🚀")
    )

    # 4. 작업 벨트 연결 (순서 정하기)
    # 망지기 >> 검사원 >> 적재함 >> 알림봇
    wait_for_solution >> validate_task >> update_rag_task >> notify_success