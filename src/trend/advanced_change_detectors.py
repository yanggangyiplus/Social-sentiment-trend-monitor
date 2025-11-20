"""
고급 변화점 탐지 알고리즘
CUSUM, Z-score, Bayesian Change Point Detection 구현
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CUSUMDetector:
    """
    CUSUM (Cumulative Sum) 기반 변화점 탐지
    누적 합을 사용하여 평균의 변화를 감지
    """
    
    def __init__(self, threshold: float = 5.0, drift: float = 0.5):
        """
        CUSUM 탐지기 초기화
        
        Args:
            threshold: 변화 감지 임계값 (h)
            drift: 드리프트 파라미터 (k)
        """
        self.threshold = threshold
        self.drift = drift
    
    def detect_changes(self, sentiment_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        CUSUM 알고리즘으로 변화점 탐지
        
        Args:
            sentiment_data: 감정 분석 결과 리스트
        
        Returns:
            변화점 리스트
        """
        if not sentiment_data or len(sentiment_data) < 3:
            return []
        
        try:
            # 데이터프레임 생성
            df = pd.DataFrame(sentiment_data)
            df['analyzed_at'] = pd.to_datetime(df['analyzed_at'])
            df = df.sort_values('analyzed_at')
            
            # 감정 스코어 계산
            df['sentiment_score'] = df.apply(
                lambda row: self._calculate_sentiment_score(
                    row['positive_score'],
                    row['negative_score'],
                    row['neutral_score']
                ),
                axis=1
            )
            
            scores = df['sentiment_score'].values
            timestamps = df['analyzed_at'].values
            
            # CUSUM 계산
            change_points = self._cusum_detect(scores, timestamps)
            
            return change_points
            
        except Exception as e:
            logger.error(f"CUSUM 탐지 실패: {e}", exc_info=True)
            return []
    
    def _cusum_detect(self, values: np.ndarray, timestamps: np.ndarray) -> List[Dict[str, Any]]:
        """
        CUSUM 알고리즘 실행
        
        Args:
            values: 값 배열
            timestamps: 타임스탬프 배열
        
        Returns:
            변화점 리스트
        """
        if len(values) < 3:
            return []
        
        # 평균 및 표준편차 계산
        mean = np.mean(values)
        std = np.std(values)
        
        if std < 1e-8:
            return []
        
        # 정규화
        normalized = (values - mean) / std
        
        # CUSUM 통계량 계산
        n = len(normalized)
        S_plus = np.zeros(n)
        S_minus = np.zeros(n)
        
        for i in range(1, n):
            S_plus[i] = max(0, S_plus[i-1] + normalized[i] - self.drift)
            S_minus[i] = max(0, S_minus[i-1] - normalized[i] - self.drift)
        
        # 변화점 탐지
        change_points = []
        for i in range(1, n):
            if S_plus[i] > self.threshold or S_minus[i] > self.threshold:
                # 변화 방향 결정
                if S_plus[i] > self.threshold:
                    change_type = "increase"
                    change_magnitude = S_plus[i]
                else:
                    change_type = "decrease"
                    change_magnitude = S_minus[i]
                
                # 이전 값과 현재 값 비교
                prev_idx = max(0, i - 5)  # 이전 5개 평균
                curr_idx = min(n - 1, i + 5)  # 이후 5개 평균
                
                prev_score = np.mean(values[prev_idx:i])
                curr_score = np.mean(values[i:curr_idx])
                
                change_points.append({
                    "change_point": pd.Timestamp(timestamps[i]).isoformat(),
                    "previous_score": float(prev_score),
                    "current_score": float(curr_score),
                    "change_rate": float(abs(curr_score - prev_score) / (abs(prev_score) + 1e-8)),
                    "change_type": change_type,
                    "change_magnitude": float(change_magnitude),
                    "method": "CUSUM"
                })
        
        return change_points
    
    def _calculate_sentiment_score(self, positive: float, negative: float, neutral: float) -> float:
        """감정 점수 계산"""
        return positive * 1.0 + neutral * 0.0 + negative * (-1.0)


