"""
Twitter(X) 데이터 수집기
v0 버전: Mock Data 반환 (실제 API 연동은 v2에서 구현)
"""
from typing import List, Dict, Any
from datetime import datetime
import random
from .base_collector import BaseCollector


class TwitterCollector(BaseCollector):
    """
    Twitter(X) 트윗 수집기 (Mock Data)
    v0: Mock Data 반환
    v2: 실제 API 연동 예정
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Twitter 수집기 초기화
        
        Args:
            config: Twitter 설정 딕셔너리
        """
        super().__init__(config)
        self.max_tweets = config.get("max_tweets", 100)
    
    def collect(self, keyword: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Twitter에서 키워드 기반 트윗 수집 (Mock Data)
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 수집 개수
            
        Returns:
            수집된 데이터 리스트 (Mock Data)
        """
        if not self.enabled:
            return []
        
        max_results = max_results or self.max_tweets
        
        # Mock Data 생성
        mock_tweets = [
            f"{keyword}에 대한 긍정적인 의견입니다. 좋은 제품이에요!",
            f"{keyword} 관련해서 부정적인 경험이 있었습니다.",
            f"{keyword}에 대해 중립적인 입장입니다.",
            f"{keyword}를 사용해본 결과 만족스럽습니다.",
            f"{keyword}에 대한 다양한 의견이 있네요.",
        ]
        
        results = []
        for i in range(min(max_results, len(mock_tweets) * 10)):
            text = random.choice(mock_tweets)
            if i >= len(mock_tweets):
                text = f"{keyword} 관련 트윗 {i+1}"
            
            result = self._create_result(
                text=text,
                author=f"user_{i+1}",
                url=f"https://twitter.com/user_{i+1}/status/{1000000+i}",
                source="twitter",
                tweet_id=f"{1000000+i}"
            )
            results.append(result)
        
        print(f"Twitter Mock Data: {len(results)}개 생성")
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
                    source=item.get('source', 'twitter'),
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

