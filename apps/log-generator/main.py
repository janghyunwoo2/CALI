#!/usr/bin/env python3
"""
=====================================================
프로덕션급 로그 시뮬레이터
=====================================================
설명: 실제 운영 환경의 에러 패턴을 시뮬레이션
용도:
  - 본 프로젝트 데모 및 테스트
  - Fluent Bit 파서 검증
  - AI 분석 학습 데이터 생성
출력: stdout (실제 애플리케이션 로그 형식)
=====================================================
"""

import random
import sys
import time
from datetime import datetime
from typing import Dict, List

from faker import Faker


class ProductionLogSimulator:
    """실제 운영 환경의 로그를 시뮬레이션하는 클래스"""

    def __init__(self):
        # Faker 인스턴스 생성
        self.fake = Faker()

        # 실제 마이크로서비스 아키텍처 시뮬레이션
        self.services = {
            "payment-api": {
                "version": "v2.3.1",
                "instances": ["payment-api-7d8f9c-abc123", "payment-api-7d8f9c-def456"],
            },
            "order-service": {
                "version": "v1.8.4",
                "instances": [
                    "order-service-5k2m3n-xyz789",
                    "order-service-5k2m3n-uvw012",
                ],
            },
            "auth-service": {
                "version": "v3.1.0",
                "instances": [
                    "auth-service-9p4q5r-ghi345",
                    "auth-service-9p4q5r-jkl678",
                ],
            },
            "inventory-service": {
                "version": "v2.1.5",
                "instances": [
                    "inventory-service-6t7u8v-mno901",
                    "inventory-service-6t7u8v-pqr234",
                ],
            },
            "notification-service": {
                "version": "v1.5.2",
                "instances": [
                    "notification-service-3w4x5y-stu567",
                    "notification-service-3w4x5y-vwx890",
                ],
            },
            "user-profile-api": {
                "version": "v2.0.3",
                "instances": [
                    "user-profile-api-8z9a1b-yza123",
                    "user-profile-api-8z9a1b-bcd456",
                ],
            },
            "analytics-engine": {
                "version": "v1.2.7",
                "instances": [
                    "analytics-engine-2c3d4e-efg789",
                    "analytics-engine-2c3d4e-hij012",
                ],
            },
        }

        # 실제 프로덕션 환경에서 발생하는 에러 시나리오
        self.error_scenarios = [
            {
                "type": "database",
                "message": "Connection pool exhausted: unable to acquire connection within 30s timeout",
                "details": "HikariCP connection pool size: 20/20 active, 100 waiting threads",
                "exception": "java.sql.SQLTransientConnectionException",
                "recovery": "Auto-retry enabled, circuit breaker: OPEN",
            },
            {
                "type": "payment",
                "message": "Payment gateway timeout: no response from provider within 15s",
                "details": "Transaction ID: TXN-20260119-ABC123, Amount: $459.99, Provider: Stripe",
                "exception": "com.stripe.exception.ApiConnectionException",
                "recovery": "Transaction rolled back, refund initiated",
            },
            {
                "type": "cache",
                "message": "Redis connection refused: unable to connect to redis-cluster-master:6379",
                "details": "Cluster status: 2/3 nodes available, failover in progress",
                "exception": "redis.exceptions.ConnectionError",
                "recovery": "Fallback to database, cache warming scheduled",
            },
            {
                "type": "api",
                "message": "External API rate limit exceeded: 1000 requests/minute quota reached",
                "details": "API: partner-api.example.com, Retry-After: 42s, Current rate: 1247 req/min",
                "exception": "org.springframework.web.client.HttpClientErrorException$TooManyRequests",
                "recovery": "Request queued, exponential backoff applied",
            },
            {
                "type": "auth",
                "message": "JWT token validation failed: signature verification error",
                "details": "Token issuer: auth-service, Algorithm: RS256, Key ID mismatch",
                "exception": "io.jsonwebtoken.security.SignatureException",
                "recovery": "User session invalidated, re-authentication required",
            },
            {
                "type": "inventory",
                "message": "Stock synchronization failed: pessimistic lock timeout after 10s",
                "details": "SKU: PROD-8472, Requested: 5, Available: 2, Waitlist: 15 customers",
                "exception": "org.hibernate.exception.LockAcquisitionException",
                "recovery": "Transaction rolled back, stock reservation cancelled",
            },
            {
                "type": "message_queue",
                "message": "Kafka consumer lag critical: 50000 messages behind, offset lag increasing",
                "details": "Topic: order-events, Partition: 3, Consumer group: order-processor-group",
                "exception": "org.apache.kafka.common.errors.TimeoutException",
                "recovery": "Scaling consumer instances: 3 → 6, partition rebalance triggered",
            },
            {
                "type": "memory",
                "message": "OutOfMemory: Metaspace exhausted, unable to load classes",
                "details": "Metaspace: 245MB/256MB used, Classes loaded: 18432, GC: 15 Full GC in 5min",
                "exception": "java.lang.OutOfMemoryError: Metaspace",
                "recovery": "Pod restart triggered, Metaspace limit increased to 512MB",
            },
        ]

        # 정상 동작 메시지
        self.info_messages = [
            "Order processed successfully: ORDER-{} (${:.2f}, 3 items)",
            "User authentication completed: user-{} from IP {}.{}.{}.{}",
            "Payment confirmed: TXN-{} via {} (${:.2f})",
            "Cache hit rate: {:.1f}% ({}ms avg response time)",
            "Inventory updated: SKU-{} stock: {} → {} units",
            "Email notification sent: {} to user-{} (delivered in {}ms)",
            "API request completed: GET /api/v1/users/{} ({}ms, 200 OK)",
            "Database query executed: {} rows returned in {}ms",
        ]

    def get_timestamp(self) -> str:
        """ISO 8601 형식 타임스탬프 생성"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    def get_service_info(self, service_name: str) -> Dict:
        """서비스 정보 및 인스턴스 선택"""
        service = self.services[service_name]
        return {
            "name": service_name,
            "version": service["version"],
            "instance": random.choice(service["instances"]),
        }

    def generate_info_log(self) -> str:
        """정상 동작 로그 생성"""
        service_name = random.choice(list(self.services.keys()))
        service = self.get_service_info(service_name)
        template = random.choice(self.info_messages)

        # 템플릿에 맞는 데이터 생성
        if "ORDER-" in template:
            msg = template.format(
                self.fake.ean(length=8),
                self.fake.pydecimal(left_digits=3, right_digits=2, positive=True),
            )
        elif "user-" in template and "IP" in template:
            msg = template.format(self.fake.user_name(), *self.fake.ipv4().split("."))
        elif "TXN-" in template:
            msg = template.format(
                self.fake.uuid4()[:13],
                random.choice(["Stripe", "PayPal", "Square"]),
                self.fake.pydecimal(left_digits=3, right_digits=2, positive=True),
            )
        elif "Cache hit" in template:
            msg = template.format(random.uniform(85, 99), random.randint(5, 50))
        elif "SKU-" in template:
            old_stock = random.randint(10, 100)
            msg = template.format(
                self.fake.ean(length=8), old_stock, old_stock - random.randint(1, 5)
            )
        elif "Email" in template:
            msg = template.format(
                random.choice(["order_confirmation", "password_reset", "welcome"]),
                self.fake.user_name(),
                random.randint(50, 500),
            )
        elif "GET /api" in template:
            msg = template.format(self.fake.uuid4()[:8], random.randint(10, 200))
        else:
            msg = template.format(random.randint(10, 1000), random.randint(5, 100))

        return f"[INFO] {self.get_timestamp()} {service['name']}/{service['version']}: {msg}"

    def generate_warn_log(self) -> str:
        """경고 로그 생성"""
        service_name = random.choice(list(self.services.keys()))
        service = self.get_service_info(service_name)

        warnings = [
            f"Response time degraded: p95={random.randint(800, 2000)}ms (SLA: 500ms)",
            f"Memory usage high: {random.randint(75, 90)}% of {random.choice([512, 1024, 2048])}MB limit",
            f"Connection pool low: {random.randint(1, 3)}/{random.randint(10, 20)} connections available",
            f"Disk usage warning: {random.randint(80, 90)}% used on /var/log",
            f"Rate limiting approaching: {random.randint(800, 950)}/1000 requests in current window",
            f"Circuit breaker half-open: testing downstream service health",
            f"Slow query detected: {random.randint(5, 15)}s execution time (threshold: 3s)",
        ]

        return f"[WARN] {self.get_timestamp()} {service['name']}/{service['version']}: {random.choice(warnings)}"

    def generate_error_log(self) -> str:
        """실제 프로덕션 에러 로그 생성 (Multiline 스택 트레이스 포함)"""
        service_name = random.choice(list(self.services.keys()))
        service = self.get_service_info(service_name)
        scenario = random.choice(self.error_scenarios)

        # 서비스별 적절한 스택 트레이스 생성
        if "java" in scenario["exception"].lower():
            stack_trace = self._generate_java_stacktrace(service, scenario)
        else:
            stack_trace = self._generate_python_stacktrace(service, scenario)

        return stack_trace

    def _generate_java_stacktrace(self, service: Dict, scenario: Dict) -> str:
        """Java 스타일 상세 스택 트레이스"""
        package = service["name"].replace("-", ".")

        return f"""[ERROR] {self.get_timestamp()} {service["name"]}/{service["version"]} pod/{service["instance"]}: {scenario["message"]}
