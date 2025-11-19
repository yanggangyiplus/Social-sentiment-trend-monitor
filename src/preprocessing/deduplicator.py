"""
중복 제거 모듈
"""
from typing import List, Dict, Any
import hashlib


class Deduplicator:
    """
    중복 데이터 제거 클래스
    """
    
    @staticmethod
    def compute_hash(text: str) -> str:
        """
        텍스트의 해시값 계산
        
        Args:
            text: 텍스트
            
        Returns:
            해시값
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def remove_duplicates(data_list: List[Dict[str, Any]], 
                         key_field: str = "text") -> List[Dict[str, Any]]:
        """
        중복 데이터 제거
        
        Args:
            data_list: 데이터 리스트
            key_field: 중복 판단 기준 필드
            
        Returns:
            중복 제거된 데이터 리스트
        """
        seen_hashes = set()
        unique_data = []
        
        for item in data_list:
            text = item.get(key_field, "")
            if not text:
                continue
            
            text_hash = Deduplicator.compute_hash(text)
            
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_data.append(item)
        
        return unique_data
    
    @staticmethod
    def remove_similar(data_list: List[Dict[str, Any]], 
                      similarity_threshold: float = 0.9) -> List[Dict[str, Any]]:
        """
        유사한 텍스트 제거 (간단한 구현)
        
        Args:
            data_list: 데이터 리스트
            similarity_threshold: 유사도 임계값
            
        Returns:
            유사도가 낮은 데이터 리스트
        """
        # 간단한 구현: 정확한 중복만 제거
        # 실제로는 더 정교한 유사도 계산 필요 (예: Jaccard similarity, TF-IDF 등)
        return Deduplicator.remove_duplicates(data_list)

