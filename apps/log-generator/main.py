import random
import time
import uuid
import os
from datetime import datetime
from faker import Faker

class CALIIncidentSimulator:
    def __init__(self):
        self.fake = Faker()
        # 1. 5대 핵심 서비스 정의
        self.services = {
            "infra-eks-core": "v1.28.4",
            "db-cache-cluster": "v8.0.32",
            "payment-gateway": "v2.5.0",
            "auth-security-svc": "v4.2.1",
            "biz-logic-engine": "v1.12.0"
        }
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, "logs")
        self.log_file = os.path.join(self.log_dir, "app.log")
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        # Knowledge Base 기반 에러 풀 (Service: [Error Messages])
        self.kb_errors = {
            "auth-security-svc": [
                "Security Alert - High rate of JWT validation failures from IP {ip}",  # auth_security.md
                "Login Failed - Brute Force protection triggered for user {user}",     # KB-01, 10
                "Token Expired - Access token expired, refresh token invalid",        # KB-03
                "MFA Failed - Multi-factor authentication verification failed",       # KB-12
                "API Key Invalid - Unauthorized access attempt, invalid API key"      # KB-19
            ],
            "payment-gateway": [
                "PG Timeout - Upstream provider response timed out after 3000ms",     # payment_pg.md KB-02
                "Double Charge - Duplicate transaction detected for OrderID {uuid}",    # KB-05
                "Circuit Breaker Open - Failure rate threshold exceeded",             # KB-30
                "Payment Declined - Insufficient funds or card limit exceeded",       # KB-12
                "Fraud Detected - Transaction blocked by FDS rules"                   # KB-20
            ],
            "biz-logic-engine": [
                "Inventory Error - Stock count cannot be negative for ItemID {uuid}",  # businesslogic.md KB-01
                "Coupon Error - Coupon usage limit exceeded",                         # KB-10
                "Order Failed - Price mismatch between cart and checkout",            # KB-12
                "Saga Compensation - Refund issued but inventory restore failed"      # KB-16
            ],
            "db-cache-cluster": [
                "Connection Pool - HikariPool-1 connection is not available, timed out", # db_issue.md
                "Deadlock Detected - Transaction rolled back due to deadlock",        # db_cache.md KB-01
                "Slow Query - Query execution time exceeded 2000ms",                  # KB-03
                "Redis Error - OOM command not allowed, maxmemory reached"            # KB-11
            ],
            "infra-eks-core": [
                "HPA Fail - Failed to get cpu utilization for scaling",               # infra_eks.md KB-06
                "Liveness Probe Failed - Pod is unhealthy, restarting...",            # KB-23
                "OOMKilled - Pod memory limit exceeded",                              # KB-21
                "DNS Error - Temporary failure in name resolution",                   # KB-02
                "ImagePullBackOff - Failed to pull image from ECR"                    # KB-03
            ]
        }

    def get_ts(self):
        # OpenSearch 표준 ISO8601 형식
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    def write_log(self, level, svc, msg):
        ver = self.services[svc]
        tid = str(uuid.uuid4())[:8]
        
        # ⭐ 복구 포인트: 사람이 읽기 좋은 문자열 포맷
        # 이 형식을 유지해야 Fluent-bit이 예전처럼 최상단 필드로 파싱합니다.
        log_line = f"[{level}] {self.get_ts()} {svc}/{ver} [{tid}]: {msg}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
            f.flush()
        print(log_line.strip())

    def generate_incident(self):
        """핀테크 연쇄 장애 시나리오 (Knowledge Base 기반)"""
        incident_id = f"FIN-{str(uuid.uuid4())[:5].upper()}"
        
        # 시나리오 1: 보안 공격 -> DB 과부하 -> 결제 실패
        attacker_ip = self.fake.ipv4()
        
        # 1. 보안 공격 시작
        self.write_log("WARN", "auth-security-svc", 
            f"Security Alert - [{incident_id}] Suspicious traffic pattern detected from {attacker_ip}")
        time.sleep(0.5)
        self.write_log("ERROR", "auth-security-svc", 
            f"Security Alert - [{incident_id}] High rate of JWT validation failures from IP {attacker_ip}")
        time.sleep(1)

        # 2. 공격으로 인한 DB 커넥션 고갈 (db_issue.md 반영)
        self.write_log("ERROR", "db-cache-cluster", 
            f"[{incident_id}] HikariPool-1 - Connection is not available, request timed out after 30000ms.")
        time.sleep(1)

        # 3. DB 장애로 인한 결제 타임아웃 및 서킷 브레이커 발동
        self.write_log("CRITICAL", "payment-gateway", 
            f"[{incident_id}] External PG Timeout. Circuit Breaker: OPEN. Transaction rolled back.")

    def run(self):
        while True:
            dice = random.random()
            
            # A. [1%] 로그 폭주 (DDoS / Brute Force 테스트)
            if dice < 0.01:
                target_ip = self.fake.ipv4()
                print(f"⚠️  Burst Mode: Attack from {target_ip}")
                for _ in range(20):
                    msg = random.choice(self.kb_errors["auth-security-svc"]).format(ip=target_ip, user="admin")
                    self.write_log("WARN", "auth-security-svc", msg)
                time.sleep(1)

            # B. [5%] 치명적 연쇄 장애 (Incident)
            elif dice < 0.06:
                self.generate_incident()
            
            # C. [20%] 일반 에러 (Knowledge Base에서 랜덤 추출)
            elif dice < 0.20:
                # 임의의 서비스 선택
                svc = random.choice(list(self.services.keys()))
                # 해당 서비스의 KB 에러 목록에서 랜덤 선택
                if svc in self.kb_errors:
                    raw_msg = random.choice(self.kb_errors[svc])
                    # 포맷팅 필요 시 더미 데이터 주입
                    try:
                        msg = raw_msg.format(
                            ip=self.fake.ipv4(), 
                            user=self.fake.user_name(), 
                            uuid=str(uuid.uuid4())[:8]
                        )
                    except:
                        msg = raw_msg # 포맷팅 실패 시 원본 사용

                    self.write_log("ERROR", svc, f"Process Failed: {msg}")
            
            # D. [80%] 정상 로그
            else:
                svc = random.choice(list(self.services.keys()))
                self.write_log("INFO", svc, f"User {self.fake.user_name()} - Action Completed - 200 OK")
            
            time.sleep(random.uniform(1, 2.5)) # 로그 발생 주기 약간 가속

if __name__ == "__main__":
    CALIIncidentSimulator().run()