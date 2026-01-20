"""
=====================================================
서비스 테스트
=====================================================
설명: Throttler 등 주요 서비스 로직 테스트
=====================================================
"""

import pytest
from datetime import datetime, timedelta

from utils.throttle import Throttler


def test_throttler_allows_first_alert():
    """첫 번째 알림은 허용되어야 함"""
    throttler = Throttler(window_seconds=60, max_alerts=3)
    
    assert throttler.should_send_alert("test-key") is True


def test_throttler_blocks_after_max():
    """최대 횟수 초과 시 차단되어야 함"""
    throttler = Throttler(window_seconds=60, max_alerts=3)
    
    # 3번까지 허용
    for _ in range(3):
        assert throttler.should_send_alert("test-key") is True
    
    # 4번째는 차단
    assert throttler.should_send_alert("test-key") is False


def test_throttler_resets_after_window():
    """윈도우 시간 경과 후 리셋되어야 함"""
    throttler = Throttler(window_seconds=1, max_alerts=2)
    
    # 2번 허용
    assert throttler.should_send_alert("test-key") is True
    assert throttler.should_send_alert("test-key") is True
    
    # 3번째 차단
    assert throttler.should_send_alert("test-key") is False
    
    # TODO: 시간 경과 후 테스트 (mock 사용 필요)


# TODO: 추가 테스트 케이스 작성