class ZScoreDetector:
    """
    Z-score 기반 변화점 탐지
    통계적 이상치 탐지를 통한 변화점 감지
    """
    
    def __init__(self, z_threshold: float = 2.5, window_size: int = 10):
        """
        Z-score 탐지기 초기화
        
        Args:
            z_threshold: Z-score 임계값 (표준편차 단위)
            window_size: 이동 윈도우 크기
        """
        self.z_threshold = z_threshold
        self.window_size = window_size
    
    def detect_changes(self, sentiment_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Z-score 알고리즘으로 변화점 탐지
        
        Args:
            sentiment_data: 감정 분석 결과 리스트
        
        Returns:
            변화점 리스트
        """
        if not sentiment_data or len(sentiment_data) < self.window_size + 1:
            return []
        
        try:
            # 데이터프레임 생성
            df = pd.DataFrame(sentiment_data)
            df['analyzed_at'] = pd.to_datetime(df['analyzed_at'])
            df = df.sort_values('analyzed_at')
            
            # 감정 스코어 계산
            df['sentiment_score'] = df.apply(
                lambda row: self._calculate_sentiment_score(
                    row['positive_score'],
                    row['negative_score'],
                    row['neutral_score']
                ),
                axis=1
            )
            
            scores = df['sentiment_score'].values
            timestamps = df['analyzed_at'].values
            
            # Z-score 계산 및 변화점 탐지
            change_points = self._zscore_detect(scores, timestamps)
            
            return change_points
            
        except Exception as e:
            logger.error(f"Z-score 탐지 실패: {e}", exc_info=True)
            return []
    
    def _zscore_detect(self, values: np.ndarray, timestamps: np.ndarray) -> List[Dict[str, Any]]:
        """
        Z-score 알고리즘 실행
        
        Args:
            values: 값 배열
            timestamps: 타임스탬프 배열
        
        Returns:
            변화점 리스트
        """
        n = len(values)
        if n < self.window_size + 1:
            return []
        
        change_points = []
        
        # 이동 윈도우로 Z-score 계산
        for i in range(self.window_size, n - self.window_size):
            # 이전 윈도우 (기준)
            prev_window = values[i - self.window_size:i]
            prev_mean = np.mean(prev_window)
            prev_std = np.std(prev_window)
            
            if prev_std < 1e-8:
                continue
            
            # 현재 윈도우
            curr_window = values[i:i + self.window_size]
            curr_mean = np.mean(curr_window)
            
            # Z-score 계산
            z_score = abs(curr_mean - prev_mean) / prev_std
            
            if z_score > self.z_threshold:
                # 변화 방향 결정
                change_type = "increase" if curr_mean > prev_mean else "decrease"
                
                change_points.append({
                    "change_point": pd.Timestamp(timestamps[i]).isoformat(),
                    "previous_score": float(prev_mean),
                    "current_score": float(curr_mean),
                    "change_rate": float(abs(curr_mean - prev_mean) / (abs(prev_mean) + 1e-8)),
                    "change_type": change_type,
                    "z_score": float(z_score),
                    "method": "Z-score"
                })
        
        return change_points
    
    def _calculate_sentiment_score(self, positive: float, negative: float, neutral: float) -> float:
        """감정 점수 계산"""
        return positive * 1.0 + neutral * 0.0 + negative * (-1.0)


class BayesianChangeDetector:
    """
    Bayesian Change Point Detection
    베이지안 방법론을 사용한 변화점 탐지
    """
    
    def __init__(self, prior_probability: float = 0.01, min_segment_length: int = 5):
        """
        Bayesian 탐지기 초기화
        
        Args:
            prior_probability: 변화점 사전 확률
            min_segment_length: 최소 세그먼트 길이
        """
        self.prior_prob = prior_probability
        self.min_segment_length = min_segment_length
    
    def detect_changes(self, sentiment_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bayesian 알고리즘으로 변화점 탐지
        
        Args:
            sentiment_data: 감정 분석 결과 리스트
        
        Returns:
            변화점 리스트
        """
        if not sentiment_data or len(sentiment_data) < self.min_segment_length * 2:
            return []
        
        try:
            # 데이터프레임 생성
            df = pd.DataFrame(sentiment_data)
            df['analyzed_at'] = pd.to_datetime(df['analyzed_at'])
            df = df.sort_values('analyzed_at')
            
            # 감정 스코어 계산
            df['sentiment_score'] = df.apply(
                lambda row: self._calculate_sentiment_score(
                    row['positive_score'],
                    row['negative_score'],
                    row['neutral_score']
                ),
                axis=1
            )
            
            scores = df['sentiment_score'].values
            timestamps = df['analyzed_at'].values
            
            # Bayesian 변화점 탐지
            change_points = self._bayesian_detect(scores, timestamps)
            
            return change_points
            
        except Exception as e:
            logger.error(f"Bayesian 탐지 실패: {e}", exc_info=True)
            return []
    
    def _bayesian_detect(self, values: np.ndarray, timestamps: np.ndarray) -> List[Dict[str, Any]]:
        """
        Bayesian Change Point Detection 실행
        
        Args:
            values: 값 배열
            timestamps: 타임스탬프 배열
        
        Returns:
            변화점 리스트
        """
        n = len(values)
        if n < self.min_segment_length * 2:
            return []
        
        # 변화점 확률 계산
        change_probs = self._calculate_change_probabilities(values)
        
        # 임계값 이상인 지점을 변화점으로 선택
        threshold = self.prior_prob * 2  # 사전 확률의 2배
        change_indices = np.where(change_probs > threshold)[0]
        
        # 최소 세그먼트 길이 제약 적용
        filtered_indices = []
        last_idx = -self.min_segment_length
        
        for idx in change_indices:
            if idx - last_idx >= self.min_segment_length:
                filtered_indices.append(idx)
                last_idx = idx
        
        # 변화점 정보 생성
        change_points = []
        for idx in filtered_indices:
            if idx < self.min_segment_length or idx >= n - self.min_segment_length:
                continue
            
            # 이전 세그먼트 평균
            prev_start = max(0, idx - self.min_segment_length)
            prev_score = np.mean(values[prev_start:idx])
            
            # 현재 세그먼트 평균
            curr_end = min(n, idx + self.min_segment_length)
            curr_score = np.mean(values[idx:curr_end])
            
            change_type = "increase" if curr_score > prev_score else "decrease"
            change_rate = abs(curr_score - prev_score) / (abs(prev_score) + 1e-8)
            
            change_points.append({
                "change_point": pd.Timestamp(timestamps[idx]).isoformat(),
                "previous_score": float(prev_score),
                "current_score": float(curr_score),
                "change_rate": float(change_rate),
                "change_type": change_type,
                "posterior_probability": float(change_probs[idx]),
                "method": "Bayesian"
            })
        
        return change_points
    
    def _calculate_change_probabilities(self, values: np.ndarray) -> np.ndarray:
        """
        각 지점에서 변화점일 확률 계산
        
        Args:
            values: 값 배열
        
        Returns:
            변화점 확률 배열
        """
        n = len(values)
        probs = np.zeros(n)
        
        # 전체 평균 및 분산
        overall_mean = np.mean(values)
        overall_var = np.var(values)
        
        if overall_var < 1e-8:
            return probs
        
        # 각 지점에서 변화점일 가능성 평가
        for i in range(self.min_segment_length, n - self.min_segment_length):
            # 이전 세그먼트
            prev_segment = values[i - self.min_segment_length:i]
            prev_mean = np.mean(prev_segment)
            prev_var = np.var(prev_segment)
            
            # 이후 세그먼트
            next_segment = values[i:i + self.min_segment_length]
            next_mean = np.mean(next_segment)
            next_var = np.var(next_segment)
            
            # 베이지안 확률 계산 (간단한 버전)
            # 두 세그먼트의 평균 차이가 클수록 높은 확률
            mean_diff = abs(next_mean - prev_mean)
            normalized_diff = mean_diff / (np.sqrt(overall_var) + 1e-8)
            
            # 사전 확률과 우도 결합
            likelihood = 1 / (1 + np.exp(-normalized_diff))  # 시그모이드 함수
            posterior = self.prior_prob * likelihood / (self.prior_prob * likelihood + (1 - self.prior_prob) * (1 - likelihood))
            
            probs[i] = posterior
        
        return probs
    
    def _calculate_sentiment_score(self, positive: float, negative: float, neutral: float) -> float:
        """감정 점수 계산"""
        return positive * 1.0 + neutral * 0.0 + negative * (-1.0)