Details: {scenario["details"]}
Recovery Action: {scenario["recovery"]}
{scenario["exception"]}: {scenario["message"]}
    at com.cali.{package}.service.BusinessService.executeTransaction(BusinessService.java:{random.randint(100, 500)})
    at com.cali.{package}.controller.ApiController.handleRequest(ApiController.java:{random.randint(50, 150)})
    at jdk.internal.reflect.GeneratedMethodAccessor{random.randint(100, 999)}.invoke(Unknown Source)
    at jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:{random.randint(40, 50)})
    at java.lang.reflect.Method.invoke(Method.java:{random.randint(500, 600)})
    at org.springframework.web.method.support.InvocableHandlerMethod.doInvoke(InvocableHandlerMethod.java:{random.randint(150, 250)})
    at org.springframework.web.servlet.mvc.method.annotation.ServletInvocableHandlerMethod.invokeAndHandle(ServletInvocableHandlerMethod.java:{random.randint(100, 150)})
    at org.springframework.web.servlet.DispatcherServlet.doDispatch(DispatcherServlet.java:{random.randint(900, 1100)})
Caused by: {self._get_caused_by_exception(scenario["type"])}
    at {self._get_database_driver()}.connect({self._get_driver_file()}:{random.randint(100, 400)})
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:{random.randint(150, 200)})
    ... {random.randint(15, 30)} more
