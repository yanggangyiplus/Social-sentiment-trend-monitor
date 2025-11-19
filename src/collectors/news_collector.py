"""
뉴스 데이터 수집기
v0 버전: Mock Data 반환 (실제 API 연동은 v1에서 구현)
"""
from typing import List, Dict, Any
import random
from .base_collector import BaseCollector


class NewsCollector(BaseCollector):
    """
    뉴스 기사 수집기 (Mock Data)
    v0: Mock Data 반환
    v1: 실제 API 연동 예정
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        뉴스 수집기 초기화
        
        Args:
            config: 뉴스 설정 딕셔너리
        """
        super().__init__(config)
        self.max_articles = config.get("max_articles", 50)
    
    def collect(self, keyword: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        뉴스에서 키워드 기반 기사 수집 (Mock Data)
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 수집 개수
            
        Returns:
            수집된 데이터 리스트 (Mock Data)
        """
        if not self.enabled:
            return []
        
        max_results = max_results or self.max_articles
        
        # Mock Data 생성
        mock_articles = [
            f"{keyword} 관련 최신 뉴스입니다. 긍정적인 전망이 나오고 있습니다.",
            f"{keyword}에 대한 부정적인 보도가 있었습니다.",
            f"{keyword} 관련 중립적인 기사입니다.",
            f"{keyword}의 새로운 소식이 전해졌습니다.",
            f"{keyword}에 대한 분석 기사입니다.",
        ]
        
        results = []
        for i in range(min(max_results, len(mock_articles) * 10)):
            text = random.choice(mock_articles)
            if i >= len(mock_articles):
                text = f"{keyword} 관련 뉴스 기사 {i+1}"
            
            result = self._create_result(
                text=text,
                author=f"기자_{i+1}",
                url=f"https://news.example.com/article/{1000+i}",
                source="news",
                source_url="https://news.example.com"
            )
            results.append(result)
        
        print(f"News Mock Data: {len(results)}개 생성")
        return results
    
    def save_to_db(self, data: List[Dict[str, Any]], keyword: str, db_session):
        """
        수집된 데이터를 데이터베이스에 저장
        
        Args:
            data: 수집된 데이터 리스트
            keyword: 키워드
            db_session: 데이터베이스 세션
        """
        from src.database.models import CollectedText
        
        saved_count = 0
        for item in data:
            try:
                text_obj = CollectedText(
                    keyword=keyword,
                    source=item.get('source', 'news'),
                    text=item.get('text', ''),
                    author=item.get('author'),
                    url=item.get('url'),
                    collected_at=item.get('collected_at')
                )
                db_session.add(text_obj)
                saved_count += 1
            except Exception as e:
                print(f"데이터 저장 실패: {e}")
                continue
        
        try:
            db_session.commit()
            print(f"✅ {saved_count}개 데이터 저장 완료")
        except Exception as e:
            db_session.rollback()
            print(f"❌ 데이터베이스 커밋 실패: {e}")

