"""
감정 분석 유틸리티 모듈
감정 분석 실행 및 결과 처리 함수
"""
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any

from src.database.db_manager import get_db_session
from src.database.models import SentimentAnalysis
from src.sentiment.sentiment_utils import SentimentAnalyzer
from src.preprocessing.text_cleaner import TextCleaner
from app.utils.db_queries import get_unanalyzed_texts
from app.utils.logger_config import sentiment_logger as logger


def run_sentiment_analysis(keyword: str, source: str, hours: int = 24) -> Tuple[bool, int]:
    """
    감정 분석 실행
    
    Args:
        keyword: 검색 키워드
        source: 데이터 소스
        hours: 분석 기간 (시간)
    
    Returns:
        (성공 여부, 분석된 개수) 튜플
    """
    try:
        # 분석할 텍스트 조회
        texts_to_analyze = get_unanalyzed_texts(keyword, source, hours)
        
        if not texts_to_analyze:
            return True, 0
        
        # 감정 분석 수행
        sentiment_analyzer = SentimentAnalyzer()
        text_cleaner = TextCleaner()
        
        analyzed_count = 0
        
        with get_db_session() as db:
            for text_obj in texts_to_analyze:
                try:
                    cleaned_text = text_cleaner.clean_text_for_sentiment(text_obj.text)
                    if not cleaned_text or len(cleaned_text.strip()) < 5:
                        continue
                    
                    result = sentiment_analyzer.analyze(cleaned_text)
                    
                    sentiment_obj = SentimentAnalysis(
                        text_id=text_obj.id,
                        keyword=text_obj.keyword,
                        source=text_obj.source,
                        positive_score=result['positive_score'],
                        negative_score=result['negative_score'],
                        neutral_score=result['neutral_score'],
                        predicted_sentiment=result['predicted_sentiment'],
                        model_type=result.get('model_type', 'unknown'),
                        analyzed_at=datetime.utcnow()
                    )
                    db.add(sentiment_obj)
                    analyzed_count += 1
                except Exception as e:
                    logger.warning(f"텍스트 분석 실패 (ID: {text_obj.id}): {e}")
                    continue
            
            db.commit()
        
        return True, analyzed_count
    except Exception as e:
        logger.error(f"감정 분석 실행 실패: {e}", exc_info=True)
        return False, str(e)


def calculate_sentiment_statistics(sentiments: list) -> Dict[str, Any]:
    """
    감정 분석 결과 통계 계산
    
    Args:
        sentiments: SentimentAnalysis 객체 리스트
    
    Returns:
        통계 딕셔너리
    """
    from collections import defaultdict
    
    sentiment_counts = defaultdict(int)
    total_positive = 0
    total_negative = 0
    total_neutral = 0
    
    for sent in sentiments:
        sentiment_counts[sent.predicted_sentiment] += 1
        total_positive += sent.positive_score
        total_negative += sent.negative_score
        total_neutral += sent.neutral_score
    
    count = len(sentiments)
    if count == 0:
        return {
            'count': 0,
            'sentiment_counts': {},
            'avg_positive': 0,
            'avg_negative': 0,
            'avg_neutral': 0,
            'overall_sentiment': 0
        }
    
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

