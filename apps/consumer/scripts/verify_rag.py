from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from config.settings import settings
from utils.text_preprocessor import clean_log_for_embedding

def verify_rag():
    print("=== RAG 검색 검증 시작 ===")
    
    milvus = MilvusClient()
    ai = OpenAIClient()
    
    # 1. 테스트 쿼리 (auth_security.md와 유사한 내용)
    # 실제 로그처럼 timestamp나 IP가 섞여 있어도 전처리기가 제거해줄 것임
    raw_query = "2026-01-29 10:00:00 [ERROR] Excessive JWT validation failures observed from specific IP address 192.168.1.1."
    print(f"🔎 Raw Query: {raw_query}")

    clean_query = clean_log_for_embedding("auth-service", "Excessive JWT failures", raw_query)
    print(f"🧹 Clean Query: {clean_query}")
    
    # 2. 임베딩 생성
    vector = ai.create_embedding(clean_query)
    
    # 3. 검색
    results = milvus.search_similar_logs(vector, top_k=1)
    
    if not results:
        print("❌ 검색 결과 없음. 데이터가 제대로 들어갔는지 확인하세요.")
        return

    top_result = results[0]
    score = top_result['score']
    
    print(f"\n✅ 검색 성공 (Top 1) - Distance: {score:.4f}")
    print(f"   - Service: {top_result['service']}")
    print(f"   - Error: {top_result['error']}")
    print(f"   - Cause: {top_result['cause']}")
    
    # 4. Cache Hit 여부 판단
    if score < 0.35:
        print("\n🚀 [Cache Hit] 예상됨: 거리 < 0.35")
        print("   -> OpenAI 호출 없이 즉시 해결책을 반환할 수 있습니다.")
    else:
        print("\n⚠️ [Cache Miss] 예상됨: 거리 >= 0.35")
        print("   -> OpenAI 정밀 분석이 수행될 것입니다.")

if __name__ == "__main__":
    verify_rag()
