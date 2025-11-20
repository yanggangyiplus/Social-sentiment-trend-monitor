"""
Rate Limiter 및 Retry 로직
API 호출 안정성 강화
"""
import time
import random
from typing import Callable, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    API Rate Limit 관리 및 Exponential Backoff 구현
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        """
        Rate Limiter 초기화
        
        Args:
            max_retries: 최대 재시도 횟수
            base_delay: 기본 대기 시간 (초)
            max_delay: 최대 대기 시간 (초)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def exponential_backoff(self, attempt: int) -> float:
        """
        Exponential Backoff 계산
        
        Args:
            attempt: 현재 시도 횟수
        
        Returns:
            대기 시간 (초)
        """
        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
        return min(delay, self.max_delay)
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exponential Backoff를 사용한 재시도 로직
        
        Args:
            func: 실행할 함수
            *args: 함수 인자
            **kwargs: 함수 키워드 인자
        
        Returns:
            함수 실행 결과
        
        Raises:
            Exception: 최대 재시도 횟수 초과 시
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # RateLimit 에러인 경우
                if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    if attempt < self.max_retries - 1:
                        delay = self.exponential_backoff(attempt)
                        logger.warning(
                            f"Rate limit 도달. {delay:.2f}초 후 재시도... "
                            f"(시도 {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(delay)
                        continue
                
                # 일반 에러인 경우
                if attempt < self.max_retries - 1:
                    delay = self.exponential_backoff(attempt)
                    logger.warning(
                        f"에러 발생: {str(e)}. {delay:.2f}초 후 재시도... "
                        f"(시도 {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"최대 재시도 횟수 초과. 마지막 에러: {str(e)}")
        
        raise last_exception


def rate_limit_decorator(max_retries: int = 3, base_delay: float = 1.0):
    """
    Rate Limit 및 Retry 데코레이터
    
    Args:
        max_retries: 최대 재시도 횟수
        base_delay: 기본 대기 시간 (초)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = RateLimiter(max_retries=max_retries, base_delay=base_delay)
            return limiter.retry_with_backoff(func, *args, **kwargs)
        return wrapper
    return decorator

