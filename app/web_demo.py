"""
Streamlit 기반 실시간 감정 모니터링 대시보드
키워드 검색 및 소스별 데이터 표시
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time
import threading
from collections import defaultdict
import io
import re
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import init_database, get_db
from src.database.models import SentimentAnalysis, CollectedText
from src.trend.trend_utils import TrendAnalyzer
from src.trend.simple_change_detector import SimpleChangeDetector
from src.collectors.collector_manager import CollectorManager
from src.sentiment.sentiment_utils import SentimentAnalyzer
from src.preprocessing.text_cleaner import TextCleaner

# 페이지 설정
st.set_page_config(
    page_title="Social Sentiment & Trend Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 데이터베이스 초기화
init_database("sqlite:///data/database/sentiment.db")


@st.cache_data(ttl=5)  # 캐시 시간 단축 (실시간 업데이트)
def get_sentiment_data(keyword: str, source: str, hours: int = 24):
    """감정 분석 데이터 조회"""
    db = next(get_db())
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.keyword == keyword,
            SentimentAnalysis.source == source,
            SentimentAnalysis.analyzed_at >= start_time
        ).order_by(SentimentAnalysis.analyzed_at).all()
        
        data = []
        for s in sentiments:
            data.append({
                "analyzed_at": s.analyzed_at,
                "positive_score": s.positive_score,
                "negative_score": s.negative_score,
                "neutral_score": s.neutral_score,
                "predicted_sentiment": s.predicted_sentiment,
                "text_id": s.text_id
            })
        
        return data
    finally:
        db.close()


@st.cache_data(ttl=5)  # 캐시 시간 단축 (실시간 업데이트)
def get_video_data(keyword: str):
    """YouTube 비디오 정보 조회"""
    db = next(get_db())
    try:
        videos = db.query(CollectedText).filter(
            CollectedText.keyword == keyword,
            CollectedText.source == "youtube",
            CollectedText.video_id.isnot(None)
        ).distinct(CollectedText.video_id).all()
        
        video_dict = {}
        for video in videos:
            video_id = video.video_id
            if video_id and video_id not in video_dict:
                video_dict[video_id] = {
                    "video_id": video_id,
                    "title": video.video_title or "제목 없음",
                    "channel_name": video.channel_name or "채널명 없음",
                    "view_count": video.view_count or 0,
                    "like_count": video.like_count or 0,
                    "url": video.url or f"https://www.youtube.com/watch?v={video_id}"
                }
        
        return list(video_dict.values())
    finally:
        db.close()


def run_data_collection(keyword: str, sources: list, max_results: int = 10):
    """데이터 수집 실행"""
    try:
        collector_manager = CollectorManager()
        
        # 선택된 소스만 활성화
        enabled_sources = []
        if "youtube" in sources:
            enabled_sources.append("youtube")
        if "twitter" in sources:
            enabled_sources.append("twitter")
        if "news" in sources:
            enabled_sources.append("news")
        if "blog" in sources:
            enabled_sources.append("blog")
        
        if not enabled_sources:
            return False, "소스를 선택해주세요."
        
        collected_data = collector_manager.collect_all(
            keyword, 
            max_results, 
            save_to_database=True
        )
        return True, len(collected_data)
    except Exception as e:
        return False, str(e)


def run_sentiment_analysis(keyword: str, source: str, hours: int = 24):
    """감정 분석 실행"""
    try:
        db = next(get_db())
        from datetime import datetime, timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 이미 분석된 텍스트 ID 조회
        analyzed_text_ids = db.query(SentimentAnalysis.text_id).filter(
            SentimentAnalysis.keyword == keyword,
            SentimentAnalysis.source == source
        ).subquery()
        
        # 분석할 텍스트 조회
        texts_to_analyze = db.query(CollectedText).filter(
            CollectedText.keyword == keyword,
            CollectedText.source == source,
            CollectedText.collected_at >= start_time,
            ~CollectedText.id.in_(analyzed_text_ids)
        ).all()
        
        if not texts_to_analyze:
            db.close()
            return True, 0
        
        # 감정 분석 수행
        sentiment_analyzer = SentimentAnalyzer()
        text_cleaner = TextCleaner()
        
        analyzed_count = 0
        for text_obj in texts_to_analyze:
            try:
                cleaned_text = text_cleaner.clean_text_for_sentiment(text_obj.text)
                if not cleaned_text or len(cleaned_text.strip()) < 5:
                    continue
                
                result = sentiment_analyzer.analyze(cleaned_text)
                
                sentiment_obj = SentimentAnalysis(
                    text_id=text_obj.id,
                    keyword=text_obj.keyword,
                    source=text_obj.source,
                    positive_score=result['positive_score'],
                    negative_score=result['negative_score'],
                    neutral_score=result['neutral_score'],
                    predicted_sentiment=result['predicted_sentiment'],
                    model_type=result.get('model_type', 'unknown'),
                    analyzed_at=datetime.utcnow()
                )
                db.add(sentiment_obj)
                analyzed_count += 1
            except Exception:
                continue
        
        db.commit()
        db.close()
        return True, analyzed_count
    except Exception as e:
        if db:
            db.close()
        return False, str(e)


def calculate_sentiment_score(positive: float, negative: float, neutral: float) -> float:
    """감정 점수 계산 (-1 ~ 1)"""
    return positive * 1.0 + neutral * 0.0 + negative * (-1.0)


def format_number(num: int) -> str:
    """숫자 포맷팅 (예: 1000 -> 1K)"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def generate_wordcloud(texts: list, sentiment_type: str = "all") -> np.ndarray:
    """Word Cloud 생성 (한국어 지원)"""
    try:
        import platform
        import os
        
        # 텍스트 결합
        combined_text = " ".join(texts)
        
        if not combined_text or len(combined_text.strip()) < 10:
            return None
        
        # 한국어 폰트 경로 찾기
        font_path = None
        if platform.system() == 'Darwin':  # macOS
            font_paths = [
                '/System/Library/Fonts/Supplemental/AppleGothic.ttf',
                '/System/Library/Fonts/AppleGothic.ttf',
                '/Library/Fonts/AppleGothic.ttf',
            ]
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
        elif platform.system() == 'Windows':  # Windows
            font_paths = [
                'C:/Windows/Fonts/malgun.ttf',  # 맑은 고딕
                'C:/Windows/Fonts/gulim.ttc',    # 굴림
            ]
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
        elif platform.system() == 'Linux':  # Linux
            font_paths = [
                '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            ]
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
        
        # Word Cloud 생성
        if sentiment_type == "positive":
            colors = ['#2ecc71', '#27ae60', '#229954']
        elif sentiment_type == "negative":
            colors = ['#e74c3c', '#c0392b', '#a93226']
        else:
            colors = ['#3498db', '#2980b9', '#1f618d']
        
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path=font_path,  # 한국어 폰트 경로 지정
            max_words=100,
            colormap='viridis' if sentiment_type == "all" else 'Greens' if sentiment_type == "positive" else 'Reds',
            relative_scaling=0.5,
            random_state=42
        ).generate(combined_text)
        
        # 이미지로 변환
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        # Streamlit용 이미지 변환
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    except Exception as e:
        print(f"Word Cloud 생성 실패: {e}")
        return None