Thread: http-nio-8080-exec-{random.randint(1, 50)}, Request: POST /api/v1/{random.choice(["orders", "payments", "users"])}/{random.randint(1000, 9999)}"""

    def _generate_python_stacktrace(self, service: Dict, scenario: Dict) -> str:
        """Python 스타일 상세 스택 트레이스"""
        module = service["name"].replace("-", "_")

        return f"""ERROR: {service["name"]}/{service["version"]} pod/{service["instance"]} {scenario["message"]}
Details: {scenario["details"]}
Recovery Action: {scenario["recovery"]}
Traceback (most recent call last):
  File "/app/main.py", line {random.randint(50, 100)}, in <module>
    app.run()
  File "/app/{module}/application.py", line {random.randint(100, 200)}, in run
    self.process_request(request)
  File "/app/{module}/handlers.py", line {random.randint(50, 150)}, in process_request
    result = self.execute_business_logic(data)
  File "/app/{module}/services.py", line {random.randint(200, 400)}, in execute_business_logic
    return self.database.query(sql, params)
  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/base.py", line {random.randint(1000, 2000)}, in execute
    return self._execute_context(...)
  File "/usr/local/lib/python3.11/site-packages/psycopg2/__init__.py", line {random.randint(100, 300)}, in connect
    raise OperationalError(...)
{scenario["exception"]}: {scenario["message"]}
Request ID: req-{random.randint(100000, 999999)}, User ID: user-{random.randint(1000, 9999)}, Correlation ID: {self._generate_correlation_id()}"""

    def _get_caused_by_exception(self, error_type: str) -> str:
        """에러 타입별 원인 예외"""
        exceptions = {
            "database": "org.postgresql.util.PSQLException: Connection refused",
            "payment": "java.net.SocketTimeoutException: Read timed out",
            "cache": "redis.clients.jedis.exceptions.JedisConnectionException: Connection reset",
            "api": "org.apache.http.conn.HttpHostConnectException: Connect to api.example.com:443 timed out",
            "auth": "java.security.InvalidKeyException: Key is invalid",
            "inventory": "javax.persistence.PessimisticLockException: could not execute statement",
            "message_queue": "org.apache.kafka.common.errors.DisconnectException: Connection to node -1 could not be established",
            "memory": "java.lang.OutOfMemoryError: Java heap space",
        }
        return exceptions.get(error_type, "java.lang.RuntimeException: Unknown error")

    def _get_database_driver(self) -> str:
        """데이터베이스 드라이버"""
        return random.choice(
            [
                "org.postgresql.jdbc.PgConnection",
                "com.mysql.cj.jdbc.ConnectionImpl",
                "oracle.jdbc.driver.OracleDriver",
            ]
        )

    def _get_driver_file(self) -> str:
        """드라이버 파일명"""
        files = {
            "org.postgresql.jdbc.PgConnection": "PgConnection.java",
            "com.mysql.cj.jdbc.ConnectionImpl": "ConnectionImpl.java",
            "oracle.jdbc.driver.OracleDriver": "OracleDriver.java",
        }
        driver = self._get_database_driver()
        return files.get(driver, "Driver.java")

    def _generate_correlation_id(self) -> str:
        """분산 추적 Correlation ID"""
        import uuid

        return str(uuid.uuid4())[:18]

    def run(self, interval: float = 2.0, error_rate: float = 0.3):
        """
        프로덕션 수준 로그를 주기적으로 생성

        Args:
            interval: 로그 생성 간격 (초)
            error_rate: 에러 로그 발생 비율 (0.0 ~ 1.0)
        """
        print(
            f"[INFO] Production log simulator started (error_rate={error_rate}, interval={interval}s)",
            flush=True,
        )
        print(
            f"[INFO] Simulating {len(self.services)} microservices in production environment",
            flush=True,
        )

        try:
            while True:
                rand = random.random()

                if rand < error_rate:
                    # 에러 로그 (상세 스택 트레이스)
                    log = self.generate_error_log()
                elif rand < error_rate + 0.15:
                    # 경고 로그
                    log = self.generate_warn_log()
                else:
                    # 정상 로그
                    log = self.generate_info_log()

                print(log, flush=True)
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n[INFO] Shutting down production log simulator...", flush=True)
            sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="프로덕션급 로그 시뮬레이터")
    parser.add_argument(
        "--interval", type=float, default=2.0, help="로그 생성 간격 (초, 기본값: 2.0)"
    )
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.3,
        help="에러 로그 발생 비율 (0.0 ~ 1.0, 기본값: 0.3)",
    )

    args = parser.parse_args()

    simulator = ProductionLogSimulator()
    simulator.run(interval=args.interval, error_rate=args.error_rate)
