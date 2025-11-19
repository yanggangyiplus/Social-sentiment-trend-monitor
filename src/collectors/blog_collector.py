"""
블로그 데이터 수집기
v0 버전: Mock Data 반환 (실제 API 연동은 v1에서 구현)
"""
from typing import List, Dict, Any
import random
from .base_collector import BaseCollector


class BlogCollector(BaseCollector):
    """
    블로그 포스트 수집기 (Mock Data)
    v0: Mock Data 반환
    v1: 실제 API 연동 예정
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        블로그 수집기 초기화
        
        Args:
            config: 블로그 설정 딕셔너리
        """
        super().__init__(config)
        self.max_posts = config.get("max_posts", 50)
    
    def collect(self, keyword: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        블로그에서 키워드 기반 포스트 수집 (Mock Data)
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 수집 개수
            
        Returns:
            수집된 데이터 리스트 (Mock Data)
        """
        if not self.enabled:
            return []
        
        max_results = max_results or self.max_posts
        
        # Mock Data 생성
        mock_posts = [
            f"{keyword}에 대한 블로그 리뷰입니다. 추천합니다!",
            f"{keyword} 사용 후기입니다. 만족스러워요.",
            f"{keyword} 관련 정보를 공유합니다.",
            f"{keyword}에 대한 부정적인 경험이 있었습니다.",
            f"{keyword} 비교 분석 포스트입니다.",
        ]
        
        results = []
        for i in range(min(max_results, len(mock_posts) * 10)):
            text = random.choice(mock_posts)
            if i >= len(mock_posts):
                text = f"{keyword} 관련 블로그 포스트 {i+1}"
            
            result = self._create_result(
                text=text,
                author=f"blogger_{i+1}",
                url=f"https://blog.example.com/post/{2000+i}",
                source="blog",
                source_url="https://blog.example.com"
            )
            results.append(result)
        
        print(f"Blog Mock Data: {len(results)}개 생성")
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
                    source=item.get('source', 'blog'),
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

