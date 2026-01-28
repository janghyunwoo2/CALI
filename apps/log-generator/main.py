import random
import time
import uuid
import os
from datetime import datetime
from faker import Faker

class CALIIncidentSimulator:
    def __init__(self):
        self.fake = Faker()
        self.services = {
            "auth-service": "v3.1.0",
            "order-service": "v1.8.4",
            "payment-api": "v2.3.1"
        }
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, "logs")
        self.log_file = os.path.join(self.log_dir, "app.log")
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def get_ts(self):
        # return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def write_log(self, level, svc, msg):
        ver = self.services[svc]
        tid = str(uuid.uuid4())[:8]
        log_line = f"[{level}] {self.get_ts()} {svc}/{ver} [{tid}]: {msg}\n"
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
            f.flush()
        print(log_line.strip())

    def generate_incident(self):
        """통합 시나리오: 결제 시스템 연쇄 장애 (도미노 효과)"""
        incident_id = f"INC-{str(uuid.uuid4())[:5].upper()}"
        
        # 1단계: 보안/인증 (JWT 폭주)
        self.write_log("ERROR", "auth-service", 
            f"Security Alert - [{incident_id}] High rate of JWT validation failures from IP {self.fake.ipv4()}. Potential Brute Force or Traffic Surge.")
        time.sleep(1)

        # 2단계: 데이터베이스 (Connection Pool 고갈 & Stack Trace)
        db_error_msg = (
            f"[{incident_id}] HikariPool-1 - Connection is not available.\n"
            "org.hibernate.exception.GenericJDBCException: Unable to acquire JDBC Connection\n"
            "\tat org.hibernate.exception.internal.StandardSQLExceptionConverter.convert(StandardSQLExceptionConverter.java:42)\n"
            "\tat org.springframework.orm.jpa.vendor.HibernateJpaDialect.convertHibernateAccessException(HibernateJpaDialect.java:318)"
        )
        self.write_log("ERROR", "order-service", db_error_msg)
        time.sleep(1)

        # 3단계: 외부 연동 (Stripe 타임아웃 & 서킷 브레이커 OPEN)
        self.write_log("ERROR", "payment-api", 
            f"[{incident_id}] External PG(Stripe) Timeout. Response time > 5000ms. Circuit Breaker State: OPEN. All transactions blocked.")

    def run(self):
        print(f"🔥 CALI Incident Simulator Running... (8:2 Ratio)")
        while True:
            dice = random.random()
            
            if dice < 0.05:  # 5% 확률로 연쇄 장애 발생 (시나리오)
                self.generate_incident()
            elif dice < 0.25: # 20% 확률로 일반 에러
                svc = random.choice(list(self.services.keys()))
                self.write_log("ERROR", svc, f"Unexpected system error: {self.fake.sentence()}")
            else: # 75% 정상 로그
                svc = random.choice(list(self.services.keys()))
                self.write_log("INFO", svc, f"User {self.fake.user_name()} - API {self.fake.uri_path()} - 200 OK")
            
            time.sleep(random.uniform(1, 3))

if __name__ == "__main__":
    CALIIncidentSimulator().run()
