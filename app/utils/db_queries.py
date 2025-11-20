"""
데이터베이스 조회 함수 모듈
DB 쿼리 로직을 중앙화하여 재사용성과 유지보수성 향상
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.database.db_manager import get_db_session
from src.database.models import SentimentAnalysis, CollectedText


def get_sentiment_data(keyword: str, source: str, hours: int = 24) -> List[Dict[str, Any]]:
    """
    감정 분석 데이터 조회
    
    Args:
        keyword: 검색 키워드
        source: 데이터 소스 (youtube, twitter, news, blog)
        hours: 조회 기간 (시간)
    
    Returns:
        감정 분석 데이터 리스트
    """
    with get_db_session() as db:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.keyword == keyword,
            SentimentAnalysis.source == source,
            SentimentAnalysis.analyzed_at >= start_time
        ).order_by(SentimentAnalysis.analyzed_at).all()
        
        data = []
        for s in sentiments:
            data.append({
                "analyzed_at": s.analyzed_at,
                "positive_score": s.positive_score,
                "negative_score": s.negative_score,
                "neutral_score": s.neutral_score,
                "predicted_sentiment": s.predicted_sentiment,
                "text_id": s.text_id
            })
        
        return data


def get_video_data(keyword: str) -> List[Dict[str, Any]]:
    """
    YouTube 비디오 정보 조회
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        비디오 정보 리스트
    """
    with get_db_session() as db:
        videos = db.query(CollectedText).filter(
            CollectedText.keyword == keyword,
            CollectedText.source == "youtube",
            CollectedText.video_id.isnot(None)
        ).distinct(CollectedText.video_id).all()
        
        video_dict = {}
        for video in videos:
            video_id = video.video_id
            if video_id and video_id not in video_dict:
                video_dict[video_id] = {
                    "video_id": video_id,
                    "title": video.video_title or "제목 없음",
                    "channel_name": video.channel_name or "채널명 없음",
                    "view_count": video.view_count or 0,
                    "like_count": video.like_count or 0,
                    "url": video.url or f"https://www.youtube.com/watch?v={video_id}"
                }
        
        return list(video_dict.values())


def get_comments_by_keyword(keyword: str) -> List[CollectedText]:
    """
    키워드로 댓글 조회
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        댓글 리스트
    """
    with get_db_session() as db:
        return db.query(CollectedText).filter(
            CollectedText.keyword == keyword
        ).all()


def get_comments_by_video(keyword: str, video_id: str) -> List[CollectedText]:
    """
    특정 비디오의 댓글 조회
    
    Args:
        keyword: 검색 키워드
        video_id: 비디오 ID
    
    Returns:
        댓글 리스트
    """
    with get_db_session() as db:
        return db.query(CollectedText).filter(
            CollectedText.keyword == keyword,
            CollectedText.video_id == video_id
        ).order_by(CollectedText.collected_at.desc()).all()


def get_sentiments_by_keyword(keyword: str, source: Optional[str] = None) -> List[SentimentAnalysis]:
    """
    키워드로 감정 분석 결과 조회
    
    Args:
        keyword: 검색 키워드
        source: 데이터 소스 (선택사항)
    
    Returns:
        감정 분석 결과 리스트
    """
    with get_db_session() as db:
        query = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.keyword == keyword
        )
        if source:
            query = query.filter(SentimentAnalysis.source == source)
        return query.order_by(SentimentAnalysis.analyzed_at).all()


def get_sentiments_by_text_ids(text_ids: List[int]) -> Dict[int, SentimentAnalysis]:
    """
    텍스트 ID 리스트로 감정 분석 결과 조회
    
    Args:
        text_ids: 텍스트 ID 리스트
    
    Returns:
        {text_id: SentimentAnalysis} 딕셔너리
    """
    if not text_ids:
        return {}
    
    with get_db_session() as db:
        sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.text_id.in_(text_ids)
        ).all()
        return {sent.text_id: sent for sent in sentiments}


def get_unanalyzed_texts(keyword: str, source: str, hours: int = 24) -> List[CollectedText]:
    """
    아직 분석되지 않은 텍스트 조회
    
    Args:
        keyword: 검색 키워드
        source: 데이터 소스
        hours: 조회 기간 (시간)
    
    Returns:
        분석되지 않은 텍스트 리스트
    """
    with get_db_session() as db:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 이미 분석된 텍스트 ID 조회
        analyzed_text_ids = db.query(SentimentAnalysis.text_id).filter(
            SentimentAnalysis.keyword == keyword,
            SentimentAnalysis.source == source
        ).subquery()
        
        # 분석할 텍스트 조회
        return db.query(CollectedText).filter(
            CollectedText.keyword == keyword,
            CollectedText.source == source,
            CollectedText.collected_at >= start_time,
            ~CollectedText.id.in_(analyzed_text_ids)
        ).all()

