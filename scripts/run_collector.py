#!/usr/bin/env python3
"""
데이터 수집 스크립트
"""
import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from src.collectors.collector_manager import CollectorManager
from src.preprocessing.text_cleaner import TextCleaner
from src.preprocessing.deduplicator import Deduplicator
from src.database.db_manager import init_database
from src.database.models import CollectedText
from src.utils.logger import setup_logger

logger = setup_logger("collector")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="데이터 수집 스크립트")
    parser.add_argument("--keyword", type=str, required=True, help="수집할 키워드")
    parser.add_argument("--max-results", type=int, default=50, help="소스당 최대 수집 개수")
    parser.add_argument("--config", type=str, default="configs/config_collector.yaml", help="설정 파일 경로")
    
    args = parser.parse_args()
    
    print("=" * 70)
    print(f"키워드 '{args.keyword}'에 대한 데이터 수집 시작")
    print("=" * 70)
    
    # 데이터베이스 초기화
    init_database("sqlite:///data/database/sentiment.db")
    
    # 수집기 관리자 초기화
    collector_manager = CollectorManager(args.config)
    
    # 데이터 수집 및 저장 (collect_and_save 메서드가 자동으로 저장 처리)
    logger.info(f"키워드 '{args.keyword}' 수집 시작")
    
    # collect_all 메서드가 자동으로 데이터베이스에 저장함
    collected_data = collector_manager.collect_all(
        args.keyword, 
        args.max_results, 
        save_to_database=True
    )
    
    logger.info(f"총 {len(collected_data)}개 데이터 수집 및 저장 완료")
    
    if not collected_data:
        print("수집된 데이터가 없습니다.")
        return
    
    # 전처리는 감정 분석 단계에서 수행
    print("\n✅ 데이터 수집 및 저장 완료!")
    print(f"   - 총 수집 데이터: {len(collected_data)}개")
    print(f"   - 다음 단계: python scripts/run_sentiment_analysis.py --keyword {args.keyword}")
    
    print("=" * 70)
    print("데이터 수집 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()

