import random
from config.settings import settings
from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from utils.logger import setup_logger

logger = setup_logger(__name__)

import os
import glob
import frontmatter  # pip install python-frontmatter
from config.settings import settings
from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from utils.logger import setup_logger
from utils.text_preprocessor import clean_log_for_embedding

logger = setup_logger(__name__)

KB_DIR = "knowledge_base"

def parse_markdown_kb(file_path):
    """MD 파일 파싱 (Frontmatter + Sections)"""
    with open(file_path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)
        
    content = post.content
    metadata = post.metadata
    
    # 간단한 섹션 파싱 (## Root Cause, ## Action Items 기준)
    try:
        parts = content.split("## Root Cause")
        summary_part = parts[0].replace("## Incident Summary", "").strip()
        
        remaining = parts[1]
        cause_part, action_part = remaining.split("## Action Items")
        
        return {
            "service": metadata.get("service", "unknown"),
            "message": metadata.get("error_message", "unknown error"),
            "log_content": summary_part.strip(),
            "cause": cause_part.strip(),
            "action": action_part.strip()
        }
    except Exception as e:
        logger.warning(f"파일 파싱 실패 ({file_path}): 형식이 맞지 않습니다. {e}")
        return None

def seed_milvus():
    print(f"=== Milvus 지식 베이스 초기화 (Source: {KB_DIR}/*.md) ===")
    
    milvus_client = MilvusClient()
    ai_client = OpenAIClient()
    
    # 지식 베이스 폴더 내의 모든 .md 파일 로드
    md_files = glob.glob(os.path.join(KB_DIR, "*.md"))
    if not md_files:
        print(f"⚠️ '{KB_DIR}' 폴더에 .md 파일이 없습니다.")
        return

    success_count = 0
    
    for file_path in md_files:
        case = parse_markdown_kb(file_path)
        if not case:
            continue
            
        try:
            print(f"Processing: {os.path.basename(file_path)}...")
            
            # 1. 임베딩 생성 (Text Preprocessing 적용!)
            # 노이즈를 제거하여 벡터 품질 향상
            clean_text = clean_log_for_embedding(
                case['service'], 
                case['message'], 
                case['log_content']
            )
            vector = ai_client.create_embedding(clean_text)
            
            if not vector:
                print(f"❌ 임베딩 실패: {case['message']}")
                continue
                
            # 2. 데이터 삽입
            milvus_client.insert_log_case(case, vector)
            print(f"✅ 저장 완료: {case['service']} - {case['message']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 저장 실패 ({file_path}): {e}")

    print(f"=== 초기화 완료 (Total: {success_count}건) ===")

if __name__ == "__main__":
    seed_milvus()
