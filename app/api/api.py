"""
FastAPI 백엔드 API 서버
실시간 감정 분석 및 트렌드 모니터링을 위한 RESTful API 제공
"""
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.db_manager import init_database, get_db
from src.database.models import CollectedText, SentimentAnalysis, TrendAlert
from src.preprocessing.text_cleaner import TextCleaner
from src.utils.config import load_config
from sqlalchemy.orm import Session
from sqlalchemy import desc

# FastAPI 앱 생성
app = FastAPI(
    title="Social Sentiment & Trend Monitor API",
    description="AI 기반 실시간 감정 분석 & 트렌드 변화 탐지 서비스 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 설정 로드
api_config = load_config("configs/config_api.yaml")

# CORS 설정
cors_config = api_config.get("cors", {})
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config.get("allow_origins", ["*"]),
    allow_credentials=cors_config.get("allow_credentials", True),
    allow_methods=cors_config.get("allow_methods", ["*"]),
    allow_headers=cors_config.get("allow_headers", ["*"]),
)

# 데이터베이스 초기화
db_config = api_config.get("database", {})
init_database(db_config.get("url", "sqlite:///data/database/sentiment.db"))


# Pydantic 모델 정의
class SentimentResponse(BaseModel):
    """감정 분석 응답 모델"""
    id: int
    keyword: str
    source: str
    positive_score: float
    negative_score: float
    neutral_score: float
    predicted_sentiment: str
    analyzed_at: datetime


class TrendResponse(BaseModel):
    """트렌드 분석 응답 모델"""
    keyword: str
    trend_direction: str
    change_points: List[str]
    alerts: List[Dict[str, Any]]


class AlertResponse(BaseModel):
    """알림 응답 모델"""
    id: int
    keyword: str
    change_type: str
    change_rate: float
    change_point: datetime
    previous_sentiment: float
    current_sentiment: float


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "Social Sentiment & Trend Monitor API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/comments/recent")
async def get_recent_comments(
    keyword: Optional[str] = Query(None, description="키워드 필터"),
    source: Optional[str] = Query(None, description="소스 필터"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환 개수"),
    db: Session = Depends(get_db)
):
    """
    최근 수집된 댓글 조회
    
    Args:
        keyword: 키워드 필터
        source: 소스 필터
        limit: 최대 반환 개수
        db: 데이터베이스 세션
        
    Returns:
        댓글 리스트
    """
    query = db.query(CollectedText)
    
    if keyword:
        query = query.filter(CollectedText.keyword == keyword)
    
    if source:
        query = query.filter(CollectedText.source == source)
    
    results = query.order_by(desc(CollectedText.collected_at)).limit(limit).all()
    
    return [
        {
            "id": item.id,
            "keyword": item.keyword,
            "source": item.source,
            "text": item.text,
            "author": item.author,
            "url": item.url,
            "collected_at": item.collected_at.isoformat()
        }
        for item in results
    ]


@app.get("/sentiment/recent", response_model=List[SentimentResponse])
async def get_recent_sentiment(
    keyword: Optional[str] = Query(None, description="키워드 필터"),
    source: Optional[str] = Query(None, description="소스 필터 (youtube, twitter, news, blog)"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환 개수"),
    db: Session = Depends(get_db)
):
    """
    최근 감정 분석 결과 조회
    
    Args:
        keyword: 키워드 필터
        source: 소스 필터
        limit: 최대 반환 개수
        db: 데이터베이스 세션
        
    Returns:
        감정 분석 결과 리스트
    """
    query = db.query(SentimentAnalysis)
    
    if keyword:
        query = query.filter(SentimentAnalysis.keyword == keyword)
    
    if source:
        query = query.filter(SentimentAnalysis.source == source)
    
    results = query.order_by(desc(SentimentAnalysis.analyzed_at)).limit(limit).all()
    
    return results


@app.get("/trend/changes")
async def get_trend_changes(
    keyword: str = Query(..., description="키워드"),
    hours: int = Query(24, ge=1, le=168, description="분석 기간 (시간)"),
    db: Session = Depends(get_db)
):
    """
    트렌드 변화점 조회 (서비스 레이어 사용)
    
    Args:
        keyword: 키워드
        hours: 분석 기간 (시간)
        db: 데이터베이스 세션
        
    Returns:
        트렌드 변화점 정보
    """
    from app.services import trend_service
    
    # 기간 내 감정 분석 데이터 조회
    start_time = datetime.utcnow() - timedelta(hours=hours)
    sentiment_data = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.keyword == keyword,
        SentimentAnalysis.analyzed_at >= start_time
    ).all()
    
    if not sentiment_data:
        raise HTTPException(status_code=404, detail=f"키워드 '{keyword}'에 대한 데이터를 찾을 수 없습니다.")
    
    # 데이터 변환
    sentiment_list = []
    for item in sentiment_data:
        sentiment_list.append({
            "analyzed_at": item.analyzed_at,
            "positive_score": item.positive_score,
            "negative_score": item.negative_score,
            "neutral_score": item.neutral_score
        })
    
    # 트렌드 분석 수행 (서비스 레이어 사용)
    trend_result = trend_service.analyze_trend_with_change_points(sentiment_list)
    
    return {
        "keyword": keyword,
        "change_points": trend_result.get("change_points", []),
        "alerts": trend_result.get("alerts", []),
        "total_data_points": len(sentiment_data)
    }


@app.get("/trend/{keyword}", response_model=TrendResponse)
async def get_trend(
    keyword: str,
    hours: int = Query(24, ge=1, le=168, description="분석 기간 (시간)"),
    db: Session = Depends(get_db)
):
    """
    특정 키워드의 트렌드 조회
    
    Args:
        keyword: 키워드
        hours: 분석 기간 (시간)
        db: 데이터베이스 세션
        
    Returns:
        트렌드 분석 결과
    """
    from src.trend.trend_utils import TrendAnalyzer
    
    # 기간 내 감정 분석 데이터 조회
    start_time = datetime.utcnow() - timedelta(hours=hours)
    sentiment_data = db.query(SentimentAnalysis).filter(
        SentimentAnalysis.keyword == keyword,
        SentimentAnalysis.analyzed_at >= start_time
    ).all()
    
    if not sentiment_data:
        raise HTTPException(status_code=404, detail=f"키워드 '{keyword}'에 대한 데이터를 찾을 수 없습니다.")
    
    # 트렌드 분석 수행
    trend_analyzer = TrendAnalyzer()
    
    # 데이터 변환
    sentiment_list = []
    for item in sentiment_data:
        sentiment_list.append({
            "analyzed_at": item.analyzed_at,
            "positive_score": item.positive_score,
            "negative_score": item.negative_score,
            "neutral_score": item.neutral_score
        })
    
    trend_result = trend_analyzer.analyze_trend(sentiment_list)
    
    return {
        "keyword": keyword,
        "trend_direction": trend_result["trend_direction"],
        "change_points": trend_result["change_points"],
        "alerts": trend_result["alerts"]
    }


@app.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    keyword: Optional[str] = Query(None, description="키워드 필터"),
    limit: int = Query(50, ge=1, le=500, description="최대 반환 개수"),
    db: Session = Depends(get_db)
):
    """
    변화 감지 알림 조회
    
    Args:
        keyword: 키워드 필터
        limit: 최대 반환 개수
        db: 데이터베이스 세션
        
    Returns:
        알림 리스트
    """
    query = db.query(TrendAlert)
    
    if keyword:
        query = query.filter(TrendAlert.keyword == keyword)
    
    results = query.order_by(desc(TrendAlert.change_point)).limit(limit).all()
    
    return results


