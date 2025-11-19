"""
데이터베이스 모델 정의
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class CollectedText(Base):
    """
    수집된 텍스트 데이터 모델
    """
    __tablename__ = "collected_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # youtube, twitter, news, blog
    text = Column(Text, nullable=False)
    author = Column(String(200), nullable=True)
    url = Column(String(500), nullable=True)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # YouTube 비디오 정보 (YouTube인 경우)
    video_id = Column(String(50), nullable=True, index=True)
    video_title = Column(String(500), nullable=True)
    channel_name = Column(String(200), nullable=True)
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index('idx_keyword_collected_at', 'keyword', 'collected_at'),
        Index('idx_video_id', 'video_id'),
    )


class SentimentAnalysis(Base):
    """
    감정 분석 결과 모델
    """
    __tablename__ = "sentiment_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    text_id = Column(Integer, nullable=False, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    
    # 감정 점수
    positive_score = Column(Float, nullable=False)
    negative_score = Column(Float, nullable=False)
    neutral_score = Column(Float, nullable=False)
    
    # 예측된 감정 클래스
    predicted_sentiment = Column(String(20), nullable=False)  # positive, negative, neutral
    
    # 모델 정보
    model_type = Column(String(50), nullable=False)  # kobert, llm
    
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_keyword_analyzed_at', 'keyword', 'analyzed_at'),
    )


class TrendAlert(Base):
    """
    트렌드 변화 알림 모델
    """
    __tablename__ = "trend_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(100), nullable=False, index=True)
    change_type = Column(String(20), nullable=False)  # increase, decrease
    change_rate = Column(Float, nullable=False)  # 변화율 (%)
    change_point = Column(DateTime, nullable=False, index=True)
    previous_sentiment = Column(Float, nullable=False)  # 이전 평균 감정 점수
    current_sentiment = Column(Float, nullable=False)  # 현재 평균 감정 점수
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_keyword_change_point', 'keyword', 'change_point'),
    )
