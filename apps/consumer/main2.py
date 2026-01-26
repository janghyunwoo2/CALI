import os
import time

import boto3
from botocore.exceptions import ClientError

# 환경 변수 설정
STREAM_NAME = os.environ.get("KINESIS_STREAM_NAME", "cali-log-stream")
REGION = os.environ.get("AWS_REGION", "ap-northeast-2")


def get_kinesis_client():
    """Kinesis 클라이언트 생성"""
    return boto3.client("kinesis", region_name=REGION)


def main():
    print(f"Starting Simple Consumer (main2.py) for stream: {STREAM_NAME}")
    kinesis = get_kinesis_client()

    # 1. 샤드 목록 가져오기
    try:
        response = kinesis.list_shards(StreamName=STREAM_NAME)
        shards = response.get("Shards", [])
        print(f"Found {len(shards)} shards: {[s['ShardId'] for s in shards]}")
    except ClientError as e:
        print(f"FATAL: Error listing shards: {e}")
        return

    if not shards:
        print("No shards found. Exiting.")
        return

    # 2. 각 샤드에 대한 Iterator 초기화 (LATEST: 실행 이후 들어오는 데이터만 수신)
    shard_iterators = {}
    for shard in shards:
        shard_id = shard["ShardId"]
        try:
            sh_itr = kinesis.get_shard_iterator(
                StreamName=STREAM_NAME, ShardId=shard_id, ShardIteratorType="LATEST"
            )
            shard_iterators[shard_id] = sh_itr["ShardIterator"]
            print(f"Initialized iterator for {shard_id}")
        except ClientError as e:
            print(f"Error getting iterator for {shard_id}: {e}")

    # 3. 무한 루프 폴링
    print("Start polling records...")
    try:
        while True:
            # 활성 Iterator가 없으면 종료
            if not shard_iterators:
                print("No active shards to poll.")
                break

            for shard_id, iterator in list(shard_iterators.items()):
                try:
                    # 레코드 가져오기
                    resp = kinesis.get_records(ShardIterator=iterator, Limit=10)
                    records = resp.get("Records", [])

                    # 데이터 출력
                    for record in records:
                        data = record["Data"]
                        try:
                            # 바이트 데이터를 문자열로 디코딩
                            decoded_data = data.decode("utf-8")
                            print(f"[DATA received from {shard_id}]: {decoded_data}")
                        except Exception:
                            print(f"[BINARY data from {shard_id}]: {data}")

                    # 다음 Iterator 업데이트
                    next_iterator = resp.get("NextShardIterator")

                    # 밀리세컨드 단위 지연 (Kinesis 읽기 제한 방지)
                    time.sleep(0.2)

                    if next_iterator:
                        shard_iterators[shard_id] = next_iterator
                    else:
                        print(f"Shard {shard_id} closed.")
                        del shard_iterators[shard_id]

                except ClientError as e:
                    # ProvisionedThroughputExceededException 등 처리
                    print(f"Warning reading from {shard_id}: {e}")
                    time.sleep(1)
                except Exception as e:
                    print(f"Error reading from {shard_id}: {e}")
                    time.sleep(1)

            # 전체 루프 1초 대기 (CPU 과부하 방지)
            time.sleep(1.0)

    except KeyboardInterrupt:
        print("Consumer stopped by user.")


if __name__ == "__main__":
    main()
