import random
import time
from services.milvus_client import MilvusClient
from config.settings import settings

def test_milvus():
    print("=== Milvus 접속 및 CRUD 테스트 시작 ===")
    
    # 1. 클라이언트 초기화 (연결 테스트)
    try:
        client = MilvusClient()
        print(f"✅ Milvus 연결 성공: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    except Exception as e:
        print(f"❌ Milvus 연결 실패: {e}")
        return

    # 2. 더미 벡터 생성 (OpenAI 비용 절감을 위해 랜덤 벡터 사용)
    # 실제로는 OpenAIClient.create_embedding()을 사용해야 함
    dim = settings.VECTOR_DIMENSION
    dummy_vector = [random.random() for _ in range(dim)]
    
    # 3. 데이터 삽입 테스트
    test_log = {
        "service": "test-service",
        "message": "Test error message",
        "cause": "Test Cause",
        "action": "Test Action"
    }
    
    try:
        print("📥 데이터 삽입 시도...")
        client.insert_log_case(test_log, dummy_vector)
        print("✅ 데이터 삽입 완료")
    except Exception as e:
        print(f"❌ 데이터 삽입 실패: {e}")
        return

    # 4. 검색 테스트
    # Milvus는 데이터 인덱싱에 시간이 조금 걸릴 수 있음
    time.sleep(2) 
    
    try:
        print("🔍 데이터 검색 시도...")
        start_time = time.time()
        results = client.search_similar_logs(dummy_vector, top_k=1)
        duration = time.time() - start_time
        
        if results:
            print(f"✅ 검색 성공 ({duration:.2f}s): {len(results)}건 발견")
            print(f"   - 검색된 결과: {results[0]}")
        else:
            print("⚠️ 검색 결과 없음 (인덱싱 지연 가능성)")
            
    except Exception as e:
        print(f"❌ 검색 실패: {e}")

if __name__ == "__main__":
    test_milvus()
