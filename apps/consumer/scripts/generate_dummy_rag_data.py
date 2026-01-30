import sys
import os
import glob
import re
import sys
import os
import glob
import re
# import yaml (Removed to avoid dependency issues)
from typing import List, Dict

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from utils.logger import setup_logger
from utils.text_preprocessor import clean_log_for_embedding

logger = setup_logger(__name__)

KB_DIR = "knowledge_base"

def parse_yaml_manually(yaml_text):
    """PyYAML 없이 간단한 키-값 파싱"""
    metadata = {}
    for line in yaml_text.splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()
    return metadata

def parse_markdown_kb_multi(file_path):
    """MD 파일 파싱 (seed_milvus.py 로직 재사용)"""
    cases = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        pattern = re.compile(r"## \d+\..+?(?=## \d+\.|$)", re.DOTALL)
        sections = pattern.findall(full_text)
        
        for section in sections:
            try:
                yaml_match = re.search(r"---\n(.+?)\n---", section, re.DOTALL)
                if not yaml_match: continue
                
                # metadata = yaml.safe_load(yaml_match.group(1))
                metadata = parse_yaml_manually(yaml_match.group(1))
                
                body_text = section.replace(yaml_match.group(0), "")
                
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
            except: continue
    except: pass
    return cases

SYSTEM_PROMPT_GENERATOR = """
You are a Synthetic Log Data Generator for a SRE Knowledge Base.
Your task is to generate realistic variations of a given error log scenario.

Input Format:
- Service: <service_name>
- Original Error: <error_message>
- Context: <summary_and_cause>

Output Format (JSON List):
[
    {
        "message": "Varied error message 1",
        "log_content": "Multi-line stack trace conforming to Java/Python/Go standard..."
    },
    ...
]

Rules:
1. Generate 3 unique variations.
2. Maintain the same technical root cause but vary the specific error phrasing, timestamps, thread names, or variable values.
3. 'log_content' must be a realistic stack trace or log block (at least 3-5 lines).
"""

def generate_variations(ai_client, case) -> List[Dict]:
    """OpenAI를 사용하여 변형 데이터 생성"""
    prompt = f"""
    Service: {case['service']}
    Original Error: {case['message']}
    Context: {case['log_content']} / Cause: {case['cause']}
    """
    
    try:
        # OpenAI Completion API 호출 (JSON 모드 권장)
        # OpenAIClient.analyze_log 등을 우회하여 직접 client 호출이 필요하나, 
        # 여기서는 analyze_log 구조를 빌려쓰거나 client.client.chat.completions를 씁니다.
        # OpenAIClient 구조상 client 속성 접근 가능하다고 가정.
        
        response = ai_client.client.chat.completions.create(
            model="gpt-4-turbo-preview",  # 또는 gpt-3.5-turbo-0125
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_GENERATOR},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        content = response.choices[0].message.content
        data = json.loads(content)
        # 예상 포맷: {"variations": [...]} or list directly
        # 프롬프트에서 list를 요청했으므로 { "variations": [...] } 형태로 받도록 유도하거나 파싱
        
        # 안전한 파싱
        if isinstance(data, list): return data
        if "variations" in data: return data["variations"]
        return []
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        return []

def run_generator():
    print("🚀 Synthetic Data Generator Started...")
    milvus = MilvusClient()
    ai = OpenAIClient()
    
    md_files = glob.glob(os.path.join(KB_DIR, "*.md"))
    total_generated = 0
    
    for file_path in md_files:
        print(f"Reading {os.path.basename(file_path)}...")
        cases = parse_markdown_kb_multi(file_path)
        
        for case in cases:
            print(f"  - Generating variants for: {case['message'][:30]}...")
            variations = generate_variations(ai, case)
            
            for v in variations:
                # 메타데이터는 원본 유지 (Cause/Action은 동일하므로 RAG 정답률 상승)
                new_case = case.copy()
                new_case['message'] = v['message']
                new_case['log_content'] = v['log_content']
                new_case['is_synthetic'] = True
                
                # 임베딩 & 저장
                clean_text = clean_log_for_embedding(
                    new_case['service'], new_case['message'], new_case['log_content']
                )
                full_context = f"{clean_text} \nCause: {new_case['cause']} \nAction: {new_case['action']}"
                
                vector = ai.create_embedding(full_context) # 청킹 없이 전체 1개로 저장
                milvus.insert_log_case(new_case, vector, flush=False)
                total_generated += 1
                
    milvus.flush_collection()
    print(f"✅ Generated & Inserted {total_generated} synthetic records.")

if __name__ == "__main__":
    run_generator()
