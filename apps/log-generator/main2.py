import logging
import random
import sys
import time
from datetime import datetime

# 로그 포맷 설정 (Fluent Bit Regex와 일치: YYYY-MM-DD HH:MM:SS)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)

logger = logging.getLogger("test-generator")


def cause_error():
    try:
        # 10% 확률로 에러 발생 (멀티라인 로그 생성)
        x = 1 / 0
    except ZeroDivisionError:
        logger.error("Something went wrong!", exc_info=True)


def main():
    logger.info("Starting Log Generator for Multiline Testing...")

    while True:
        # 90% 정상 로그
        if random.random() > 0.1:
            logger.info(f"Processing item #{random.randint(1000, 9999)}")
        else:
            # 10% 에러 로그 (Stacktrace 포함)
            cause_error()

        time.sleep(1.0)


if __name__ == "__main__":
    main()
