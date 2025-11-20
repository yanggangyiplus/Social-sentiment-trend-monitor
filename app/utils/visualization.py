"""
시각화 유틸리티 모듈
Plotly 차트 생성 및 Word Cloud 생성 함수
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import io
import platform
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt


def calculate_sentiment_score(positive: float, negative: float, neutral: float) -> float:
    """
    감정 점수 계산 (-1 ~ 1)
    
    Args:
        positive: 긍정 점수
        negative: 부정 점수
        neutral: 중립 점수
    
    Returns:
        감정 스코어 (-1: 부정적, 0: 중립, 1: 긍정적)
    """
    return positive * 1.0 + neutral * 0.0 + negative * (-1.0)


def format_number(num: int) -> str:
    """
    숫자 포맷팅 (예: 1000 -> 1K)
    
    Args:
        num: 포맷팅할 숫자
    
    Returns:
        포맷팅된 문자열
    """
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)


def generate_wordcloud(texts: List[str], sentiment_type: str = "all") -> Optional[io.BytesIO]:
    """
    Word Cloud 생성
    
    Args:
        texts: 텍스트 리스트
        sentiment_type: "positive", "negative", "all"
    
    Returns:
        Word Cloud 이미지 BytesIO 객체
    """
    if not texts:
        return None
    
    # 한국어 폰트 경로 설정
    font_path = None
    system = platform.system()
    
    if system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/AppleGothic.ttf",
            "/Library/Fonts/AppleGothic.ttf",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                break
    elif system == "Windows":
        font_path = "C:/Windows/Fonts/malgun.ttf"  # 맑은 고딕
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
        ]
        for path in font_paths:
            if os.path.exists(path):
                font_path = path
                break
    
    # 텍스트 결합
    text = " ".join(texts)
    
    if not text.strip():
        return None
    
    try:
        # Word Cloud 생성
        wordcloud = WordCloud(
            width=800,
            height=400,
            background_color='white',
            font_path=font_path,
            max_words=100,
            relative_scaling=0.5,
            colormap='viridis'
        ).generate(text)
        
        # 이미지를 BytesIO로 변환
        img_buffer = io.BytesIO()
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    except Exception as e:
        print(f"Word Cloud 생성 실패: {e}")
        return None


def create_donut_chart(sentiment_counts: Dict[str, int], title: str = "감정 분석 분포") -> go.Figure:
    """
    Donut 차트 생성
    
    Args:
        sentiment_counts: 감정 카운트 딕셔너리 (예: {"positive": 10, "negative": 5, "neutral": 15})
        title: 차트 제목
    
    Returns:
        Plotly Figure 객체
    """
    # 딕셔너리에서 값 추출
    if isinstance(sentiment_counts, dict):
        positive = sentiment_counts.get("positive", 0)
        negative = sentiment_counts.get("negative", 0)
        neutral = sentiment_counts.get("neutral", 0)
        total = positive + negative + neutral
        
        if total > 0:
            positive_pct = positive / total
            negative_pct = negative / total
            neutral_pct = neutral / total
        else:
            positive_pct = negative_pct = neutral_pct = 0
    else:
        # 기존 호환성: 개별 값으로 전달된 경우
        positive_pct = sentiment_counts if isinstance(sentiment_counts, (int, float)) else 0
        negative_pct = negative if 'negative' in locals() else 0
        neutral_pct = neutral if 'neutral' in locals() else 0
    
    fig = go.Figure(data=[go.Pie(
        labels=['긍정', '부정', '중립'],
        values=[positive_pct, negative_pct, neutral_pct],
        hole=0.4,
        marker_colors=['#2ecc71', '#e74c3c', '#95a5a6'],
        textinfo='label+percent',
        textposition='outside'
    )])
    fig.update_layout(
        title=title,
        height=350,
        showlegend=True
    )
    return fig


def create_gauge_chart(score: float, title: str = "감정 점수") -> go.Figure:
    """
    Gauge 차트 생성
    
    Args:
        score: 감정 점수 (-1 ~ 1)
        title: 차트 제목
    
    Returns:
        Plotly Figure 객체
    """
    # 점수를 0~100 범위로 변환
    normalized_score = ((score + 1) / 2) * 100
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=normalized_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 33], 'color': "lightgray"},
                {'range': [33, 66], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    fig.update_layout(height=350)
    return fig


def create_bar_chart(avg_positive: float, avg_negative: float, avg_neutral: float, 
                    title: str = "평균 감정 점수 분포") -> go.Figure:
    """
    Bar 차트 생성
    
    Args:
        avg_positive: 평균 긍정 점수
        avg_negative: 평균 부정 점수
        avg_neutral: 평균 중립 점수
        title: 차트 제목
    
    Returns:
        Plotly Figure 객체
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='긍정',
        x=['감정 점수'],
        y=[avg_positive],
        marker_color='#2ecc71',
        text=f'{avg_positive:.2%}',
        textposition='inside'
    ))
    fig.add_trace(go.Bar(
        name='부정',
        x=['감정 점수'],
        y=[avg_negative],
        marker_color='#e74c3c',
        text=f'{avg_negative:.2%}',
        textposition='inside'
    ))
    fig.add_trace(go.Bar(
        name='중립',
        x=['감정 점수'],
        y=[avg_neutral],
        marker_color='#95a5a6',
        text=f'{avg_neutral:.2%}',
        textposition='inside'
    ))
    fig.update_layout(
        title=title,
        barmode='stack',
        height=300,
        showlegend=True,
        yaxis=dict(range=[0, 1], title="비율")
    )
    return fig


