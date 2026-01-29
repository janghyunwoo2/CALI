from services.milvus_client import MilvusClient
from config.settings import settings

def check_count():
    print(f"=== Milvus Collection Status ({settings.MILVUS_COLLECTION_NAME}) ===")
    
    try:
        client = MilvusClient()
        
        # Flush to ensure data is visible
        client.collection.flush()
        
        num_entities = client.collection.num_entities
        print(f"📊 Total Entities: {num_entities}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_count()
