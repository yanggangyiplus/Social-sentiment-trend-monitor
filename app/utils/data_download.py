"""
데이터 다운로드 유틸리티 모듈
CSV 파일 생성 및 다운로드 함수
"""
import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

from app.utils.db_queries import (
    get_comments_by_keyword,
    get_sentiments_by_keyword,
    get_sentiments_by_text_ids
)
from src.database.models import CollectedText, SentimentAnalysis


def generate_comments_csv(keyword: str) -> bytes:
    """
    원본 댓글 데이터 CSV 생성
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        CSV 바이트 데이터
    """
    comments_data = get_comments_by_keyword(keyword)
    
    if not comments_data:
        return b""
    
    comments_df = pd.DataFrame([{
        "키워드": c.keyword,
        "소스": c.source,
        "댓글": c.text,
        "작성자": c.author or "",
        "URL": c.url or "",
        "수집일시": c.collected_at.strftime("%Y-%m-%d %H:%M:%S") if c.collected_at else "",
        "영상제목": c.video_title or "",
        "채널명": c.channel_name or "",
        "조회수": c.view_count or 0,
        "좋아요": c.like_count or 0
    } for c in comments_data])
    
    csv_buffer = io.StringIO()
    comments_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    return csv_buffer.getvalue().encode('utf-8-sig')


def generate_sentiment_csv(keyword: str) -> bytes:
    """
    감정 분석 결과 CSV 생성
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        CSV 바이트 데이터
    """
    sentiments_data = get_sentiments_by_keyword(keyword)
    
    if not sentiments_data:
        return b""
    
    # 텍스트 ID 리스트 추출
    text_ids = [sent.text_id for sent in sentiments_data]
    
    # 원본 텍스트 조회
    from app.utils.db_queries import get_comments_by_keyword
    comments = get_comments_by_keyword(keyword)
    comments_dict = {c.id: c for c in comments}
    
    sentiment_list = []
    for sent in sentiments_data:
        text_obj = comments_dict.get(sent.text_id)
        sentiment_list.append({
            "키워드": sent.keyword,
            "소스": sent.source,
            "댓글": text_obj.text if text_obj else "",
            "작성자": text_obj.author if text_obj else "",
            "긍정점수": f"{sent.positive_score:.4f}",
            "부정점수": f"{sent.negative_score:.4f}",
            "중립점수": f"{sent.neutral_score:.4f}",
            "예측감정": sent.predicted_sentiment,
            "모델타입": sent.model_type,
            "분석일시": sent.analyzed_at.strftime("%Y-%m-%d %H:%M:%S") if sent.analyzed_at else ""
        })
    
    sentiments_df = pd.DataFrame(sentiment_list)
    
    csv_buffer = io.StringIO()
    sentiments_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    return csv_buffer.getvalue().encode('utf-8-sig')


def generate_summary_csv(keyword: str) -> bytes:
    """
    통계 요약 CSV 생성
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        CSV 바이트 데이터
    """
    sentiments_data = get_sentiments_by_keyword(keyword)
    
    if not sentiments_data:
        return b""
    
    sentiment_counts = defaultdict(int)
    total_positive = 0
    total_negative = 0
    total_neutral = 0
    
    for sent in sentiments_data:
        sentiment_counts[sent.predicted_sentiment] += 1
        total_positive += sent.positive_score
        total_negative += sent.negative_score
        total_neutral += sent.neutral_score
    
    count = len(sentiments_data)
    avg_positive = total_positive / count if count > 0 else 0
    avg_negative = total_negative / count if count > 0 else 0
    avg_neutral = total_neutral / count if count > 0 else 0
    overall_sentiment = avg_positive - avg_negative
    
    summary_df = pd.DataFrame([{
        "키워드": keyword,
        "총댓글수": count,
        "긍정개수": sentiment_counts.get("positive", 0),
        "부정개수": sentiment_counts.get("negative", 0),
        "중립개수": sentiment_counts.get("neutral", 0),
        "평균긍정점수": f"{avg_positive:.4f}",
        "평균부정점수": f"{avg_negative:.4f}",
        "평균중립점수": f"{avg_neutral:.4f}",
        "전체감정스코어": f"{overall_sentiment:.4f}",
        "생성일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    csv_buffer = io.StringIO()
    summary_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
    return csv_buffer.getvalue().encode('utf-8-sig')