def create_trend_chart(df_trend: pd.DataFrame, change_points: List[Any] = None) -> go.Figure:
    """
    트렌드 선 그래프 생성 (변화점 Highlight 포함)
    
    Args:
        df_trend: 트렌드 데이터프레임 (hour, sentiment_score 컬럼 필요)
        change_points: 변화점 리스트
    
    Returns:
        Plotly Figure 객체
    """
    fig = go.Figure()
    
    # 감정 스코어 라인
    fig.add_trace(go.Scatter(
        x=df_trend['hour'],
        y=df_trend['sentiment_score'],
        mode='lines+markers',
        name='감정 스코어',
        line=dict(color='#3498db', width=3),
        marker=dict(size=8),
        fill='tonexty',
        fillcolor='rgba(52, 152, 219, 0.1)'
    ))
    
    # 변화점 Highlight
    if change_points:
        for cp in change_points:
            cp_time = _parse_change_point_time(cp)
            if cp_time is None:
                continue
            
            cp_time_plotly = pd.to_datetime(cp_time)
            
            # 변화점에 수직선 추가
            fig.add_shape(
                type="line",
                x0=cp_time_plotly,
                x1=cp_time_plotly,
                y0=df_trend['sentiment_score'].min() - 0.1,
                y1=df_trend['sentiment_score'].max() + 0.1,
                line=dict(color="red", width=3, dash="dash"),
                opacity=0.7
            )
            
            # 변화점에 주석 추가
            fig.add_annotation(
                x=cp_time_plotly,
                y=df_trend['sentiment_score'].max() + 0.05,
                text="변화점",
                showarrow=True,
                arrowhead=2,
                arrowcolor="red",
                bgcolor="rgba(255, 0, 0, 0.2)",
                bordercolor="red"
            )
    
    fig.update_layout(
        title="감정 트렌드 분석 (변화점 Highlight)",
        xaxis_title="시간",
        yaxis_title="감정 스코어",
        height=500,
        hovermode='x unified'
    )
    
    return fig


