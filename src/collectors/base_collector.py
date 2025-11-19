"""
기본 수집기 클래스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime


class BaseCollector(ABC):
    """
    데이터 수집기 기본 클래스
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        수집기 초기화
        
        Args:
            config: 수집기 설정 딕셔너리
        """
        self.config = config
        self.enabled = config.get("enabled", False)
    
    @abstractmethod
    def collect(self, keyword: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        키워드 기반 데이터 수집
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 수집 개수
            
        Returns:
            수집된 데이터 리스트 (각 항목은 text, author, url, source 등을 포함)
        """
        pass
    
    def _create_result(self, text: str, author: str = None, url: str = None, 
                      source: str = None, **kwargs) -> Dict[str, Any]:
        """
        수집 결과 딕셔너리 생성
        
        Args:
            text: 텍스트 내용
            author: 작성자
            url: 원본 URL
            source: 소스 이름
            **kwargs: 추가 필드
            
        Returns:
            수집 결과 딕셔너리
        """
        return {
            "text": text,
            "author": author,
            "url": url,
            "source": source or self.__class__.__name__.lower().replace("collector", ""),
            "collected_at": datetime.utcnow(),
            **kwargs
        }

