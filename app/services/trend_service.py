"""
트렌드 분석 서비스
트렌드 분석 및 변화점 탐지 로직 통합
고급 알고리즘 지원: CUSUM, Z-score, Bayesian
"""
from typing import List, Dict, Any, Optional

from src.trend.trend_utils import TrendAnalyzer
from src.trend.simple_change_detector import SimpleChangeDetector
from src.trend.advanced_change_detectors import CUSUMDetector, ZScoreDetector, BayesianChangeDetector
from app.utils.logger_config import trend_logger as logger


def analyze_trend_with_change_points(
    sentiment_list: List[Dict[str, Any]], 
    method: Optional[str] = None
) -> Dict[str, Any]:
    """
    트렌드 분석 및 변화점 탐지 (고급 알고리즘 지원)
    
    Args:
        sentiment_list: 감정 분석 결과 리스트
        method: 탐지 방법 (simple, cusum, zscore, bayesian) - None이면 설정 파일 사용
    
    Returns:
        트렌드 분석 결과 딕셔너리
    """
    try:
        trend_analyzer = TrendAnalyzer()
        
        # 특정 방법 지정 시 임시로 변경
        if method and method in ["cusum", "zscore", "bayesian"]:
            if method == "cusum":
                trend_analyzer.change_detector = CUSUMDetector()
            elif method == "zscore":
                trend_analyzer.change_detector = ZScoreDetector()
            elif method == "bayesian":
                trend_analyzer.change_detector = BayesianChangeDetector()
        
        trend_result = trend_analyzer.analyze_trend(sentiment_list)
        
        change_points_data = trend_result.get("change_points", [])
        alerts = trend_result.get("alerts", [])
        
        # 상세 정보 가져오기 (고급 탐지기 지원)
        if isinstance(trend_analyzer.change_detector, 
                     (SimpleChangeDetector, CUSUMDetector, ZScoreDetector, BayesianChangeDetector)):
            change_points_detail = trend_analyzer.change_detector.detect_changes(sentiment_list)
            # ISO 문자열 리스트로 변환
            change_points_data = [cp['change_point'] for cp in change_points_detail]
            alerts = change_points_detail
        
        return {
            "change_points": change_points_data,
            "alerts": alerts,
            "trend_result": trend_result,
            "method": method or "config_default"
        }
    except Exception as e:
        logger.error(f"트렌드 분석 실패: {e}", exc_info=True)
        return {
            "change_points": [],
            "alerts": [],
            "trend_result": {},
            "method": method or "config_default"
        }

