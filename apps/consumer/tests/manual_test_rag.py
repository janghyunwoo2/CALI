import os
import sys

# 프로젝트 루트 경로를 sys.path에 추가 (앱 내 모듈 임포트 위함)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from datetime import datetime
from models.log_schema import LogRecord
from services.milvus_client import MilvusClient
from services.openai_client import OpenAIClient
from services.slack_notifier import SlackNotifier
from utils.text_preprocessor import clean_log_for_embedding

def run_manual_test():
    print("🚀 Manual RAG Verification Script Started...")

    # 1. 컴포넌트 초기화
    try:
        milvus = MilvusClient()
        ai = OpenAIClient()
        slack = SlackNotifier()
        print("✅ Services Initialized (Milvus, OpenAI, Slack)")
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. 테스트 시나리오 정의 (Knowledge Base와 일치)
    test_cases = [
        {
            "service": "common-db",
            "level": "ERROR",
            # KB: remaining connection slots are reserved
            "message": "remaining connection slots are reserved", 
            "log_content": """FATAL: remaining connection slots are reserved
    at org.postgresql.core.v3.ConnectionFactoryImpl.openConnectionImpl(ConnectionFactoryImpl.java:342)
    at org.postgresql.core.ConnectionFactory.openConnection(ConnectionFactory.java:54)"""
        },
        {
            "service": "payment-api",
            "level": "ERROR",
            # KB: OOMKilled
            "message": "OOMKilled", 
            "log_content": """Warning: OOMKilled - Container payment-api limit reached.
    Host kernel: [1234.56] Out of memory: Kill process 234 (java) score 950 or sacrifice child
    Killed process 234 (java) total-vm:4GB, anon-rss:2GB, file-rss:0kB"""
        },
        {
            "service": "payment-api",
            "level": "ERROR",
            # KB: request timeout
            "message": "request timeout", 
            "log_content": """java.net.SocketTimeoutException: request timeout
    at java.net.SocketInputStream.socketRead0(Native Method)
    at java.net.SocketInputStream.socketRead(SocketInputStream.java:116)
    at sun.security.ssl.InputRecord.read(InputRecord.java:504)"""
        }
    ]

    # 3. 시나리오 실행
    # 3. Aggregation Logic Test
    # 테스트를 위해 윈도우 시간을 단축 (60s -> 3s)
    slack.throttler.window_seconds = 3
    print(f"⚡ Testing Aggregation Logic (Window: 3s)")
    
    for i, case in enumerate(test_cases[:1]): # 첫 번째 케이스만 테스트
        print(f"\n[Test Case #{i+1}] {case['service']} - {case['message']}")
        
        # 3-1. 최초 발생 (First Alert)
        print("   Attempt 1 (Expected: First Alert)...", end="")
        
        # LogRecord 생성
        record = LogRecord(
            timestamp=datetime.now(),
            service=case['service'],
            level=case['level'],
            message=case['message'],
            log_content=case['log_content'],
            environment="test-manual"
        )
        
        # Throttle Check
        alert_key = f"{record.service}_{record.message[:100]}"
        # manual_test_rag에서는 slack.throttler를 직접 사용 (Consumer와 동일 로직 시뮬레이션)
        # slack_notifier 내부에는 이제 throttler 로직이 제거되었거나 미사용됨 -> 직접 호출 필요
        
        # **중요**: slack.throttler 인스턴스를 직접 제어
        is_first = slack.throttler.record_occurrence(record.service, record.message)
        
        if is_first:
            # RAG Pipeline Simulation
            rag_info = {"source": "ManualTest", "occurrence_count": 1}
            analysis = {"cause": "Test Cause", "action": "Test Action"}
            
            sent = slack.send_alert(record.model_dump(), analysis, rag_info)
            if sent:
                print(" -> 🔔 SENT! (First Alert)")
        else:
            print(" -> ❌ Error: Should have been sent!")
            
        # 3-2. 추가 발생 (Aggregation) - 5번 반복
        print("   Generating 5 duplicates (Expected: Throttled)...")
        for j in range(5):
            is_first = slack.throttler.record_occurrence(record.service, record.message)
            if not is_first:
                print(f"     Dup #{j+1} -> 🔇 Buffered")
            else:
                print(f"     Dup #{j+1} -> ❌ Error: Should be throttled!")
                
        # 3-3. 윈도우 만료 대기 (3초)
        print("   Waiting 4s for window expiry...", end="")
        time.sleep(4)
        print(" Done.")
        
        # 3-4. 요약 알림 확인
        print("   Checking summaries...", end="")
        summaries = slack.throttler.get_summaries_to_send()
        
        if summaries:
            print(f" -> 📊 Summaries Found: {len(summaries)}")
            for s in summaries:
                print(f"      Service: {s['service']}, Count: {s['count']}, Duration: {s['duration']}s")
                slack.send_summary_alert(s['service'], s['message'], s['count'], s['duration'])
                print("      -> 📨 Summary Sent!")
        else:
             print(" -> ❌ No summaries found (Failed)")

    print("\n✅ Verification Finished. Check Slack for 1 Red Alert + 1 Gray Summary.")

if __name__ == "__main__":
    run_manual_test()
