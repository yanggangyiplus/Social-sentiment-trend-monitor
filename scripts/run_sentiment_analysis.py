#!/usr/bin/env python3
"""
감정 분석 스크립트
"""
import sys
import argparse
import re
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from src.sentiment.sentiment_utils import SentimentAnalyzer
from src.database.db_manager import init_database, get_db
from src.database.models import CollectedText, SentimentAnalysis
from src.preprocessing.text_cleaner import TextCleaner
from src.utils.logger import setup_logger

logger = setup_logger("sentiment_analysis")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="감정 분석 스크립트")
    parser.add_argument("--keyword", type=str, help="분석할 키워드 (지정하지 않으면 모든 미분석 데이터 분석)")
    parser.add_argument("--hours", type=int, default=24, help="분석할 데이터의 시간 범위 (시간)")
    parser.add_argument("--config", type=str, default="configs/config_sentiment.yaml", help="설정 파일 경로")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("감정 분석 시작")
    print("=" * 70)
    
    # 데이터베이스 초기화
    init_database("sqlite:///data/database/sentiment.db")
    
    # 감정 분석기 초기화
    sentiment_analyzer = SentimentAnalyzer(args.config)
    
    # 데이터 조회
    db = next(get_db())
    try:
        query = db.query(CollectedText)
        
        if args.keyword:
            query = query.filter(CollectedText.keyword == args.keyword)
        
        # 시간 범위 필터
        start_time = datetime.utcnow() - timedelta(hours=args.hours)
        query = query.filter(CollectedText.collected_at >= start_time)
        
        # 이미 분석된 텍스트 제외
        analyzed_text_ids = db.query(SentimentAnalysis.text_id).subquery()
        query = query.filter(~CollectedText.id.in_(analyzed_text_ids))
        
        texts_to_analyze = query.all()
        logger.info(f"{len(texts_to_analyze)}개 텍스트 분석 시작")
        
        if not texts_to_analyze:
            print("분석할 데이터가 없습니다.")
            return
        
        # 전처리기 초기화
        text_cleaner = TextCleaner()
        
        # 규칙 기반 분석기 사용 시 전처리 최소화
        use_minimal_preprocessing = sentiment_analyzer.model_type == "rule_based"
        
        # 감정 분석 수행
        analyzed_count = 0
        for text_obj in texts_to_analyze:
            try:
                # 텍스트 전처리
                if use_minimal_preprocessing:
                    # 규칙 기반 분석기: 최소한의 전처리만 (URL, HTML 태그만 제거)
                    cleaned_text = text_obj.text
                    cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)  # HTML 태그 제거
                    cleaned_text = re.sub(r'http[s]?://\S+', '', cleaned_text)  # URL 제거
                    cleaned_text = cleaned_text.strip()
                else:
                    cleaned_text = text_cleaner.clean_text_for_sentiment(text_obj.text)
                
                # 빈 텍스트 필터링
                if not cleaned_text or len(cleaned_text.strip()) < 1:
                    logger.warning(f"텍스트 ID {text_obj.id}: 전처리 후 텍스트가 너무 짧음")
                    continue
                
                # 감정 분석
                result = sentiment_analyzer.analyze(cleaned_text)
                
                # 결과 저장
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
                
                if analyzed_count % 10 == 0:
                    db.commit()
                    print(f"진행 중... {analyzed_count}/{len(texts_to_analyze)}")
            
            except Exception as e:
                logger.error(f"텍스트 ID {text_obj.id} 분석 실패: {e}")
                continue
        
        db.commit()
        logger.info(f"{analyzed_count}개 텍스트 분석 완료")
        print(f"✅ {analyzed_count}개 텍스트 분석 완료")
    
    except Exception as e:
        db.rollback()
        logger.error(f"감정 분석 실패: {e}")
        print(f"❌ 감정 분석 실패: {e}")
    
    finally:
        db.close()
    
    print("=" * 70)
    print("감정 분석 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()

