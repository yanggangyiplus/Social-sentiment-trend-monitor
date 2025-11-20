"""
캐시 관리 모듈
Delta update 방식의 캐싱 전략 구현
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import json


class CacheManager:
    """
    검색 시점 기준 캐싱 및 Delta Update 관리
    """
    
    @staticmethod
    def get_cache_key(keyword: str, source: str, hours: int) -> str:
        """
        캐시 키 생성
        
        Args:
            keyword: 검색 키워드
            source: 데이터 소스
            hours: 조회 기간
        
        Returns:
            캐시 키 문자열
        """
        key_string = f"{keyword}_{source}_{hours}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def get_last_checkpoint(keyword: str, source: str) -> Optional[datetime]:
        """
        마지막 데이터 수집 시점 조회
        
        Args:
            keyword: 검색 키워드
            source: 데이터 소스
        
        Returns:
            마지막 체크포인트 datetime 또는 None
        """
        cache_key = f"checkpoint_{keyword}_{source}"
        checkpoint_str = st.session_state.get(cache_key)
        if checkpoint_str:
            try:
                return datetime.fromisoformat(checkpoint_str)
            except Exception:
                return None
        return None
    
    @staticmethod
    def update_checkpoint(keyword: str, source: str, checkpoint: datetime):
        """
        마지막 데이터 수집 시점 업데이트
        
        Args:
            keyword: 검색 키워드
            source: 데이터 소스
            checkpoint: 체크포인트 datetime
        """
        cache_key = f"checkpoint_{keyword}_{source}"
        st.session_state[cache_key] = checkpoint.isoformat()
    
    @staticmethod
    def get_cached_data(keyword: str, source: str, hours: int) -> Optional[Any]:
        """
        캐시된 데이터 조회
        
        Args:
            keyword: 검색 키워드
            source: 데이터 소스
            hours: 조회 기간
        
        Returns:
            캐시된 데이터 또는 None
        """
        cache_key = CacheManager.get_cache_key(keyword, source, hours)
        return st.session_state.get(f"cache_{cache_key}")
    
    @staticmethod
    def set_cached_data(keyword: str, source: str, hours: int, data: Any):
        """
        데이터 캐싱
        
        Args:
            keyword: 검색 키워드
            source: 데이터 소스
            hours: 조회 기간
            data: 캐싱할 데이터
        """
        cache_key = CacheManager.get_cache_key(keyword, source, hours)
        st.session_state[f"cache_{cache_key}"] = data
    
    @staticmethod
    def should_use_delta_update(keyword: str, source: str, max_age_minutes: int = 5) -> bool:
        """
        Delta update 사용 여부 결정
        
        Args:
            keyword: 검색 키워드
            source: 데이터 소스
            max_age_minutes: 캐시 최대 유효 시간 (분)
        
        Returns:
            Delta update 사용 여부
        """
        checkpoint = CacheManager.get_last_checkpoint(keyword, source)
        if checkpoint is None:
            return False
        
        age_minutes = (datetime.now() - checkpoint).total_seconds() / 60
        return age_minutes < max_age_minutes

