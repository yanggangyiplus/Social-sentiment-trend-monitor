#!/usr/bin/env python3
"""
트렌드 탐지 스크립트
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from src.trend.trend_utils import TrendAnalyzer
from src.database.db_manager import init_database, get_db
from src.database.models import SentimentAnalysis, TrendAlert
from src.utils.logger import setup_logger

logger = setup_logger("trend_detection")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="트렌드 탐지 스크립트")
    parser.add_argument("--keyword", type=str, required=True, help="분석할 키워드")
    parser.add_argument("--hours", type=int, default=24, help="분석 기간 (시간)")
    parser.add_argument("--config", type=str, default="configs/config_trend.yaml", help="설정 파일 경로")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"키워드 '{args.keyword}'의 트렌드 탐지 시작")
    print("=" * 70)
    
    # 데이터베이스 초기화
    init_database("sqlite:///data/database/sentiment.db")
    
    # 트렌드 분석기 초기화
    trend_analyzer = TrendAnalyzer(args.config)
    
    # 감정 분석 데이터 조회
    db = next(get_db())
    try:
        start_time = datetime.utcnow() - timedelta(hours=args.hours)
        sentiment_data = db.query(SentimentAnalysis).filter(
            SentimentAnalysis.keyword == args.keyword,
            SentimentAnalysis.analyzed_at >= start_time
        ).all()
        
        if not sentiment_data:
            print(f"키워드 '{args.keyword}'에 대한 데이터를 찾을 수 없습니다.")
            return
        
        logger.info(f"{len(sentiment_data)}개 감정 분석 데이터로 트렌드 분석 시작")
        
        # 데이터 변환
        sentiment_list = []
        for item in sentiment_data:
            sentiment_list.append({
                "analyzed_at": item.analyzed_at,
                "positive_score": item.positive_score,
                "negative_score": item.negative_score,
                "neutral_score": item.neutral_score
            })
        
        # 트렌드 분석 수행
        trend_result = trend_analyzer.analyze_trend(sentiment_list)
        
        print(f"\n트렌드 방향: {trend_result['trend_direction']}")
        print(f"변화점 개수: {len(trend_result['change_points'])}")
        print(f"알림 개수: {len(trend_result['alerts'])}")
        
        # 알림 저장
        if trend_result['alerts']:
            alert_count = 0
            for alert in trend_result['alerts']:
                alert_obj = TrendAlert(
                    keyword=args.keyword,
                    change_type=alert['change_type'],
                    change_rate=alert['change_rate'],
                    change_point=datetime.fromisoformat(alert['change_point']),
                    previous_sentiment=alert['previous_sentiment'],
                    current_sentiment=alert['current_sentiment']
                )
                db.add(alert_obj)
                alert_count += 1
            
            db.commit()
            logger.info(f"{alert_count}개 알림 저장 완료")
            print(f"✅ {alert_count}개 알림 저장 완료")
        
        # 변화점 출력
        if trend_result['change_points']:
            print("\n변화점:")
            for cp in trend_result['change_points']:
                print(f"  - {cp}")
        
        # 알림 출력
        if trend_result['alerts']:
            print("\n알림:")
            for alert in trend_result['alerts']:
                change_type = alert['change_type']
                change_rate = alert['change_rate']
                print(f"  - {change_type}: {change_rate:.1f}% 변화 감지")
    
    except Exception as e:
        db.rollback()
        logger.error(f"트렌드 탐지 실패: {e}")
        print(f"❌ 트렌드 탐지 실패: {e}")
    
    finally:
        db.close()
    
    print("=" * 70)
    print("트렌드 탐지 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()

