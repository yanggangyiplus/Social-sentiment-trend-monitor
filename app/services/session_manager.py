"""
세션 상태 관리 모듈
Streamlit session_state 초기화 및 관리
"""
import streamlit as st
from datetime import datetime
from typing import Optional, List


def init_session_state():
    """
    세션 상태 초기화 (한 곳에서 통합 관리)
    rerun 시에도 기존 값을 유지하도록 주의
    """
    # 실시간 모니터링 관련 (기존 값 유지)
    if 'realtime_monitoring' not in st.session_state:
        st.session_state.realtime_monitoring = False
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = None
    if 'monitoring_keyword' not in st.session_state:
        st.session_state.monitoring_keyword = None
    if 'monitoring_sources' not in st.session_state:
        st.session_state.monitoring_sources = []
    
    # 현재 검색 관련 (기존 값 유지)
    if 'current_keyword' not in st.session_state:
        st.session_state.current_keyword = None
    if 'current_source' not in st.session_state:
        st.session_state.current_source = "youtube"
    
    # 캐시 관련 (기존 값 유지)
    if 'use_cache' not in st.session_state:
        st.session_state.use_cache = False


def should_use_cache() -> bool:
    """
    캐시 사용 여부 결정
    실시간 모니터링 중일 때는 캐시 사용하지 않음
    """
    return not st.session_state.get('realtime_monitoring', False)


def update_monitoring_state(keyword: Optional[str], sources: List[str]):
    """
    모니터링 상태 업데이트
    """
    st.session_state.monitoring_keyword = keyword
    st.session_state.monitoring_sources = sources.copy() if sources else []
    st.session_state.last_update_time = datetime.now()

