"""
상수 정의 모듈
하드코딩된 문자열을 상수로 관리
"""
from enum import Enum


class DataSource(str, Enum):
    """데이터 소스 타입"""
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    NEWS = "news"
    BLOG = "blog"


class SentimentType(str, Enum):
    """감정 타입"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ChangeType(str, Enum):
    """변화 유형"""
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


# 기본 설정값
DEFAULT_HOURS = 24
DEFAULT_MAX_RESULTS = 10
DEFAULT_REALTIME_INTERVAL = 5  # 분

# UI 메시지
MESSAGES = {
    'NO_KEYWORD': "키워드를 입력해주세요.",
    'NO_SOURCE': "최소 하나의 소스를 선택해주세요.",
    'NO_DATA': "데이터가 없습니다.",
    'ANALYSIS_COMPLETE': "분석 완료",
    'COLLECTION_COMPLETE': "데이터 수집 완료",
}

