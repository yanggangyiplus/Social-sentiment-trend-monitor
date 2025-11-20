"""
Streamlit 기반 실시간 감정 모니터링 대시보드
키워드 검색 및 소스별 데이터 표시
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import sys
import logging
from collections import defaultdict

# 프로젝트 루트를 경로에 추가
# app/web/web_demo.py -> app/web -> app -> 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import init_database, get_db_session
from src.database.models import SentimentAnalysis, CollectedText
from src.trend.trend_utils import TrendAnalyzer
from src.trend.simple_change_detector import SimpleChangeDetector
from src.collectors.collector_manager import CollectorManager

# 유틸리티 모듈 import
from app.utils import db_queries, visualization, sentiment_analysis, data_download, constants
from app.utils.visualization import (
    calculate_sentiment_score,
    format_number,
    generate_wordcloud,
    create_donut_chart,
    create_gauge_chart,
    create_bar_chart,
    create_trend_chart,
    create_emotion_distribution_chart,
    create_topic_sentiment_chart
)
from app.utils.sentiment_analysis import calculate_sentiment_statistics
from app.utils.sentiment_utils import calculate_sentiment_statistics_from_dict

# 로깅 설정 (모듈별 로그 파일 사용)
from app.utils.logger_config import app_logger as logger

# 페이지 설정
st.set_page_config(
    page_title="Social Sentiment & Trend Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터베이스 초기화
init_database("sqlite:///data/database/sentiment.db")


# 서비스 모듈 import
from app.services import session_manager, monitoring_service, trend_service, youtube_service, emotion_service
from app.components.trend_selector import render_algorithm_selector

# 캐시는 실시간 모니터링이 아닐 때만 사용 (기본값: False)
def get_sentiment_data(keyword: str, source: str, hours: int = 24):
    """감정 분석 데이터 조회 (실시간 모니터링에서는 캐시 사용 안 함)"""
    return db_queries.get_sentiment_data(keyword, source, hours)


def get_video_data(keyword: str):
    """YouTube 비디오 정보 조회 (실시간 모니터링에서는 캐시 사용 안 함)"""
    return db_queries.get_video_data(keyword)


def main():
    """메인 대시보드 함수"""
    st.title("📊 Social Sentiment & Trend Monitor")
    
    # 세션 상태 초기화 (통합 관리)
    session_manager.init_session_state()
    
    # 실시간 모니터링 상태 표시
    if st.session_state.realtime_monitoring:
        status_container = st.container()
        with status_container:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown("🟢 **실시간 모니터링 활성화**")
            with col2:
                if st.session_state.last_update_time:
                    elapsed = (datetime.now() - st.session_state.last_update_time).total_seconds()
                    elapsed_minutes = int(elapsed // 60)
                    elapsed_seconds = int(elapsed % 60)
                    if elapsed_minutes > 0:
                        st.markdown(f"마지막 업데이트: {elapsed_minutes}분 {elapsed_seconds}초 전")
                    else:
                        st.markdown(f"마지막 업데이트: {elapsed_seconds}초 전")
            with col3:
                if st.button("🔄 새로고침", key="refresh_main"):
                    st.cache_data.clear()
                    st.rerun()
    
    st.markdown("---")
    
    # 사이드바
    st.sidebar.title("🔍 검색 설정")
    
    # 키워드 검색
    search_keyword = st.sidebar.text_input(
        "키워드 입력",
        placeholder="예: 영화리뷰, 아이폰, 맥북...",
        key="search_keyword"
    )
    
    # 소스 선택
    st.sidebar.markdown("### 📱 정보 소스 선택")
    source_youtube = st.sidebar.checkbox("YouTube", value=True)
    source_twitter = st.sidebar.checkbox("X (트위터)", value=False)
    source_news = st.sidebar.checkbox("뉴스", value=False)
    source_blog = st.sidebar.checkbox("블로그", value=False)
    
    selected_sources = []
    if source_youtube:
        selected_sources.append("youtube")
    if source_twitter:
        selected_sources.append("twitter")
    if source_news:
        selected_sources.append("news")
    if source_blog:
        selected_sources.append("blog")
    
    # 추후 추가될 서비스 안내
    if source_twitter or source_news or source_blog:
        st.sidebar.info("⚠️ X(트위터), 뉴스, 블로그는 추후 추가될 서비스입니다.")
    
    max_results = st.sidebar.number_input(
        "수집할 데이터 수",
        min_value=5,
        max_value=50,
        value=10,
        step=5
    )
    
    st.sidebar.markdown("---")
    
    # 실시간 모니터링 설정 (검색 버튼 전에 정의)
    st.sidebar.markdown("### ⚡ 실시간 모니터링")
    
    realtime_enabled = st.sidebar.checkbox(
        "실시간 자동 수집 활성화",
        value=st.session_state.realtime_monitoring,
        help="활성화 시 주기적으로 자동으로 데이터를 수집하고 분석합니다."
    )
    
    if realtime_enabled != st.session_state.realtime_monitoring:
        st.session_state.realtime_monitoring = realtime_enabled
        if realtime_enabled:
            st.session_state.monitoring_keyword = search_keyword.strip() if search_keyword else None
            st.session_state.monitoring_sources = selected_sources.copy()
            st.session_state.last_update_time = datetime.now()
            st.sidebar.success("✅ 실시간 모니터링 시작")
        else:
            st.sidebar.info("⏸️ 실시간 모니터링 중지")
    
    st.sidebar.markdown("---")
    
    # 검색 버튼
    if st.sidebar.button("🔎 검색 및 분석", type="primary"):
        if not search_keyword or not search_keyword.strip():
            st.sidebar.error("키워드를 입력해주세요.")
        elif not selected_sources:
            st.sidebar.error("최소 하나의 소스를 선택해주세요.")
        else:
            keyword = search_keyword.strip()
            st.sidebar.info(f"'{keyword}' 키워드로 데이터 수집 및 분석을 시작합니다...")
            
            # 데이터 수집
            with st.spinner(f"'{keyword}' 데이터 수집 중..."):
                success, result = monitoring_service.run_data_collection(keyword, selected_sources, max_results)
                if success:
                    st.sidebar.success(f"✅ {result}개 데이터 수집 완료")
                else:
                    st.sidebar.error(f"❌ 데이터 수집 실패")
            
            # 감정 분석 (YouTube만)
            if success and "youtube" in selected_sources:
                with st.spinner(f"'{keyword}' 감정 분석 중..."):
                    success2, analyzed_count = sentiment_analysis.run_sentiment_analysis(keyword, "youtube", 24)
                    if success2:
                        if analyzed_count > 0:
                            st.sidebar.success(f"✅ {analyzed_count}개 텍스트 분석 완료")
                        else:
                            st.sidebar.info("ℹ️ 분석할 새 데이터가 없습니다.")
                    else:
                        st.sidebar.error(f"❌ 감정 분석 실패")
            
            # 실시간 모니터링 시작 (선택사항)
            if realtime_enabled:
                session_manager.update_monitoring_state(keyword, selected_sources)
            
            # 페이지 새로고침
            st.success(f"✅ '{keyword}' 키워드 분석 완료!")
            # 캐시 초기화
            st.cache_data.clear()
            st.rerun()
    
    hours = st.sidebar.slider("분석 기간 (시간)", 1, 168, 24)
    
    # 트렌드 분석 알고리즘 선택
    selected_algorithm = render_algorithm_selector()
    
    st.sidebar.markdown("---")
    
    if realtime_enabled:
        interval = st.sidebar.selectbox(
            "수집 주기",
            options=[1, 3, 5, 10, 15, 30],
            index=2,  # 기본값: 5분
            format_func=lambda x: f"{x}분"
        )
        
        # 실시간 모니터링 실행
        if st.session_state.monitoring_keyword and st.session_state.monitoring_sources:
            # 마지막 업데이트로부터 경과 시간 확인
            if st.session_state.last_update_time:
                elapsed_minutes = (datetime.now() - st.session_state.last_update_time).total_seconds() / 60
                if elapsed_minutes >= interval:
                    with st.sidebar.spinner(f"'{st.session_state.monitoring_keyword}' 자동 수집 중..."):
                        success, result = monitoring_service.auto_collect_and_analyze(
                            st.session_state.monitoring_keyword,
                            st.session_state.monitoring_sources,
                            interval
                        )
                        if success:
                            session_manager.update_monitoring_state(
                                st.session_state.monitoring_keyword,
                                st.session_state.monitoring_sources
                            )
                            st.sidebar.success(f"✅ {result}개 데이터 수집 완료")
                            # 캐시 초기화
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.sidebar.error(f"❌ 수집 실패")
            else:
                session_manager.update_monitoring_state(
                    st.session_state.monitoring_keyword,
                    st.session_state.monitoring_sources
                )
        
        # 자동 새로고침 안내
        st.sidebar.markdown("---")
        st.sidebar.info("💡 **팁:** 실시간 업데이트를 보려면 페이지를 새로고침하세요 (F5 또는 Cmd+R)")
        
        # 새로고침 버튼
        if st.sidebar.button("🔄 지금 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    # 세션 상태는 이미 init_session_state()에서 초기화됨
    
    # 메인 화면
    if not search_keyword or not search_keyword.strip():
        st.warning("🔍 키워드를 입력하고 검색해주세요.")
        st.info("""
        **사용 방법:**
        1. 왼쪽 사이드바에서 키워드를 입력하세요
        2. 정보 소스를 선택하세요 (현재 YouTube만 지원)
        3. '검색 및 분석' 버튼을 클릭하세요
        4. 데이터 수집 및 감정 분석이 자동으로 실행됩니다
        """)
        return
    
    keyword = search_keyword.strip()
    
    # 데이터 다운로드 기능
    # 참고: Streamlit의 download_button은 렌더링 시 data를 생성하므로,
    # 대량 데이터의 경우 성능에 영향을 줄 수 있습니다.
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # 원본 댓글 데이터 다운로드
        try:
            csv_data = data_download.generate_comments_csv(keyword)
            if csv_data:
                st.download_button(
                    label="📥 원본 댓글 데이터 다운로드 (CSV)",
                    data=csv_data,
                    file_name=f"{keyword}_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_comments"
                )
        except Exception as e:
            logger.error(f"댓글 데이터 CSV 생성 실패: {e}", exc_info=True)
            st.error("데이터 다운로드 중 오류가 발생했습니다.")
    
    with col2:
        # 감정 분석 결과 다운로드
        try:
            csv_data = data_download.generate_sentiment_csv(keyword)
            if csv_data:
                st.download_button(
                    label="📊 감정 분석 결과 다운로드 (CSV)",
                    data=csv_data,
                    file_name=f"{keyword}_sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_sentiment"
                )
        except Exception as e:
            logger.error(f"감정 분석 CSV 생성 실패: {e}", exc_info=True)
            st.error("데이터 다운로드 중 오류가 발생했습니다.")
    
    with col3:
        # 통계 요약 다운로드
        try:
            csv_data = data_download.generate_summary_csv(keyword)
            if csv_data:
                st.download_button(
                    label="📈 통계 요약 다운로드 (CSV)",
                    data=csv_data,
                    file_name=f"{keyword}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_summary"
                )
        except Exception as e:
            logger.error(f"통계 요약 CSV 생성 실패: {e}", exc_info=True)
            st.error("데이터 다운로드 중 오류가 발생했습니다.")
    
    st.markdown("---")
    
    # 전체 트렌드 시각화 (변화점 Highlight)
    st.header(f"📈 전체 트렌드 분석: '{keyword}'")
    
    with get_db_session() as db:
        # 전체 감정 분석 데이터 조회
        all_sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.keyword == keyword,
            SentimentAnalysis.source == "youtube"
        ).order_by(SentimentAnalysis.analyzed_at).all()
        
        if all_sentiments:
            # 트렌드 분석 수행
            sentiment_list = []
            for sent in all_sentiments:
                sentiment_list.append({
                    "analyzed_at": sent.analyzed_at,
                    "positive_score": sent.positive_score,
                    "negative_score": sent.negative_score,
                    "neutral_score": sent.neutral_score
                })
            
            # 트렌드 분석 및 변화점 탐지 (고급 알고리즘 지원)
            try:
                trend_analysis_result = trend_service.analyze_trend_with_change_points(
                    sentiment_list, 
                    method=selected_algorithm  # 사용자가 선택한 알고리즘 사용
                )
                change_points_data = trend_analysis_result.get("change_points", [])
                alerts = trend_analysis_result.get("alerts", [])
                method_used = trend_analysis_result.get("method", "unknown")
            except Exception as e:
                logger.error(f"트렌드 분석 실패: {e}", exc_info=True)
                # 오류 발생 시 사용자에게 명확히 알림
                st.error(f"❌ 트렌드 분석 중 오류가 발생했습니다: {str(e)}")
                st.info("데이터를 확인하고 다시 시도해주세요.")
                change_points_data = []
                alerts = []
            
            # 시계열 데이터 준비
            df_trend = pd.DataFrame(sentiment_list)
            df_trend['analyzed_at'] = pd.to_datetime(df_trend['analyzed_at'])
            df_trend['sentiment_score'] = df_trend.apply(
                lambda row: calculate_sentiment_score(
                    row['positive_score'],
                    row['negative_score'],
                    row['neutral_score']
                ),
                axis=1
            )
            
            # 시간별 집계 (1시간 단위)
            df_trend['hour'] = df_trend['analyzed_at'].dt.floor('1h')  # 'H' -> 'h' (deprecated 경고 해결)
            hourly_df = df_trend.groupby('hour').agg({
                'sentiment_score': 'mean',
                'positive_score': 'mean',
                'negative_score': 'mean',
                'neutral_score': 'mean'
            }).reset_index()
            
            # Trend 선그래프 + 변화점 표시 (visualization 모듈 사용)
            fig_trend = create_trend_chart(hourly_df, change_points_data)
            st.plotly_chart(fig_trend, use_container_width=True, key=f"trend_chart_{keyword}")
            
            # 변화점 상세 정보
            if alerts:
                st.markdown("---")
                st.markdown(f"### 🚨 변화점 상세 정보 ({algorithm_display} 알고리즘)")
                alerts_df = pd.DataFrame(alerts)
                
                # 존재하는 컬럼만 선택 (SimpleChangeDetector는 previous_score/current_score 사용)
                available_columns = []
                column_mapping = {
                    'change_point': '변화점 시간',
                    'change_type': '변화 유형',
                    'change_rate': '변화율',
                    'previous_score': '이전 감정 점수',
                    'current_score': '현재 감정 점수',
                    'previous_sentiment': '이전 감정',
                    'current_sentiment': '현재 감정',
                    'window_start': '구간 시작',
                    'window_end': '구간 종료'
                }
                
                # 존재하는 컬럼 찾기
                for col in ['change_point', 'change_type', 'change_rate', 
                           'previous_score', 'current_score', 
                           'previous_sentiment', 'current_sentiment',
                           'window_start', 'window_end']:
                    if col in alerts_df.columns:
                        available_columns.append(col)
                
                if available_columns:
                    display_df = alerts_df[available_columns].copy()
                    # 컬럼명 한글로 변경
                    display_df.columns = [column_mapping.get(col, col) for col in display_df.columns]
                    st.dataframe(
                        display_df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.dataframe(alerts_df, use_container_width=True, hide_index=True)
            elif change_points_data:
                st.info(f"✅ {len(change_points_data)}개의 변화점이 감지되었습니다.")
        else:
            st.info("트렌드 분석을 위한 데이터가 충분하지 않습니다.")
    
    st.markdown("---")
    
    # YouTube 데이터 표시
    if "youtube" in selected_sources:
        st.header(f"📺 YouTube: '{keyword}'")
        
        # 한 번의 DB 세션으로 모든 데이터 조회 (성능 최적화)
        try:
            videos, comments_by_video, all_sentiments_dict = youtube_service.get_all_video_data(keyword)
        except Exception as e:
            logger.error(f"YouTube 데이터 조회 실패: {e}", exc_info=True)
            st.error("데이터를 불러오는 중 오류가 발생했습니다.")
            return
        
        if not videos:
            st.warning(f"키워드 '{keyword}'에 대한 YouTube 데이터가 없습니다.")
            st.info("위에서 '검색 및 분석' 버튼을 클릭하여 데이터를 수집하세요.")
            return
        
        st.markdown(f"**총 {len(videos)}개의 영상**")
        st.markdown("---")
        
        # 각 비디오별로 표시
        for idx, video in enumerate(videos, 1):
            video_id = video["video_id"]
            
            # 비디오 정보 카드
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"{idx}. {video['title']}")
                    st.markdown(f"**채널:** {video['channel_name']}")
                    st.markdown(f"**URL:** [{video['url']}]({video['url']})")
                
                with col2:
                    st.metric("조회수", format_number(video['view_count']))
                    st.metric("좋아요", format_number(video['like_count']))
                
                # 해당 비디오의 댓글 및 감정 분석 결과 (이미 로드된 데이터 사용)
                comments = comments_by_video.get(video_id, [])
                # 해당 비디오의 댓글 ID만 필터링
                video_comment_ids = {c.id for c in comments}
                sentiments_dict = {
                    text_id: sent 
                    for text_id, sent in all_sentiments_dict.items() 
                    if text_id in video_comment_ids
                }
                
                if sentiments_dict:
                    # 감정 통계 계산 (유틸리티 함수 사용 - 중복 제거)
                    stats = calculate_sentiment_statistics_from_dict(sentiments_dict)
                    sentiment_counts = stats['sentiment_counts']
                    avg_positive = stats['avg_positive']
                    avg_negative = stats['avg_negative']
                    avg_neutral = stats['avg_neutral']
                    overall_sentiment = stats['overall_sentiment']
                    
                    # 상위 댓글 5개 표시
                    st.markdown("---")
                    st.markdown("### 💬 상위 댓글")
                    
                    # 댓글과 감정 분석 결과 매칭하여 정렬
                    comment_sentiment_pairs = []
                    for comment in comments[:20]:  # 최대 20개 중에서 선택
                        if comment.id in sentiments_dict:
                            sent = sentiments_dict[comment.id]
                            sentiment_score = sent.positive_score - sent.negative_score
                            comment_sentiment_pairs.append((comment, sent, sentiment_score))
                    
                    # 감정 점수 순으로 정렬 (긍정/부정 모두 포함)
                    comment_sentiment_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
                    top_comments = comment_sentiment_pairs[:5]
                    
                    for i, (comment, sent, score) in enumerate(top_comments, 1):
                        sentiment_label = sent.predicted_sentiment
                        sentiment_emoji = "😊" if sentiment_label == "positive" else "😢" if sentiment_label == "negative" else "😐"
                        
                        with st.expander(f"{sentiment_emoji} 댓글 {i}: {comment.text[:50]}..." if len(comment.text) > 50 else f"{sentiment_emoji} 댓글 {i}: {comment.text}"):
                            st.markdown(f"**댓글:** {comment.text}")
                            if comment.author:
                                st.markdown(f"**작성자:** {comment.author}")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("긍정", f"{sent.positive_score:.2f}", delta=None)
                            with col2:
                                st.metric("부정", f"{sent.negative_score:.2f}", delta=None)
                            with col3:
                                st.metric("중립", f"{sent.neutral_score:.2f}", delta=None)
                    
                    st.markdown("---")
                    
                    # 감정 분석 결과 표시
                    st.markdown("### 📊 감정 분석 결과")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("분석된 댓글", len(sentiments_dict))
                    with col2:
                        st.metric("긍정", sentiment_counts.get("positive", 0), 
                                delta=f"{sentiment_counts.get('positive', 0)/len(sentiments_dict)*100:.1f}%")
                    with col3:
                        st.metric("부정", sentiment_counts.get("negative", 0),
                                delta=f"{sentiment_counts.get('negative', 0)/len(sentiments_dict)*100:.1f}%")
                    with col4:
                        st.metric("중립", sentiment_counts.get("neutral", 0),
                                delta=f"{sentiment_counts.get('neutral', 0)/len(sentiments_dict)*100:.1f}%")
                    
                    # 시각적인 그래프들 (visualization 모듈 사용)
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig_donut = create_donut_chart(sentiment_counts, "감정 분포")
                        st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_chart_{video_id}_{idx}")
                    
                    with col2:
                        fig_gauge = create_gauge_chart(overall_sentiment, "전체 감정 스코어")
                        st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_chart_{video_id}_{idx}")
                    
                    fig_bar = create_bar_chart(avg_positive, avg_negative, avg_neutral, "평균 감정 점수 분포")
                    st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_chart_{video_id}_{idx}")
                    
                    # 9가지 감정 분류 추가
                    st.markdown("---")
                    st.markdown("### 🎭 9가지 감정 분류")
                    
                    try:
                        # 댓글 텍스트 추출
                        comment_texts = [c.text for c in comments if c.id in sentiments_dict]
                        
                        if comment_texts:
                            # 감정 서비스 초기화
                            emotion_svc = emotion_service.EmotionService()
                            
                            # 9가지 감정 분류 수행
                            emotion_results = emotion_svc.analyze_emotions_batch(comment_texts[:100])  # 최대 100개
                            emotion_stats = emotion_svc.get_emotion_statistics(emotion_results)
                            
                            # 감정 분포 차트 표시
                            fig_emotion = create_emotion_distribution_chart(emotion_stats)
                            st.plotly_chart(fig_emotion, use_container_width=True, key=f"emotion_chart_{video_id}_{idx}")
                            
                            # 상위 감정 표시
                            if emotion_stats.get("emotion_counts"):
                                top_emotions = sorted(
                                    emotion_stats["emotion_counts"].items(),
                                    key=lambda x: x[1],
                                    reverse=True
                                )[:3]
                                
                                col1, col2, col3 = st.columns(3)
                                for i, (emotion, count) in enumerate(top_emotions):
                                    with [col1, col2, col3][i]:
                                        emotion_label_kr = emotion_svc.get_emotion_label_kr(emotion)
                                        percentage = emotion_stats["emotion_percentages"].get(emotion, 0)
                                        st.metric(
                                            emotion_label_kr,
                                            f"{count}개",
                                            delta=f"{percentage:.1f}%"
                                        )
                        else:
                            st.info("감정 분류를 위한 댓글 데이터가 없습니다.")
                    except Exception as e:
                        logger.error(f"9가지 감정 분류 실패: {e}", exc_info=True)
                        st.warning("감정 분류 중 오류가 발생했습니다.")
                    
                    # 토픽-감정 분석 추가
                    st.markdown("---")
                    st.markdown("### 📚 토픽별 감정 분석")
                    
                    try:
                        # 댓글 텍스트 및 감정 분석 결과 추출
                        comment_texts_for_topic = []
                        sentiment_results_for_topic = []
                        
                        for comment in comments[:100]:  # 최대 100개
                            if comment.id in sentiments_dict:
                                sent = sentiments_dict[comment.id]
                                comment_texts_for_topic.append(comment.text)
                                sentiment_results_for_topic.append({
                                    "positive_score": sent.positive_score,
                                    "negative_score": sent.negative_score,
                                    "neutral_score": sent.neutral_score
                                })
                        
                        if comment_texts_for_topic:
                            # 감정 서비스 초기화
                            emotion_svc = emotion_service.EmotionService()
                            
                            # 토픽-감정 분석 수행
                            topic_results = emotion_svc.analyze_topics_with_sentiment(
                                comment_texts_for_topic,
                                sentiment_results_for_topic,
                                use_bertopic=True  # BERTopic 사용 (설치되어 있으면)
                            )
                            
                            # 토픽별 감정 차트 표시
                            fig_topic = create_topic_sentiment_chart(topic_results)
                            st.plotly_chart(fig_topic, use_container_width=True, key=f"topic_chart_{video_id}_{idx}")
                            
                            # 토픽 상세 정보 표시
                            if topic_results.get("topics"):
                                st.markdown("**주요 토픽:**")
                                for topic in topic_results["topics"][:5]:  # 상위 5개
                                    keywords = topic.get("keywords", [])
                                    sentiment = topic.get("sentiment", {})
                                    count = topic.get("count", 0)
                                    
                                    if keywords:
                                        keyword_str = ", ".join(keywords[:3])
                                        st.markdown(f"- **{keyword_str}** ({count}개 댓글)")
                                        st.caption(
                                            f"  긍정: {sentiment.get('avg_positive', 0):.1%}, "
                                            f"부정: {sentiment.get('avg_negative', 0):.1%}, "
                                            f"중립: {sentiment.get('avg_neutral', 0):.1%}"
                                        )
                            
                            # 분석 방법 표시
                            method = topic_results.get("method", "unknown")
                            method_label = {
                                "bertopic": "BERTopic (고급 토픽 모델링)",
                                "keyword_based": "키워드 기반 분석",
                                "none": "분석 불가",
                                "error": "오류 발생"
                            }.get(method, method)
                            st.caption(f"분석 방법: {method_label}")
                        else:
                            st.info("토픽 분석을 위한 댓글 데이터가 없습니다.")
                    except Exception as e:
                        logger.error(f"토픽-감정 분석 실패: {e}", exc_info=True)
                        st.warning("토픽 분석 중 오류가 발생했습니다.")
                    
                    # Word Cloud 추가
                    st.markdown("---")
                    st.markdown("### ☁️ 키워드 Word Cloud")
                    
                    # 긍정/부정 댓글 분리
                    positive_texts = []
                    negative_texts = []
                    all_texts = []
                    
                    # 상위 댓글에서 긍정/부정 분리
                    for comment, sent, score in comment_sentiment_pairs:
                        cleaned_text = comment.text
                        sentiment_label = sent.predicted_sentiment.lower()  # 대소문자 통일
                        
                        if sentiment_label == "positive":
                            positive_texts.append(cleaned_text)
                        elif sentiment_label == "negative":
                            negative_texts.append(cleaned_text)
                        all_texts.append(cleaned_text)
                    
                    # 전체 댓글에서도 추가 수집 (중복 제거)
                    seen_texts = set(positive_texts + negative_texts)
                    for comment in comments[:100]:  # 더 많은 댓글 확인
                        if comment.id in sentiments_dict:
                            sent = sentiments_dict[comment.id]
                            sentiment_label = sent.predicted_sentiment.lower()
                            
                            # 중복 제거
                            if comment.text not in seen_texts:
                                if sentiment_label == "positive":
                                    positive_texts.append(comment.text)
                                    seen_texts.add(comment.text)
                                elif sentiment_label == "negative":
                                    negative_texts.append(comment.text)
                                    seen_texts.add(comment.text)
                                all_texts.append(comment.text)
                    
                    # 디버깅 정보 (개발용)
                    # st.write(f"디버그: 긍정 {len(positive_texts)}개, 부정 {len(negative_texts)}개")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**긍정 키워드**")
                        if positive_texts:
                            st.caption(f"총 {len(positive_texts)}개의 긍정 댓글")
                            wordcloud_img = generate_wordcloud(positive_texts, "positive")
                            if wordcloud_img:
                                st.image(wordcloud_img, use_container_width=True)
                            else:
                                st.info("Word Cloud 생성에 충분한 데이터가 없습니다.")
                        else:
                            st.info("긍정 댓글이 없습니다.")
                            # 디버깅: 감정 분포 확인
                            sentiment_dist = {}
                            for comment in comments[:20]:
                                if comment.id in sentiments_dict:
                                    sent = sentiments_dict[comment.id]
                                    sentiment_dist[sent.predicted_sentiment] = sentiment_dist.get(sent.predicted_sentiment, 0) + 1
                            if sentiment_dist:
                                st.write(f"감정 분포: {sentiment_dist}")
                    
                    with col2:
                        st.markdown("**부정 키워드**")
                        if negative_texts:
                            st.caption(f"총 {len(negative_texts)}개의 부정 댓글")
                            wordcloud_img = generate_wordcloud(negative_texts, "negative")
                            if wordcloud_img:
                                st.image(wordcloud_img, use_container_width=True)
                            else:
                                st.info("Word Cloud 생성에 충분한 데이터가 없습니다.")
                        else:
                            st.info("부정 댓글이 없습니다.")
                    
                    # 분석 이유 설명
                    st.markdown("---")
                    st.markdown("### 💡 분석 요약")
                    
                    # 감정 분석 기반 설명 생성
                    dominant_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])
                    dominant_ratio = dominant_sentiment[1] / len(sentiments_dict) * 100
                    
                    analysis_text = f"""
                    **주요 감정:** {dominant_sentiment[0].upper()} ({dominant_ratio:.1f}%)
                    
                    **분석 근거:**
                    - 전체 {len(sentiments_dict)}개 댓글 중 {sentiment_counts.get('positive', 0)}개가 긍정적, {sentiment_counts.get('negative', 0)}개가 부정적, {sentiment_counts.get('neutral', 0)}개가 중립적입니다.
                    - 평균 감정 스코어는 {overall_sentiment:.2f}로, {'긍정적인 반응이 우세' if overall_sentiment > 0.1 else '부정적인 반응이 우세' if overall_sentiment < -0.1 else '중립적인 반응이 우세'}합니다.
                    - {'긍정' if avg_positive > avg_negative and avg_positive > avg_neutral else '부정' if avg_negative > avg_positive and avg_negative > avg_neutral else '중립'} 감정이 가장 높은 비율({max(avg_positive, avg_negative, avg_neutral):.1%})을 차지합니다.
                    """
                    
                    st.info(analysis_text)
                else:
                    st.info("이 영상에 대한 감정 분석 결과가 없습니다.")
                
                st.markdown("---")
    
    # X(트위터), 뉴스, 블로그는 추후 추가 안내
    if "twitter" in selected_sources or "news" in selected_sources or "blog" in selected_sources:
        st.markdown("---")
        st.info("""
        **추후 추가될 서비스**
        - X (트위터): 트위터/X API 연동 예정
        - 뉴스: 뉴스 API 연동 예정
        - 블로그: 블로그 크롤링 기능 추가 예정
        
        현재는 YouTube 데이터만 확인 가능합니다.
        """)


if __name__ == "__main__":
    main()
