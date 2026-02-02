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

    def write_log(self, level, svc, msg, extra_info=None):
        ver = self.services[svc]
        tid = str(uuid.uuid4())[:8]
        
        # 기본 로그
        log_line = f"[{level}] {self.get_ts()} {svc}/{ver} [{tid}]: {msg}"
        
        # 추가 컨텍스트 정보가 있으면 JSON 스타일로 덧붙임
        if extra_info:
            context_str = ", ".join([f'{k}="{v}"' for k, v in extra_info.items()])
            log_line += f" | Context: {{{context_str}}}"
            
        log_line += "\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
            f.flush()
        print(log_line.strip())

    def generate_context(self, svc):
        """서비스별 랜덤 컨텍스트 생성 (메타데이터)"""
        if svc == "auth-security-svc":
            return {
                "UserAgent": self.fake.user_agent(),
                "ClientIP": self.fake.ipv4(),
                "AuthMethod": random.choice(["Bearer", "Basic", "OAuth2", "APIKey"]),
                "Region": random.choice(["ap-northeast-2", "us-east-1", "eu-west-1"])
            }
        elif svc == "payment-gateway":
            return {
                "Amount": random.randint(1000, 500000),
                "Currency": random.choice(["KRW", "USD", "JPY"]),
                "CardType": random.choice(["Visa", "MasterCard", "Amex"]),
                "MerchantID": f"M-{random.randint(1000, 9999)}"
            }
        elif svc == "biz-logic-engine":
            return {
                "ItemID": f"ITEM-{random.randint(100, 999)}",
                "StockLevel": random.randint(-5, 100),
                "CouponCode": self.fake.bothify(text='??-####-####').upper(),
                "CartID": str(uuid.uuid4())[:8]
            }
        elif svc == "db-cache-cluster":
            return {
                "QueryTime": f"{random.randint(500, 5000)}ms",
                "Table": random.choice(["Orders", "Users", "Payments", "Logs"]),
                "LockWait": f"{random.randint(0, 1000)}ms",
                "SQLState": random.choice(["40001", "08001", "23505"])
            }
        elif svc == "infra-eks-core":
            return {
                "PodName": f"{svc}-{random.randint(1, 5)}-{self.fake.bothify(text='?????')}",
                "NodeIP": self.fake.ipv4_private(),
                "CPU_Usage": f"{random.randint(80, 100)}%",
                "Mem_Usage": f"{random.randint(85, 100)}%"
            }
        return {}

    def generate_incident(self):
        """핀테크 연쇄 장애 시나리오 (Knowledge Base 기반)"""
        incident_id = f"FIN-{str(uuid.uuid4())[:5].upper()}"
        attacker_ip = self.fake.ipv4()
        
        # 1. 보안 공격 시작
        self.write_log("WARN", "auth-security-svc", 
            f"Security Alert - [{incident_id}] Suspicious traffic.", 
            {"ClientIP": attacker_ip, "ThreatLevel": "Medium"}
        )
        time.sleep(0.5)
        
        self.write_log("ERROR", "auth-security-svc", 
            f"Security Alert - [{incident_id}] High rate of JWT validation failures.", 
            {"ClientIP": attacker_ip, "FailCount": "150/s", "AuthMethod": "Bearer"}
        )
        time.sleep(1)

        # 2. DB 연결 고갈
        self.write_log("ERROR", "db-cache-cluster", 
            f"[{incident_id}] HikariPool-1 - Connection is not available, request timed out.", 
            {"WaitTime": "30000ms", "ActiveConnections": "50/50", "QueueSize": "200"}
        )
        time.sleep(1)

        # 3. 결제 실패
        self.write_log("CRITICAL", "payment-gateway", 
            f"[{incident_id}] External PG Timeout. Circuit Breaker: OPEN.", 
            {"CircuitState": "Open", "FailRate": "85%", "LastSuccess": "20s ago"}
        )

    def run(self):
        print(f"🔥 CALI Fintech Simulator Running... (Context Expanded)")
        while True:
            dice = random.random()
            
            # A. [1%] 로그 폭주 (DDoS / Brute Force 테스트)
            if dice < 0.01:
                target_ip = self.fake.ipv4()
                # 1. 메시지 고정
                raw_msg = random.choice(self.kb_errors["auth-security-svc"])
                msg = raw_msg.format(ip=target_ip, user="admin")
                
                # 2. 컨텍스트도 고정 (같은 공격이니까)
                ctx = {"ClientIP": target_ip, "Action": "BruteForce", "TargetUser": "admin"}
                
                print(f"⚠️  Burst Mode: Attack from {target_ip} (30 identical logs)")
                for _ in range(30):
                    self.write_log("WARN", "auth-security-svc", msg, ctx)
                time.sleep(1)

            # B. [5%] 치명적 연쇄 장애 (Incident)
            elif dice < 0.06:
                self.generate_incident()
            
            # C. [20%] 일반 에러 (Knowledge Base에서 랜덤 추출)
            elif dice < 0.26:
                svc = random.choice(list(self.services.keys()))
                if svc in self.kb_errors:
                    raw_msg = random.choice(self.kb_errors[svc])
                    try:
                        msg = raw_msg.format(
                            ip=self.fake.ipv4(), 
                            user=self.fake.user_name(), 
                            uuid=str(uuid.uuid4())[:8]
                        )
                    except:
                        msg = raw_msg
                    
                    # 랜덤 컨텍스트 생성
                    extra = self.generate_context(svc)
                    self.write_log("ERROR", svc, f"Process Failed: {msg}", extra)
            
            # D. [74%] 정상 로그
            else:
                svc = random.choice(list(self.services.keys()))
                self.write_log("INFO", svc, f"User {self.fake.user_name()} - Action Completed - 200 OK")
            
            time.sleep(random.uniform(1, 2.5))

if __name__ == "__main__":
    CALIIncidentSimulator().run()