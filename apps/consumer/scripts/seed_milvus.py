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
CHUNK_SIZE = 1000  # 청킹 기준 (글자 수)
CHUNK_OVERLAP = 200  # 중복 허용 범위

def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    긴 텍스트를 의미 단위로 쪼개는 청킹(Chunking) 함수
    (LangChain의 RecursiveCharacterTextSplitter와 유사한 로직)
    """
    if len(text) <= chunk_size:
        return [text]
        
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:])
            break
            
        # 문장 끝(.)이나 줄바꿈(\n) 등 자연스러운 분기점 찾기
        # 못 찾으면 그냥 자름
        split_point = -1
        for delimiter in ["\n\n", "\n", ". ", " "]:
            idx = text.rfind(delimiter, start, end)
            if idx != -1 and idx > start + (chunk_size // 2):
                split_point = idx + len(delimiter)
                break
        
        if split_point == -1:
            split_point = end
            
        chunks.append(text[start:split_point])
        start = split_point - overlap # 겹치게 이동
        
    return chunks

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
        
        # Action Items 섹션이 없는 경우 대비
        if "## Action Items" in remaining:
            cause_part, action_part = remaining.split("## Action Items")
        else:
            cause_part = remaining
            action_part = "참고: Action Items 섹션이 없습니다."
        
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
            
            # 1. 텍스트 전처리 (노이즈 제거)
            clean_text = clean_log_for_embedding(
                case['service'], 
                case['message'], 
                case['log_content']
            )
            # 검색 정확도를 위해 cause/action도 임베딩 텍스트에 포함
            full_context = f"{clean_text} \nCause: {case['cause']} \nAction: {case['action']}"
            
            # 2. 청킹 (Chunking) - 문맥 단위 분할
            chunks = chunk_text(full_context)
            if len(chunks) > 1:
                print(f"   -> 텍스트 길이가 길어 {len(chunks)}개 청크로 분할합니다.")
            
            # 3. 기존 데이터 삭제 (Upsert 전처리)
            # 청크가 여러 개일 수 있으므로, 먼저 해당 케이스의 데이터를 모두 지움
            milvus_client.delete_log_case(case['service'], case['message'])
            
            # 4. 청크별 임베딩 및 저장
            for i, chunk in enumerate(chunks):
                vector = ai_client.create_embedding(chunk)
                
                if not vector:
                    print(f"❌ 임베딩 실패 (Chunk {i}): {case['message']}")
                    continue
                
                # 메타데이터는 원본 유지 (검색되면 전체 Action을 보여주기 위함)
                # 단, 디버깅을 위해 로그에는 청크 인덱스 표시
                milvus_client.insert_log_case(case, vector)
                
            print(f"✅ 저장 완료 ({len(chunks)} chunks): {case['service']} - {case['message']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 저장 실패 ({file_path}): {e}")

    print(f"=== 초기화 완료 (Total: {success_count}건) ===")

if __name__ == "__main__":
    seed_milvus()
