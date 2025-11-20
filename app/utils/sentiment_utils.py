"""
감정 분석 유틸리티 함수
중복 계산 제거 및 통계 함수
"""
from typing import Dict, List
from collections import defaultdict


def calculate_sentiment_statistics_from_dict(sentiments_dict: Dict) -> Dict:
    """
    감정 분석 결과 딕셔너리에서 통계 계산 (중복 제거)
    
    Args:
        sentiments_dict: {text_id: SentimentAnalysis} 딕셔너리
    
    Returns:
        통계 딕셔너리
    """
    if not sentiments_dict:
        return {
            'count': 0,
            'sentiment_counts': {},
            'avg_positive': 0,
            'avg_negative': 0,
            'avg_neutral': 0,
            'overall_sentiment': 0
        }
    
    sentiment_counts = defaultdict(int)
    total_positive = 0
    total_negative = 0
    total_neutral = 0
    
    for sent in sentiments_dict.values():
        sentiment_counts[sent.predicted_sentiment] += 1
        total_positive += sent.positive_score
        total_negative += sent.negative_score
        total_neutral += sent.neutral_score
    
    count = len(sentiments_dict)
    avg_positive = total_positive / count
    avg_negative = total_negative / count
    avg_neutral = total_neutral / count
    overall_sentiment = avg_positive - avg_negative
    
    return {
        'count': count,
        'sentiment_counts': dict(sentiment_counts),
        'avg_positive': avg_positive,
        'avg_negative': avg_negative,
        'avg_neutral': avg_neutral,
        'overall_sentiment': overall_sentiment
    }

