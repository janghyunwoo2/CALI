import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
import glob
import frontmatter  # pip install python-frontmatter
from config.settings import settings
from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from utils.logger import setup_logger
from utils.text_preprocessor import clean_log_for_embedding

logger = setup_logger(__name__)

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")
CHUNK_SIZE = 500  # 청킹 기준 (글자 수)
CHUNK_OVERLAP = 100  # 중복 허용 범위

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

def parse_markdown_kb_multi(file_path):
    """MD 파일 파싱 (다중 케이스 지원)"""
    cases = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        # 정규표현식으로 각 항목 분리 (## 번호. 제목 패턴)
        # 예: ## 01. Title ... (다음 ## 번호 전까지)
        import re
        pattern = re.compile(r"## \d+\..+?(?=## \d+\.|$)", re.DOTALL)
        sections = pattern.findall(full_text)
        
        if not sections:
            # 기존 단일 포맷 지원 (백워드 호환)
            single_case = parse_markdown_kb_legacy(file_path)
            if single_case: cases.append(single_case)
            return cases

        for section in sections:
            try:
                # YAML 파싱 (--- ... ---)
                yaml_match = re.search(r"---\n(.+?)\n---", section, re.DOTALL)
                if not yaml_match:
                    continue
                
                yaml_text = yaml_match.group(1)
                import yaml
                metadata = yaml.safe_load(yaml_text)
                
                # 본문 파싱
                body_text = section.replace(yaml_match.group(0), "")
                
                # 간단한 섹션 파싱
                summary = ""
                cause = "분석 중..."
                action = "내용 없음"
                
                parts = body_text.split("### Root Cause")
                if len(parts) > 1:
                    summary = parts[0].replace("### Incident Summary", "").strip()
                    remaining = parts[1]
                    if "### Action Items" in remaining:
                        c, a = remaining.split("### Action Items")
                        cause = c.strip()
                        action = a.strip()
                    else:
                        cause = remaining.strip()
                
                cases.append({
                    "service": metadata.get("service", "unknown"),
                    "message": metadata.get("error_message", "unknown error"),
                    "log_content": summary,
                    "cause": cause,
                    "action": action
                })
            except Exception as e:
                logger.warning(f"섹션 파싱 실패: {e}")
                continue

    except Exception as e:
        logger.warning(f"파일 파싱 실패 ({file_path}): {e}")
    
    return cases

def parse_markdown_kb_legacy(file_path):
    """기존 단일 파일 파싱 (백업용)"""
    try:
        import frontmatter
        with open(file_path, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
        parts = post.content.split("## Root Cause")
        summary = parts[0].replace("## Incident Summary", "").strip()
        remaining = parts[1]
        if "### Action Items" in remaining:
            c, a = remaining.split("### Action Items")
            cause = c.strip()
            action = a.strip()
        else:
            cause = remaining.strip()
            action = "내용 없음"
        return {
            "service": post.metadata.get("service", "unknown"),
            "message": post.metadata.get("error_message", "unknown error"),
            "log_content": summary,
            "cause": cause,
            "action": action
        }
    except:
        return None

def seed_milvus():
    print(f"=== Milvus 지식 베이스 추가 (Source: {KB_DIR}/*.md) ===")
    
    milvus_client = MilvusClient()
    ai_client = OpenAIClient()
    
    md_files = glob.glob(os.path.join(KB_DIR, "*.md"))
    success_count = 0
    
    for file_path in md_files:
        print(f"Processing File: {os.path.basename(file_path)}...")
        cases = parse_markdown_kb_multi(file_path)
        
        if not cases:
            print(f"   -> No cases found in {file_path}")
            continue

        print(f"   -> Found {len(cases)} cases.")
        
        for case in cases:
            try:
                # 1. 텍스트 전처리
                clean_text = clean_log_for_embedding(
                    case['service'], 
                    case['message'], 
                    case['log_content']
                )
                full_context = f"{clean_text} \nCause: {case['cause']} \nAction: {case['action']}"
                
                # 2. 청킹
                chunks = chunk_text(full_context)
                
                # 3. 기존 데이터 삭제 (Upsert)
                # 대량 처리를 위해 flush=False 설정
                # 중복 방지 삭제 로직 제거 (Append 모드)
                # milvus_client.delete_log_case(case['service'], case['message'], flush=False)
                
                # 4. 저장
                for i, chunk in enumerate(chunks):
                    vector = ai_client.create_embedding(chunk)
                    if vector:
                        milvus_client.insert_log_case(case, vector, flush=False)
                
                success_count += 1
                if success_count % 50 == 0:
                    print(f"   ... Processed {success_count} cases so far (Flushing...)")
                    milvus_client.flush_collection()
                    
            except Exception as e:
                print(f"❌ Case Error: {e}")

    # 최종 Flush
    milvus_client.flush_collection()
    print(f"=== 초기화 완료 (Total: {success_count}건) ===")

    print(f"=== 초기화 완료 (Total: {success_count}건) ===")

if __name__ == "__main__":
    seed_milvus()