def create_emotion_distribution_chart(emotion_stats: Dict[str, Any]) -> go.Figure:
    """
    9가지 감정 분포 차트 생성
    
    Args:
        emotion_stats: 감정 통계 딕셔너리 (emotion_counts, emotion_percentages 포함)
    
    Returns:
        Plotly Figure 객체
    """
    emotion_labels_kr = {
        "anger": "분노",
        "fear": "공포",
        "joy": "기쁨",
        "sadness": "슬픔",
        "surprise": "놀람",
        "disgust": "혐오",
        "trust": "신뢰",
        "anticipation": "기대",
        "neutral": "중립"
    }
    
    emotion_colors = {
        "anger": "#e74c3c",
        "fear": "#9b59b6",
        "joy": "#f39c12",
        "sadness": "#3498db",
        "surprise": "#1abc9c",
        "disgust": "#95a5a6",
        "trust": "#2ecc71",
        "anticipation": "#e67e22",
        "neutral": "#bdc3c7"
    }
    
    emotion_counts = emotion_stats.get("emotion_counts", {})
    emotion_percentages = emotion_stats.get("emotion_percentages", {})
    
    # 데이터 준비
    emotions = list(emotion_counts.keys())
    counts = [emotion_counts.get(e, 0) for e in emotions]
    percentages = [emotion_percentages.get(e, 0) for e in emotions]
    labels_kr = [emotion_labels_kr.get(e, e) for e in emotions]
    colors = [emotion_colors.get(e, "#95a5a6") for e in emotions]
    
    fig = go.Figure(data=[go.Bar(
        x=labels_kr,
        y=counts,
        marker_color=colors,
        text=[f"{p:.1f}%" for p in percentages],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>개수: %{y}<br>비율: %{text}<extra></extra>'
    )])
    
    fig.update_layout(
        title="9가지 감정 분포",
        xaxis_title="감정",
        yaxis_title="개수",
        height=400,
        showlegend=False
    )
    
    return fig


def create_topic_sentiment_chart(topic_results: Dict[str, Any]) -> go.Figure:
    """
    토픽별 감정 분석 차트 생성
    
    Args:
        topic_results: 토픽 분석 결과 딕셔너리
    
    Returns:
        Plotly Figure 객체
    """
    topics = topic_results.get("topics", [])
    
    if not topics:
        # 빈 차트 반환
        fig = go.Figure()
        fig.add_annotation(
            text="토픽 데이터가 없습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(height=300)
        return fig
    
    # 데이터 준비
    topic_labels = []
    positive_scores = []
    negative_scores = []
    neutral_scores = []
    
    for topic in topics[:10]:  # 상위 10개만 표시
        keywords = topic.get("keywords", [])
        sentiment = topic.get("sentiment", {})
        
        if keywords:
            label = ", ".join(keywords[:3])  # 상위 3개 키워드만 표시
            topic_labels.append(label)
            positive_scores.append(sentiment.get("avg_positive", 0))
            negative_scores.append(sentiment.get("avg_negative", 0))
            neutral_scores.append(sentiment.get("avg_neutral", 0))
    
    if not topic_labels:
        fig = go.Figure()
        fig.add_annotation(
            text="토픽 데이터가 없습니다.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        fig.update_layout(height=300)
        return fig
    
    # Stacked bar chart 생성
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='긍정',
        x=topic_labels,
        y=positive_scores,
        marker_color='#2ecc71',
        text=[f"{s:.1%}" for s in positive_scores],
        textposition='inside'
    ))
    fig.add_trace(go.Bar(
        name='부정',
        x=topic_labels,
        y=negative_scores,
        marker_color='#e74c3c',
        text=[f"{s:.1%}" for s in negative_scores],
        textposition='inside'
    ))
    fig.add_trace(go.Bar(
        name='중립',
        x=topic_labels,
        y=neutral_scores,
        marker_color='#95a5a6',
        text=[f"{s:.1%}" for s in neutral_scores],
        textposition='inside'
    ))
    
    fig.update_layout(
        title="토픽별 감정 분석",
        xaxis_title="토픽 (키워드)",
        yaxis_title="평균 감정 점수",
        barmode='stack',
        height=400,
        showlegend=True,
        xaxis=dict(tickangle=-45)
    )
    
    return fig


def _parse_change_point_time(cp: Any) -> Optional[datetime]:
    """
    변화점 시간 파싱 헬퍼 함수
    
    Args:
        cp: 변화점 딕셔너리 또는 문자열
    
    Returns:
        datetime 객체 또는 None
    """
    if isinstance(cp, dict):
        cp_time = cp.get('change_point') or cp.get('timestamp') or cp.get('time')
    elif isinstance(cp, str):
        cp_time = cp
    else:
        return None
    
    if cp_time is None:
        return None
    
    try:
        if isinstance(cp_time, str):
            # ISO 형식 문자열 파싱
            if 'T' in cp_time:
                return pd.to_datetime(cp_time)
            else:
                return pd.to_datetime(cp_time)
        elif isinstance(cp_time, datetime):
            return cp_time
        else:
            return None
    except Exception:
        return None
