"""
실시간 모니터링 서비스
데이터 수집 및 분석 자동화 로직
"""
from typing import Tuple, List
from datetime import datetime

from src.collectors.collector_manager import CollectorManager
from app.utils import sentiment_analysis, constants
from app.utils.logger_config import collector_logger as logger


def run_data_collection(keyword: str, sources: List[str], max_results: int = 10) -> Tuple[bool, int]:
    """
    데이터 수집 실행
    
    Args:
        keyword: 검색 키워드
        sources: 데이터 소스 리스트
        max_results: 최대 수집 개수
    
    Returns:
        (성공 여부, 수집 개수) 튜플
    """
    try:
        collector_manager = CollectorManager()
        
        # 선택된 소스만 활성화
        enabled_sources = [s for s in sources if s in ["youtube", "twitter", "news", "blog"]]
        
        if not enabled_sources:
            logger.warning(f"데이터 소스가 선택되지 않음: {sources}")
            return False, 0
        
        collected_data = collector_manager.collect_all(
            keyword, 
            max_results, 
            save_to_database=True
        )
        logger.info(f"데이터 수집 완료: {len(collected_data)}개 (키워드: {keyword})")
        return True, len(collected_data)
    except Exception as e:
        logger.error(f"데이터 수집 실패 (키워드: {keyword}): {e}", exc_info=True)
        return False, 0


def auto_collect_and_analyze(keyword: str, sources: List[str], interval_minutes: int = 5) -> Tuple[bool, int]:
    """
    백그라운드에서 자동으로 데이터 수집 및 분석
    
    Args:
        keyword: 검색 키워드
        sources: 데이터 소스 리스트
        interval_minutes: 수집 주기 (분)
    
    Returns:
        (성공 여부, 수집 개수) 튜플
    """
    try:
        # 데이터 수집
        collector_manager = CollectorManager()
        collected_data = collector_manager.collect_all(
            keyword, 
            10,  # 소량만 수집
            save_to_database=True
        )
        
        # 감정 분석 (YouTube만)
        if constants.DataSource.YOUTUBE.value in sources and collected_data:
            success, count = sentiment_analysis.run_sentiment_analysis(
                keyword, 
                constants.DataSource.YOUTUBE.value, 
                24
            )
            if not success:
                logger.warning(f"자동 감정 분석 실패 (키워드: {keyword}): {count}")
        
        logger.info(f"자동 수집 완료: {len(collected_data)}개 (키워드: {keyword})")
        return True, len(collected_data)
    except Exception as e:
        logger.error(f"자동 수집 및 분석 실패 (키워드: {keyword}): {e}", exc_info=True)
        return False, 0