def auto_collect_and_analyze(keyword: str, sources: list, interval_minutes: int = 5):
    """백그라운드에서 자동으로 데이터 수집 및 분석"""
    try:
        # 데이터 수집
        collector_manager = CollectorManager()
        collected_data = collector_manager.collect_all(
            keyword, 
            10,  # 소량만 수집
            save_to_database=True
        )
        
        # 감정 분석 (YouTube만)
        if "youtube" in sources and collected_data:
            run_sentiment_analysis(keyword, "youtube", 24)
        
        return True, len(collected_data)
    except Exception as e:
        return False, str(e)


def main():
    """메인 대시보드 함수"""
    st.title("📊 Social Sentiment & Trend Monitor")
    
    # 실시간 모니터링 상태 표시
    if 'realtime_monitoring' not in st.session_state:
        st.session_state.realtime_monitoring = False
    if 'last_update_time' not in st.session_state:
        st.session_state.last_update_time = None
    if 'monitoring_keyword' not in st.session_state:
        st.session_state.monitoring_keyword = None
    if 'monitoring_sources' not in st.session_state:
        st.session_state.monitoring_sources = []
    
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
                success, result = run_data_collection(keyword, selected_sources, max_results)
                if success:
                    st.sidebar.success(f"✅ {result}개 데이터 수집 완료")
                else:
                    st.sidebar.error(f"❌ 데이터 수집 실패: {result}")
            
            # 감정 분석 (YouTube만)
            if success and "youtube" in selected_sources:
                with st.spinner(f"'{keyword}' 감정 분석 중..."):
                    success2, analyzed_count = run_sentiment_analysis(keyword, "youtube", 24)
                    if success2:
                        if analyzed_count > 0:
                            st.sidebar.success(f"✅ {analyzed_count}개 텍스트 분석 완료")
                        else:
                            st.sidebar.info("ℹ️ 분석할 새 데이터가 없습니다.")
                    else:
                        st.sidebar.error(f"❌ 감정 분석 실패: {analyzed_count}")
            
            # 실시간 모니터링 시작 (선택사항)
            if realtime_enabled:
                st.session_state.monitoring_keyword = keyword
                st.session_state.monitoring_sources = selected_sources.copy()
                st.session_state.last_update_time = datetime.now()
            
            # 페이지 새로고침
            st.success(f"✅ '{keyword}' 키워드 분석 완료!")
            # 캐시 초기화
            st.cache_data.clear()
            st.rerun()
    
    hours = st.sidebar.slider("분석 기간 (시간)", 1, 168, 24)
    
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
                        success, result = auto_collect_and_analyze(
                            st.session_state.monitoring_keyword,
                            st.session_state.monitoring_sources,
                            interval
                        )
                        if success:
                            st.session_state.last_update_time = datetime.now()
                            st.sidebar.success(f"✅ {result}개 데이터 수집 완료")
                            # 캐시 초기화
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.sidebar.error(f"❌ 수집 실패: {result}")
            else:
                st.session_state.last_update_time = datetime.now()
        
        # 자동 새로고침 안내
        st.sidebar.markdown("---")
        st.sidebar.info("💡 **팁:** 실시간 업데이트를 보려면 페이지를 새로고침하세요 (F5 또는 Cmd+R)")
        
        # 새로고침 버튼
        if st.sidebar.button("🔄 지금 새로고침"):
            st.cache_data.clear()
            st.rerun()
    
    # 세션 상태에 검색 키워드 저장
    if 'current_keyword' not in st.session_state:
        st.session_state.current_keyword = None
    if 'current_source' not in st.session_state:
        st.session_state.current_source = "youtube"
    
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
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # 원본 댓글 데이터 다운로드
        db = next(get_db())
        try:
            comments_data = db.query(CollectedText).filter(
                CollectedText.keyword == keyword
            ).all()
            
            if comments_data:
                comments_df = pd.DataFrame([{
                    "키워드": c.keyword,
                    "소스": c.source,
                    "댓글": c.text,
                    "작성자": c.author or "",
                    "URL": c.url or "",
                    "수집일시": c.collected_at.strftime("%Y-%m-%d %H:%M:%S") if c.collected_at else "",
                    "영상제목": c.video_title or "",
                    "채널명": c.channel_name or "",
                    "조회수": c.view_count or 0,
                    "좋아요": c.like_count or 0
                } for c in comments_data])
                
                csv_buffer = io.StringIO()
                comments_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📥 원본 댓글 데이터 다운로드 (CSV)",
                    data=csv_data.encode('utf-8-sig'),
                    file_name=f"{keyword}_comments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_comments"
                )
        finally:
            db.close()
    
    with col2:
        # 감정 분석 결과 다운로드
        db = next(get_db())
        try:
            sentiments_data = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.keyword == keyword
            ).all()
            
            if sentiments_data:
                # 원본 텍스트와 매칭
                sentiment_list = []
                for sent in sentiments_data:
                    text_obj = db.query(CollectedText).filter(CollectedText.id == sent.text_id).first()
                    sentiment_list.append({
                        "키워드": sent.keyword,
                        "소스": sent.source,
                        "댓글": text_obj.text if text_obj else "",
                        "작성자": text_obj.author if text_obj else "",
                        "긍정점수": f"{sent.positive_score:.4f}",
                        "부정점수": f"{sent.negative_score:.4f}",
                        "중립점수": f"{sent.neutral_score:.4f}",
                        "예측감정": sent.predicted_sentiment,
                        "모델타입": sent.model_type,
                        "분석일시": sent.analyzed_at.strftime("%Y-%m-%d %H:%M:%S") if sent.analyzed_at else ""
                    })
                
                sentiments_df = pd.DataFrame(sentiment_list)
                
                csv_buffer = io.StringIO()
                sentiments_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📊 감정 분석 결과 다운로드 (CSV)",
                    data=csv_data.encode('utf-8-sig'),
                    file_name=f"{keyword}_sentiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_sentiment"
                )
        finally:
            db.close()
    
    with col3:
        # 통계 요약 다운로드
        db = next(get_db())
        try:
            sentiments_data = db.query(SentimentAnalysis).filter(
                SentimentAnalysis.keyword == keyword
            ).all()
            
            if sentiments_data:
                sentiment_counts = defaultdict(int)
                total_positive = 0
                total_negative = 0
                total_neutral = 0
                
                for sent in sentiments_data:
                    sentiment_counts[sent.predicted_sentiment] += 1
                    total_positive += sent.positive_score
                    total_negative += sent.negative_score
                    total_neutral += sent.neutral_score
                
                avg_positive = total_positive / len(sentiments_data) if sentiments_data else 0
                avg_negative = total_negative / len(sentiments_data) if sentiments_data else 0
                avg_neutral = total_neutral / len(sentiments_data) if sentiments_data else 0
                overall_sentiment = avg_positive - avg_negative
                
                summary_df = pd.DataFrame([{
                    "키워드": keyword,
                    "총댓글수": len(sentiments_data),
                    "긍정개수": sentiment_counts.get("positive", 0),
                    "부정개수": sentiment_counts.get("negative", 0),
                    "중립개수": sentiment_counts.get("neutral", 0),
                    "평균긍정점수": f"{avg_positive:.4f}",
                    "평균부정점수": f"{avg_negative:.4f}",
                    "평균중립점수": f"{avg_neutral:.4f}",
                    "전체감정스코어": f"{overall_sentiment:.4f}",
                    "생성일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                
                csv_buffer = io.StringIO()
                summary_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                csv_data = csv_buffer.getvalue()
                
                st.download_button(
                    label="📈 통계 요약 다운로드 (CSV)",
                    data=csv_data.encode('utf-8-sig'),
                    file_name=f"{keyword}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_summary"
                )
        finally:
            db.close()
    
    st.markdown("---")
    
    # 전체 트렌드 시각화 (변화점 Highlight)
    st.header(f"📈 전체 트렌드 분석: '{keyword}'")
    
    db = next(get_db())
    try:
        # 전체 감정 분석 데이터 조회
        all_sentiments = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.keyword == keyword,
            SentimentAnalysis.source == "youtube"
        ).order_by(SentimentAnalysis.analyzed_at).all()
        
        if all_sentiments:
            # 트렌드 분석 수행
            trend_analyzer = TrendAnalyzer()
            sentiment_list = []
            for sent in all_sentiments:
                sentiment_list.append({
                    "analyzed_at": sent.analyzed_at,
                    "positive_score": sent.positive_score,
                    "negative_score": sent.negative_score,
                    "neutral_score": sent.neutral_score
                })
            
            trend_result = trend_analyzer.analyze_trend(sentiment_list)
            change_points_data = trend_result.get("change_points", [])
            alerts = trend_result.get("alerts", [])
            
            # SimpleChangeDetector에서 변화점 데이터 가져오기 (상세 정보 포함)
            if isinstance(trend_analyzer.change_detector, SimpleChangeDetector):
                change_points_detail = trend_analyzer.change_detector.detect_changes(sentiment_list)
                # ISO 문자열 리스트로 변환
                change_points_data = [cp['change_point'] for cp in change_points_detail]
                alerts = change_points_detail
            
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
            df_trend['hour'] = df_trend['analyzed_at'].dt.floor('1H')
            hourly_df = df_trend.groupby('hour').agg({
                'sentiment_score': 'mean',
                'positive_score': 'mean',
                'negative_score': 'mean',
                'neutral_score': 'mean'
            }).reset_index()
            
            # Trend 선그래프 + 변화점 표시
            fig_trend = go.Figure()
            
            # 감정 스코어 라인
            fig_trend.add_trace(go.Scatter(
                x=hourly_df['hour'],
                y=hourly_df['sentiment_score'],
                mode='lines+markers',
                name='감정 스코어',
                line=dict(color='#3498db', width=3),
                marker=dict(size=8),
                fill='tonexty',
                fillcolor='rgba(52, 152, 219, 0.1)'
            ))
            
            # 변화점 Highlight
            if change_points_data:
                for cp in change_points_data:
                    # cp는 ISO 형식 문자열이거나 datetime 객체일 수 있음
                    if isinstance(cp, str):
                        cp_time = pd.to_datetime(cp)
                    elif isinstance(cp, datetime):
                        cp_time = pd.to_datetime(cp)
                    elif isinstance(cp, dict):
                        cp_time_str = cp.get('change_point', '')
                        cp_time = pd.to_datetime(cp_time_str) if cp_time_str else None
                        cp_type = cp.get('change_type', 'unknown')
                        cp_rate = cp.get('change_rate', 0)
                    else:
                        cp_time = pd.to_datetime(cp)
                    
                    if cp_time is None:
                        continue
                    
                    # Plotly는 datetime을 직접 받을 수 있지만, pandas Timestamp로 변환
                    cp_time_plotly = pd.to_datetime(cp_time)
                    
                    # 변화점에 수직선 추가 (add_shape 사용 - 더 안정적)
                    fig_trend.add_shape(
                        type="line",
                        x0=cp_time_plotly,
                        x1=cp_time_plotly,
                        y0=hourly_df['sentiment_score'].min() - 0.1,
                        y1=hourly_df['sentiment_score'].max() + 0.1,
                        line=dict(
                            color="red",
                            width=3,
                            dash="dash"
                        ),
                        opacity=0.7
                    )
                    
                    # 변화점 주석 추가
                    fig_trend.add_annotation(
                        x=cp_time_plotly,
                        y=hourly_df['sentiment_score'].max() + 0.05,
                        text="변화점",
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor="red",
                        font=dict(size=12, color="red"),
                        bgcolor="rgba(255, 255, 255, 0.8)",
                        bordercolor="red",
                        borderwidth=1
                    )
                    # 변화점에 마커 추가 (해당 시간의 감정 스코어 찾기)
                    cp_hour = cp_time_plotly.floor('1H')
                    matching_rows = hourly_df[hourly_df['hour'] == cp_hour]
                    if len(matching_rows) > 0:
                        cp_score = matching_rows.iloc[0]['sentiment_score']
                    else:
                        # 가장 가까운 시간 찾기
                        closest_idx = (hourly_df['hour'] - cp_hour).abs().idxmin()
                        cp_score = hourly_df.loc[closest_idx, 'sentiment_score'] if closest_idx < len(hourly_df) else 0
                    
                    fig_trend.add_trace(go.Scatter(
                        x=[cp_time_plotly],
                        y=[cp_score],
                        mode='markers',
                        name='변화점' if cp == change_points_data[0] else '',
                        marker=dict(
                            size=20,
                            color='red',
                            symbol='diamond',
                            line=dict(width=3, color='darkred')
                        ),
                        showlegend=(cp == change_points_data[0]),
                        hovertemplate=f'변화점<br>시간: {cp_time_plotly}<br>감정 스코어: {cp_score:.3f}<extra></extra>'
                    ))
            
            # 기준선 (0)
            fig_trend.add_hline(
                y=0,
                line_dash="dot",
                line_color="gray",
                line_width=1,
                annotation_text="중립",
                annotation_position="right"
            )
            
            fig_trend.update_layout(
                title=f"📈 감정 트렌드 타임라인 (변화점 Highlight)",
                xaxis_title="시간",
                yaxis_title="감정 스코어 (-1: 부정적, 0: 중립, 1: 긍정적)",
                hovermode='x unified',
                height=500,
                showlegend=True,
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
            )
            
            st.plotly_chart(fig_trend, use_container_width=True, key=f"trend_chart_{keyword}")
            
            # 변화점 상세 정보
            if alerts:
                st.markdown("---")
                st.markdown("### 🚨 변화점 상세 정보")
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
    finally:
        db.close()
    
    st.markdown("---")
    
    # YouTube 데이터 표시
    if "youtube" in selected_sources:
        st.header(f"📺 YouTube: '{keyword}'")
        
        # 비디오 정보 조회
        videos = get_video_data(keyword)
        
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
                
                # 해당 비디오의 댓글 및 감정 분석 결과
                db = next(get_db())
                try:
                    # 비디오의 댓글 조회
                    comments = db.query(CollectedText).filter(
                        CollectedText.keyword == keyword,
                        CollectedText.video_id == video_id
                    ).order_by(CollectedText.collected_at.desc()).all()
                    
                    # 감정 분석 결과 조회 및 매칭
                    comment_ids = [c.id for c in comments]
                    sentiments_dict = {}
                    if comment_ids:
                        sentiments = db.query(SentimentAnalysis).filter(
                            SentimentAnalysis.text_id.in_(comment_ids)
                        ).all()
                        sentiments_dict = {sent.text_id: sent for sent in sentiments}
                    
                    if sentiments_dict:
                        # 감정 통계
                        sentiment_counts = defaultdict(int)
                        total_positive = 0
                        total_negative = 0
                        total_neutral = 0
                        
                        for sent in sentiments_dict.values():
                            sentiment_counts[sent.predicted_sentiment] += 1
                            total_positive += sent.positive_score
                            total_negative += sent.negative_score
                            total_neutral += sent.neutral_score
                        
                        avg_positive = total_positive / len(sentiments_dict) if sentiments_dict else 0
                        avg_negative = total_negative / len(sentiments_dict) if sentiments_dict else 0
                        avg_neutral = total_neutral / len(sentiments_dict) if sentiments_dict else 0
                        
                        # 전체 감정 스코어 계산 (-1 ~ 1)
                        overall_sentiment = avg_positive - avg_negative
                        
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
                        
                        # 시각적인 그래프들
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Donut Chart
                            fig_donut = go.Figure(data=[go.Pie(
                                labels=['긍정', '부정', '중립'],
                                values=[sentiment_counts.get("positive", 0), 
                                       sentiment_counts.get("negative", 0),
                                       sentiment_counts.get("neutral", 0)],
                                hole=0.5,
                                marker_colors=['#2ecc71', '#e74c3c', '#95a5a6'],
                                textinfo='label+percent',
                                textposition='outside'
                            )])
                            fig_donut.update_layout(
                                title="감정 분포",
                                height=350,
                                showlegend=True
                            )
                            st.plotly_chart(fig_donut, use_container_width=True, key=f"donut_chart_{video_id}_{idx}")
                        
                        with col2:
                            # Gauge Chart (전체 감정 스코어)
                            fig_gauge = go.Figure(go.Indicator(
                                mode="gauge+number+delta",
                                value=overall_sentiment * 100,  # -100 ~ 100 범위
                                domain={'x': [0, 1], 'y': [0, 1]},
                                title={'text': "전체 감정 스코어"},
                                delta={'reference': 0},
                                gauge={
                                    'axis': {'range': [-100, 100]},
                                    'bar': {'color': "#2ecc71" if overall_sentiment > 0 else "#e74c3c" if overall_sentiment < 0 else "#95a5a6"},
                                    'steps': [
                                        {'range': [-100, 0], 'color': "lightgray"},
                                        {'range': [0, 100], 'color': "gray"}
                                    ],
                                    'threshold': {
                                        'line': {'color': "red", 'width': 4},
                                        'thickness': 0.75,
                                        'value': 0
                                    }
                                }
                            ))
                            fig_gauge.update_layout(height=350)
                            st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_chart_{video_id}_{idx}")
                        
                        # 감정 점수 바 차트 (개선)
                        fig_bar = go.Figure()
                        fig_bar.add_trace(go.Bar(
                            name='긍정',
                            x=['감정 점수'],
                            y=[avg_positive],
                            marker_color='#2ecc71',
                            text=f'{avg_positive:.2%}',
                            textposition='inside'
                        ))
                        fig_bar.add_trace(go.Bar(
                            name='부정',
                            x=['감정 점수'],
                            y=[avg_negative],
                            marker_color='#e74c3c',
                            text=f'{avg_negative:.2%}',
                            textposition='inside'
                        ))
                        fig_bar.add_trace(go.Bar(
                            name='중립',
                            x=['감정 점수'],
                            y=[avg_neutral],
                            marker_color='#95a5a6',
                            text=f'{avg_neutral:.2%}',
                            textposition='inside'
                        ))
                        fig_bar.update_layout(
                            title="평균 감정 점수 분포",
                            barmode='stack',
                            height=300,
                            showlegend=True,
                            yaxis=dict(range=[0, 1], title="비율")
                        )
                        st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_chart_{video_id}_{idx}")
                        
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
                    
                finally:
                    db.close()
                
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
