"""
변화 탐지 모듈
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime


class ChangeDetector:
    """
    변화 탐지 클래스
    """
    
    def __init__(self, method: str = "pelt", min_size: int = 2, 
                 penalty: float = 10, threshold: float = 0.3):
        """
        변화 탐지기 초기화
        
        Args:
            method: 탐지 방법 ("pelt" or "window")
            min_size: 최소 세그먼트 크기
            penalty: 페널티 파라미터
            threshold: 변화 감지 임계값
        """
        self.method = method
        self.min_size = min_size
        self.penalty = penalty
        self.threshold = threshold
    
    def detect_change_points(self, time_series: pd.DataFrame, 
                            value_column: str = "sentiment_score") -> List[datetime]:
        """
        시계열 데이터에서 변화점 탐지
        
        Args:
            time_series: 시계열 데이터프레임 (datetime 인덱스 또는 analyzed_at 컬럼 필요)
            value_column: 분석할 값 컬럼명
            
        Returns:
            변화점 datetime 리스트
        """
        if time_series.empty or value_column not in time_series.columns:
            return []
        
        # 시계열 데이터 준비
        if 'analyzed_at' in time_series.columns:
            time_series = time_series.set_index('analyzed_at')
        
        values = time_series[value_column].values
        
        if len(values) < self.min_size * 2:
            return []
        
        change_points = []
        
        if self.method == "pelt":
            change_points = self._detect_pelt(values, time_series.index)
        elif self.method == "window":
            change_points = self._detect_window(values, time_series.index)
        else:
            change_points = self._detect_simple(values, time_series.index)
        
        return change_points
    
    def _detect_simple(self, values: np.ndarray, timestamps: pd.DatetimeIndex) -> List[datetime]:
        """
        간단한 변화 탐지 (이동 평균 기반)
        
        Args:
            values: 값 배열
            timestamps: 타임스탬프 인덱스
            
        Returns:
            변화점 datetime 리스트
        """
        change_points = []
        
        if len(values) < 3:
            return change_points
        
        # 이동 평균 계산
        window_size = max(3, len(values) // 10)
        moving_avg = pd.Series(values).rolling(window=window_size, center=True).mean()
        
        # 표준편차 계산
        std = np.std(values)
        
        # 변화 감지
        for i in range(1, len(values) - 1):
            prev_avg = moving_avg.iloc[i-1] if not pd.isna(moving_avg.iloc[i-1]) else values[i-1]
            curr_avg = moving_avg.iloc[i] if not pd.isna(moving_avg.iloc[i]) else values[i]
            
            change_rate = abs(curr_avg - prev_avg) / (std + 1e-8)
            
            if change_rate > self.threshold:
                change_points.append(timestamps[i])
        
        return change_points
    
    def _detect_pelt(self, values: np.ndarray, timestamps: pd.DatetimeIndex) -> List[datetime]:
        """
        PELT 알고리즘 기반 변화 탐지 (간단한 구현)
        
        Args:
            values: 값 배열
            timestamps: 타임스탬프 인덱스
            
        Returns:
            변화점 datetime 리스트
        """
        # 실제 PELT 구현은 더 복잡하므로, 여기서는 간단한 버전 사용
        return self._detect_simple(values, timestamps)
    
    def _detect_window(self, values: np.ndarray, timestamps: pd.DatetimeIndex) -> List[datetime]:
        """
        윈도우 기반 변화 탐지
        
        Args:
            values: 값 배열
            timestamps: 타임스탬프 인덱스
            
        Returns:
            변화점 datetime 리스트
        """
        change_points = []
        window_size = max(self.min_size, len(values) // 10)
        
        for i in range(window_size, len(values) - window_size):
            prev_window = values[i - window_size:i]
            curr_window = values[i:i + window_size]
            
            prev_mean = np.mean(prev_window)
            curr_mean = np.mean(curr_window)
            std = np.std(values)
            
            change_rate = abs(curr_mean - prev_mean) / (std + 1e-8)
            
            if change_rate > self.threshold:
                change_points.append(timestamps[i])
        
        return change_points
    
    def calculate_change_rate(self, before_values: List[float], 
                             after_values: List[float]) -> float:
        """
        변화율 계산
        
        Args:
            before_values: 변화 이전 값들
            after_values: 변화 이후 값들
            
        Returns:
            변화율 (%)
        """
        if not before_values or not after_values:
            return 0.0
        
        before_mean = np.mean(before_values)
        after_mean = np.mean(after_values)
        
        if before_mean == 0:
            return 0.0
        
        change_rate = ((after_mean - before_mean) / abs(before_mean)) * 100
        return change_rate

