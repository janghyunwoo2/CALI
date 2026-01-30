import sys
import os
import glob
import re
import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from utils.logger import setup_logger
from utils.text_preprocessor import clean_log_for_embedding

logger = setup_logger(__name__)

KB_DIR = "knowledge_base"
BATCH_SIZE = 20
MAX_WORKERS = 10

SYSTEM_PROMPT_LOG_CREATOR = """
You are a Synthetic Log Generator.
Your task is to generate a REALISTIC LOG START TRACE or ERROR LOG BLOCK based on the provided incident summary.

Input:
- Service: <service>
- Error Message: <message>
- Root Cause: <cause>

Output Format (JSON):
{
    "log_content": "2024-05-20 10:23:45 [ERROR] [Thread-5] ... (Multi-line stack trace)"
}

Rules:
1. The log must match the language/framework of the service (e.g., Java/Spring for auth-service/payment-api, Python for recommendation-engine, Go for api-gateway).
2. Include timestamps, log levels (ERROR), thread IDs, and stack traces.
3. Do NOT include markdown formatting (```). Output raw JSON.
"""

def parse_yaml_manually(yaml_text):
    metadata = {}
    for line in yaml_text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()
    return metadata

def parse_markdown_kb_entries(file_path):
    """MD 파일 내의 모든 섹션 파싱"""
    cases = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        # "## 숫자. 제목" 패턴으로 섹션 분리
        pattern = re.compile(r"## \d+\..+?(?=## \d+\.|$)", re.DOTALL)
        sections = pattern.findall(full_text)
        
        for section in sections:
            try:
                # YAML Frontmatter 추출
                yaml_match = re.search(r"---\n(.+?)\n---", section, re.DOTALL)
                if not yaml_match: continue
                
                metadata = parse_yaml_manually(yaml_match.group(1))
                body_text = section.replace(yaml_match.group(0), "")
                
                summary = ""
                cause = "분석 중..."
                action = "내용 없음"
                
                # 본문 파싱 (Summary / Cause / Action)
                # 정규식으로 유연하게 추출
                s_match = re.search(r"### Incident Summary\n(.+?)(?=### Root Cause|$)", body_text, re.DOTALL)
                c_match = re.search(r"### Root Cause\n(.+?)(?=### Action Items|$)", body_text, re.DOTALL)
                a_match = re.search(r"### Action Items\n(.+?)$", body_text, re.DOTALL)
                
                if s_match: summary = s_match.group(1).strip()
                if c_match: cause = c_match.group(1).strip()
                if a_match: action = a_match.group(1).strip()
                
                cases.append({
                    "service": metadata.get("service", "unknown"),
                    "message": metadata.get("error_message", "unknown error"),
                    "log_content": summary, # 임시로 요약을 넣고, 나중에 LLM으로 스택트레이스 생성 덮어쓰기
                    "summary": summary,
                    "cause": cause,
                    "action": action
                })
            except Exception as e:
                logger.warning(f"Section parsing failed: {e}")
                continue
    except Exception as e:
        logger.error(f"File reading failed {file_path}: {e}")
        
    return cases

def generate_log_content(ai_client, case) -> str:
    """OpenAI를 사용하여 리얼한 로그 스택트레이스 생성"""
    prompt = f"""
    Service: {case['service']}
    Error Message: {case['message']}
    Root Cause: {case['cause']}
    summary: {case['summary']}
    """
    
    try:
        response = ai_client.client.chat.completions.create(
            model="gpt-4-turbo-preview", 
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_LOG_CREATOR},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("log_content", case['summary'])
        
    except Exception as e:
        logger.error(f"Log generation failed for {case['message'][:20]}: {e}")
        return case['summary'] # 실패 시 요약본이라도 사용

def process_case(ai_client, case):
    """단일 케이스 처리 (로그 생성 -> 임베딩 -> Row)"""
    # 1. 로그 생성 (Flesh out)
    real_log = generate_log_content(ai_client, case)
    case['log_content'] = real_log # 업데이트
    
    # 2. 임베딩
    clean_text = clean_log_for_embedding(
        case['service'], case['message'], case['log_content']
    )
    full_context = f"{clean_text} \nCause: {case['cause']} \nAction: {case['action']}"
    
    vector = ai_client.create_embedding(full_context)
    
    if vector:
         row = {
            "vector": vector,
            "service": case.get("service", "unknown")[:64],
            "error_message": case.get("message", "")[:1024],
            "cause": case.get("cause", "")[:2048],
            "action": case.get("action", "")[:2048],
        }
         return row
    return None

def run_generator():
    start_time = time.time()
    print(f"🚀 KB-Based Data Generator Started (Fleshing out scenarios)...")
    
    milvus = MilvusClient()
    ai = OpenAIClient()
    
    # 1. 모든 파일 로드
    md_files = glob.glob(os.path.join(KB_DIR, "*.md"))
    all_cases = []
    for file_path in md_files:
        p = parse_markdown_kb_entries(file_path)
        print(f"  - Loaded {len(p)} cases from {os.path.basename(file_path)}")
        all_cases.extend(p)
    
    print(f"📊 Total KB Scenarios: {len(all_cases)}")
    
    generated_count = 0
    batch_buffer = []
    
    # 2. 병렬 처리
    print(f"⚡ Generating realistic logs with {MAX_WORKERS} workers...")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Future -> Case
        futures = [executor.submit(process_case, ai, case) for case in all_cases]
        
        for future in as_completed(futures):
            row = future.result()
            if row:
                batch_buffer.append(row)
                generated_count += 1
                print(f"  + Prepared: {row['service']} - {row['error_message'][:30]}...")
                
                if len(batch_buffer) >= BATCH_SIZE:
                     print(f"💾 Flushing batch of {len(batch_buffer)}...")
                     milvus.collection.insert(batch_buffer)
                     batch_buffer = []
    
    if batch_buffer:
        milvus.collection.insert(batch_buffer)
        
    milvus.flush_collection()
    print(f"\n✅ Inserted {generated_count} enhanced KB records in {time.time()-start_time:.2f}s")

if __name__ == "__main__":
    run_generator()
