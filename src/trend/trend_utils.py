"""
트렌드 분석 유틸리티 모듈
"""
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import load_config
from .time_series import TimeSeriesAnalyzer
from .change_detection import ChangeDetector
from .simple_change_detector import SimpleChangeDetector
from .advanced_change_detectors import CUSUMDetector, ZScoreDetector, BayesianChangeDetector
from .advanced_change_detectors import CUSUMDetector, ZScoreDetector, BayesianChangeDetector


class TrendAnalyzer:
    """
    트렌드 분석 통합 클래스
    """
    
    def __init__(self, config_path: str = "configs/config_trend.yaml"):
        """
        트렌드 분석기 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config = load_config(config_path)
        
        # 시계열 분석기 초기화
        time_series_config = self.config.get("time_series", {})
        self.time_series_analyzer = TimeSeriesAnalyzer(
            aggregation_window=time_series_config.get("aggregation_window", "1h")
        )
        
        # 변화 탐지기 초기화 (고급 알고리즘 지원)
        change_config = self.config.get("change_detection", {})
        method = change_config.get("method", "simple")  # simple, cusum, zscore, bayesian, advanced
        
        if method == "cusum":
            self.change_detector = CUSUMDetector(
                threshold=change_config.get("cusum_threshold", 5.0),
                drift=change_config.get("drift", 0.5)
            )
        elif method == "zscore":
            self.change_detector = ZScoreDetector(
                z_threshold=change_config.get("z_threshold", 2.5),
                window_size=change_config.get("window_size", 10)
            )
        elif method == "bayesian":
            self.change_detector = BayesianChangeDetector(
                prior_probability=change_config.get("prior_probability", 0.01),
                min_segment_length=change_config.get("min_segment_length", 5)
            )
        elif method == "advanced":
            # 고급 ChangeDetector 사용
            self.change_detector = ChangeDetector(
                method=change_config.get("advanced_method", "pelt"),
                min_size=change_config.get("min_size", 2),
                penalty=change_config.get("penalty", 10),
                threshold=change_config.get("threshold", 0.3)
            )
        else:
            # 기본: SimpleChangeDetector 사용
            self.change_detector = SimpleChangeDetector(
                window_minutes=change_config.get("window_minutes", 10),
                threshold=change_config.get("threshold", 0.3)
            )
        
        # 알림 설정
        alert_config = self.config.get("alerts", {})
        self.alerts_enabled = alert_config.get("enabled", True)
        self.alert_threshold = alert_config.get("threshold_change_rate", 0.5)
    
    def analyze_trend(self, sentiment_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        트렌드 분석 수행
        
        Args:
            sentiment_data: 감정 분석 결과 리스트
            
        Returns:
            트렌드 분석 결과 딕셔너리
        """
        # 시계열 집계
        aggregated_df = self.time_series_analyzer.aggregate_sentiment(sentiment_data)
        
        if aggregated_df.empty:
            return {
                "trend_direction": "stable",
                "change_points": [],
                "alerts": []
            }
        
        # 감정 스코어 계산
        aggregated_df['sentiment_score'] = aggregated_df.apply(
            lambda row: self.time_series_analyzer.calculate_sentiment_score(
                row['positive_score'],
                row['negative_score'],
                row['neutral_score']
            ),
            axis=1
        )
        
        # 트렌드 방향 판단
        scores = aggregated_df['sentiment_score'].tolist()
        trend_direction = self.time_series_analyzer.get_trend_direction(scores)
        
        # 변화점 탐지 (모든 탐지기 지원)
        if isinstance(self.change_detector, 
                     (SimpleChangeDetector, CUSUMDetector, ZScoreDetector, BayesianChangeDetector)):
            # 리스트 형태로 변환
            sentiment_list = aggregated_df.to_dict('records')
            change_points_data = self.change_detector.detect_changes(sentiment_list)
            # 변화점 datetime 변환 (안전하게 처리)
            change_points = []
            for cp in change_points_data:
                if isinstance(cp, dict) and 'change_point' in cp:
                    try:
                        cp_dt = datetime.fromisoformat(cp['change_point'])
                        change_points.append(cp_dt)
                    except (ValueError, TypeError) as e:
                        # ISO 형식이 아닌 경우 무시
                        continue
        else:
            # 기존 ChangeDetector 사용
            change_points = self.change_detector.detect_change_points(
                aggregated_df,
                value_column="sentiment_score"
            )
        
        # 알림 생성
        alerts = []
        if self.alerts_enabled and change_points:
            alerts = self._generate_alerts(aggregated_df, change_points)
        
        return {
            "trend_direction": trend_direction,
            "change_points": [cp.isoformat() for cp in change_points],
            "alerts": alerts,
            "aggregated_data": aggregated_df.to_dict('records')
        }
    
    def _generate_alerts(self, aggregated_df: pd.DataFrame, 
                        change_points: List) -> List[Dict[str, Any]]:
        """
        변화점 기반 알림 생성
        
        Args:
            aggregated_df: 집계된 데이터프레임
            change_points: 변화점 리스트
            
        Returns:
            알림 리스트
        """
        alerts = []
        
        for cp in change_points:
            # 변화점 이전/이후 데이터 추출 (analyzed_at 컬럼 사용)
            if 'analyzed_at' in aggregated_df.columns:
                before_data = aggregated_df[pd.to_datetime(aggregated_df['analyzed_at']) < cp]
                after_data = aggregated_df[pd.to_datetime(aggregated_df['analyzed_at']) >= cp]
            else:
                # 인덱스가 datetime인 경우
                before_data = aggregated_df[aggregated_df.index < cp]
                after_data = aggregated_df[aggregated_df.index >= cp]
            
            if before_data.empty or after_data.empty:
                continue
            
            before_scores = before_data['sentiment_score'].tolist()
            after_scores = after_data['sentiment_score'].tolist()
            
            # 변화율 계산 (SimpleChangeDetector는 calculate_change_rate가 없을 수 있음)
            if hasattr(self.change_detector, 'calculate_change_rate'):
                change_rate = self.change_detector.calculate_change_rate(before_scores, after_scores)
            else:
                # 간단한 변화율 계산
                before_mean = np.mean(before_scores) if before_scores else 0
                after_mean = np.mean(after_scores) if after_scores else 0
                change_rate = ((after_mean - before_mean) / (abs(before_mean) + 1e-8)) * 100
            
            # 임계값 초과 시 알림 생성
            if abs(change_rate) >= self.alert_threshold * 100:
                change_type = "increase" if change_rate > 0 else "decrease"
                
                alert = {
                    "change_point": cp.isoformat(),
                    "change_type": change_type,
                    "change_rate": abs(change_rate),
                    "previous_sentiment": float(np.mean(before_scores)),
                    "current_sentiment": float(np.mean(after_scores))
                }
                alerts.append(alert)
        
        return alerts

