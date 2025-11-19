"""
간단한 변화 감지 알고리즘 (v0)
10분 단위 평균 감정 점수 계산 → 직전 구간 대비 변화율 계산 → 임계값 초과 시 변화점으로 판단

알고리즘:
1. 감정 데이터를 시간 윈도우(기본 10분)로 그룹화
2. 각 윈도우의 평균 감정 점수 계산
3. 직전 윈도우 대비 변화율 계산: |curr_score - prev_score| / |prev_score|
4. 변화율이 임계값(기본 0.3)을 초과하면 변화점으로 판단

향후 v1에서는 ruptures 라이브러리의 전문 알고리즘(PELT, Binseg, Dynp) 사용 예정
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta


class SimpleChangeDetector:
    """
    간단한 변화 감지 클래스 (v0)
    """
    
    def __init__(self, window_minutes: int = 10, threshold: float = 0.3):
        """
        변화 감지기 초기화
        
        Args:
            window_minutes: 집계 시간 단위 (분)
            threshold: 변화 감지 임계값 (변화율)
        """
        self.window_minutes = window_minutes
        self.threshold = threshold
    
    def detect_changes(self, sentiment_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        감정 데이터에서 변화점 탐지
        
        Args:
            sentiment_data: 감정 분석 결과 리스트 (analyzed_at, positive_score, negative_score, neutral_score 포함)
            
        Returns:
            변화점 리스트
        """
        if not sentiment_data or len(sentiment_data) < 2:
            return []
        
        # 데이터프레임 생성
        df = pd.DataFrame(sentiment_data)
        df['analyzed_at'] = pd.to_datetime(df['analyzed_at'])
        
        # 감정 스코어 계산 (-1 ~ 1)
        df['sentiment_score'] = df.apply(
            lambda row: self._calculate_sentiment_score(
                row['positive_score'],
                row['negative_score'],
                row['neutral_score']
            ),
            axis=1
        )
        
        # 시간 단위로 집계
        df_grouped = self._aggregate_by_window(df)
        
        if len(df_grouped) < 2:
            return []
        
        # 변화점 탐지
        change_points = []
        
        for i in range(1, len(df_grouped)):
            prev_score = df_grouped.iloc[i-1]['mean_sentiment']
            curr_score = df_grouped.iloc[i]['mean_sentiment']
            prev_time = df_grouped.iloc[i-1]['time_window']
            curr_time = df_grouped.iloc[i]['time_window']
            
            # 변화율 계산
            if abs(prev_score) > 0.01:  # 0으로 나누기 방지
                change_rate = abs(curr_score - prev_score) / abs(prev_score)
            else:
                change_rate = abs(curr_score - prev_score)
            
            # 임계값 초과 시 변화점으로 판단
            if change_rate > self.threshold:
                change_points.append({
                    "change_point": curr_time.isoformat(),
                    "previous_score": float(prev_score),
                    "current_score": float(curr_score),
                    "change_rate": float(change_rate),
                    "change_type": "increase" if curr_score > prev_score else "decrease",
                    "window_start": prev_time.isoformat(),
                    "window_end": curr_time.isoformat()
                })
        
        return change_points
    
    def _aggregate_by_window(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        시간 단위로 감정 점수 집계
        
        Args:
            df: 감정 데이터프레임
            
        Returns:
            집계된 데이터프레임
        """
        # 시간 윈도우 생성
        df['time_window'] = df['analyzed_at'].dt.floor(f'{self.window_minutes}min')
        
        # 집계
        grouped = df.groupby('time_window').agg({
            'sentiment_score': ['mean', 'std', 'count']
        }).reset_index()
        
        grouped.columns = ['time_window', 'mean_sentiment', 'std_sentiment', 'count']
        
        # 결측값 처리
        grouped = grouped.fillna(0)
        
        return grouped
    
    def _calculate_sentiment_score(self, positive: float, negative: float, neutral: float) -> float:
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
    
    def get_trend_summary(self, sentiment_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        트렌드 요약 정보 반환
        
        Args:
            sentiment_data: 감정 분석 결과 리스트
            
        Returns:
            트렌드 요약 딕셔너리
        """
        if not sentiment_data:
            return {
                "total_count": 0,
                "avg_sentiment": 0.0,
                "trend_direction": "stable",
                "change_points": []
            }
        
        # 변화점 탐지
        change_points = self.detect_changes(sentiment_data)
        
        # 평균 감정 점수 계산
        scores = []
        for item in sentiment_data:
            score = self._calculate_sentiment_score(
                item.get('positive_score', 0),
                item.get('negative_score', 0),
                item.get('neutral_score', 0)
            )
            scores.append(score)
        
        avg_sentiment = np.mean(scores) if scores else 0.0
        
        # 트렌드 방향 판단
        if len(scores) >= 2:
            # 선형 회귀로 트렌드 계산
            x = np.arange(len(scores))
            slope = np.polyfit(x, scores, 1)[0]
            
            if slope > 0.01:
                trend_direction = "increasing"
            elif slope < -0.01:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "stable"
        
        return {
            "total_count": len(sentiment_data),
            "avg_sentiment": float(avg_sentiment),
            "trend_direction": trend_direction,
            "change_points_count": len(change_points),
            "change_points": change_points
        }

