"""
시계열 분석 모듈
"""
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
import numpy as np


class TimeSeriesAnalyzer:
    """
    시계열 분석 클래스
    """
    
    def __init__(self, aggregation_window: str = "1h"):
        """
        시계열 분석기 초기화
        
        Args:
            aggregation_window: 집계 시간 단위 ("1h", "6h", "1d" 등)
        """
        self.aggregation_window = aggregation_window
    
    def aggregate_sentiment(self, sentiment_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        감정 데이터를 시간 단위로 집계
        
        Args:
            sentiment_data: 감정 분석 결과 리스트 (analyzed_at, positive_score, negative_score, neutral_score 포함)
            
        Returns:
            시간별 집계된 감정 데이터프레임
        """
        if not sentiment_data:
            return pd.DataFrame()
        
        # 데이터프레임 생성
        df = pd.DataFrame(sentiment_data)
        
        # analyzed_at을 datetime으로 변환
        df['analyzed_at'] = pd.to_datetime(df['analyzed_at'])
        
        # 시간 단위로 그룹화
        df_grouped = df.groupby(pd.Grouper(key='analyzed_at', freq=self.aggregation_window)).agg({
            'positive_score': 'mean',
            'negative_score': 'mean',
            'neutral_score': 'mean'
        }).reset_index()
        
        # 결측값 처리
        df_grouped = df_grouped.fillna(0)
        
        return df_grouped
    
    def calculate_sentiment_score(self, positive: float, negative: float, neutral: float) -> float:
        """
        감정 점수를 단일 스코어로 변환 (-1 ~ 1)
        
        Args:
            positive: 긍정 점수
            negative: 부정 점수
            neutral: 중립 점수
            
        Returns:
            감정 스코어 (-1: 매우 부정적, 0: 중립, 1: 매우 긍정적)
        """
        # 가중 평균 계산
        score = positive * 1.0 + neutral * 0.0 + negative * (-1.0)
        return score
    
    def get_trend_direction(self, scores: List[float]) -> str:
        """
        트렌드 방향 판단
        
        Args:
            scores: 감정 스코어 리스트
            
        Returns:
            트렌드 방향 ("increasing", "decreasing", "stable")
        """
        if len(scores) < 2:
            return "stable"
        
        # 선형 회귀를 사용한 트렌드 계산
        x = np.arange(len(scores))
        slope = np.polyfit(x, scores, 1)[0]
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"