@app.post("/collect")
async def start_collection(
    keyword: str,
    sources: List[str] = Query(["youtube"], description="수집할 소스 리스트"),
    max_results: int = Query(50, ge=1, le=500, description="소스당 최대 수집 개수")
):
    """
    데이터 수집 시작
    
    Args:
        keyword: 수집할 키워드
        sources: 수집할 소스 리스트
        max_results: 소스당 최대 수집 개수
        
    Returns:
        수집 작업 결과
    """
    from app.services import monitoring_service
    
    try:
        success, count = monitoring_service.run_data_collection(keyword, sources, max_results)
        if success:
            return {
                "message": f"데이터 수집 완료",
                "keyword": keyword,
                "sources": sources,
                "collected_count": count,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail=f"데이터 수집 실패: {count}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"수집 중 오류 발생: {str(e)}")


@app.post("/analyze")
async def start_analysis(
    keyword: str,
    source: str = Query("youtube", description="분석할 소스"),
    hours: int = Query(24, ge=1, le=168, description="분석 기간 (시간)")
):
    """
    감정 분석 시작
    
    Args:
        keyword: 분석할 키워드
        source: 분석할 소스
        hours: 분석 기간 (시간)
        
    Returns:
        분석 작업 결과
    """
    from app.utils import sentiment_analysis
    
    try:
        success, count = sentiment_analysis.run_sentiment_analysis(keyword, source, hours)
        if success:
            return {
                "message": f"감정 분석 완료",
                "keyword": keyword,
                "source": source,
                "analyzed_count": count,
                "status": "success"
            }
        else:
            raise HTTPException(status_code=500, detail=f"감정 분석 실패: {count}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.get("/keywords")
async def get_keywords(
    limit: int = Query(100, ge=1, le=1000, description="최대 반환 개수"),
    db: Session = Depends(get_db)
):
    """
    등록된 키워드 목록 조회
    
    Args:
        limit: 최대 반환 개수
        db: 데이터베이스 세션
        
    Returns:
        키워드 리스트
    """
    keywords = db.query(SentimentAnalysis.keyword).distinct().limit(limit).all()
    return [kw[0] for kw in keywords]


if __name__ == "__main__":
    import uvicorn
    server_config = api_config.get("server", {})
    uvicorn.run(
        "app.api:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", True)
    )

