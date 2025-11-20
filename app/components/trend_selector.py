"""
트렌드 분석 알고리즘 선택 컴포넌트
사용자가 알고리즘을 선택할 수 있는 UI 컴포넌트
"""
import streamlit as st
from typing import Optional


def render_algorithm_selector() -> Optional[str]:
    """
    알고리즘 선택 UI 렌더링
    
    Returns:
        선택된 알고리즘 이름 또는 None
    """
    st.sidebar.markdown("### 🔬 트렌드 분석 알고리즘")
    
    algorithm = st.sidebar.selectbox(
        "변화점 탐지 방법",
        options=[
            "simple",      # SimpleChangeDetector
            "cusum",      # CUSUM
            "zscore",     # Z-score
            "bayesian"    # Bayesian
        ],
        index=0,
        format_func=lambda x: {
            "simple": "📊 간단한 방법 (기본)",
            "cusum": "📈 CUSUM (누적 합)",
            "zscore": "📉 Z-score (통계적 이상치)",
            "bayesian": "🧠 Bayesian (베이지안)"
        }.get(x, x),
        help="변화점 탐지에 사용할 알고리즘을 선택하세요."
    )
    
    if algorithm != "simple":
        st.sidebar.info(f"**{algorithm.upper()}** 알고리즘이 선택되었습니다.")
    
    return algorithm

