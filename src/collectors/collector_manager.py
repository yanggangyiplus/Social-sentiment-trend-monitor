"""
수집기 관리자 모듈
collect() → parse_response() → save_to_db() 구조로 명확화
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import load_config
from src.database.db_manager import init_database, get_db
from .youtube_collector import YouTubeCollector
from .twitter_collector import TwitterCollector
from .news_collector import NewsCollector
from .blog_collector import BlogCollector


class CollectorManager:
    """
    데이터 수집기 관리 클래스
    collect() → parse_response() → save_to_db() 파이프라인 관리
    """
    
    def __init__(self, config_path: str = "configs/config_collector.yaml"):
        """
        수집기 관리자 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config = load_config(config_path)
        self.collectors = {}
        
        # 각 소스별 수집기 초기화
        sources_config = self.config.get("sources", {})
        
        if sources_config.get("youtube", {}).get("enabled", False):
            self.collectors["youtube"] = YouTubeCollector(sources_config["youtube"])
        
        if sources_config.get("twitter", {}).get("enabled", False):
            self.collectors["twitter"] = TwitterCollector(sources_config["twitter"])
        
        if sources_config.get("news", {}).get("enabled", False):
            self.collectors["news"] = NewsCollector(sources_config["news"])
        
        if sources_config.get("blog", {}).get("enabled", False):
            self.collectors["blog"] = BlogCollector(sources_config["blog"])
        
        # 데이터베이스 초기화
        storage_config = self.config.get("storage", {})
        db_path = storage_config.get("database_path", "data/database/sentiment.db")
        init_database(f"sqlite:///{db_path}")
    
    def collect_all(self, keyword: str, max_results_per_source: int = 50, 
                   save_to_database: bool = True) -> List[Dict[str, Any]]:
        """
        모든 활성화된 소스에서 데이터 수집 및 저장
        
        Args:
            keyword: 검색 키워드
            max_results_per_source: 소스당 최대 수집 개수
            save_to_database: 데이터베이스 저장 여부
            
        Returns:
            수집된 데이터 리스트
        """
        all_results = []
        
        # 데이터베이스 세션 준비
        db_session = None
        if save_to_database:
            db_session = next(get_db())
        
        try:
            for source_name, collector in self.collectors.items():
                print(f"\n{'='*70}")
                print(f"[{source_name.upper()}] 데이터 수집 시작")
                print(f"{'='*70}")
                
                # 1단계: collect() - 데이터 수집
                results = collector.collect(keyword, max_results_per_source)
                print(f"[{source_name}] 수집 완료: {len(results)}개")
                
                # 2단계: save_to_db() - 데이터베이스 저장
                if save_to_database and db_session and hasattr(collector, 'save_to_db'):
                    collector.save_to_db(results, keyword, db_session)
                
                all_results.extend(results)
            
            if save_to_database and db_session:
                print(f"\n{'='*70}")
                print(f"전체 수집 완료: 총 {len(all_results)}개 데이터")
                print(f"{'='*70}")
        
        except Exception as e:
            print(f"수집 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            if db_session:
                db_session.rollback()
        
        finally:
            if db_session:
                db_session.close()
        
        return all_results
    
    def collect_and_save(self, keyword: str, max_results_per_source: int = 50) -> int:
        """
        데이터 수집 및 저장 (간편 메서드)
        
        Args:
            keyword: 검색 키워드
            max_results_per_source: 소스당 최대 수집 개수
            
        Returns:
            저장된 데이터 개수
        """
        results = self.collect_all(keyword, max_results_per_source, save_to_database=True)
        return len(results)

