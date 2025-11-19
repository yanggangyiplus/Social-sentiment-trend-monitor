"""
감정 분석 유틸리티 모듈
"""
from typing import Dict, Any
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import load_config
from .kobert_analyzer import KoBERTAnalyzer
from .kcbert_analyzer import KcBERTAnalyzer
from .rule_based_analyzer import RuleBasedAnalyzer
from .llm_analyzer import LLMAnalyzer


class SentimentAnalyzer:
    """
    감정 분석기 통합 클래스
    """
    
    def __init__(self, config_path: str = "configs/config_sentiment.yaml"):
        """
        감정 분석기 초기화
        
        Args:
            config_path: 설정 파일 경로
        """
        self.config = load_config(config_path)
        model_config = self.config.get("model", {})
        model_type = model_config.get("type", "kcbert")  # 기본값을 kcbert로 변경
        
        if model_type == "kcbert":
            # KcBERT 모델 사용 (AI 허브 한국어 감정 데이터셋 기반)
            model_name = model_config.get("model_name", "beomi/KcBERT-base")
            fine_tuned_path = model_config.get("fine_tuned_model_path", None)
            self.analyzer = KcBERTAnalyzer(model_name, fine_tuned_path)
        elif model_type == "kobert":
            model_name = model_config.get("model_name", "monologg/kobert")
            self.analyzer = KoBERTAnalyzer(model_name)
        elif model_type == "rule_based":
            # 규칙 기반 분석기 사용 (빠르고 안정적, 정확도는 중간)
            self.analyzer = RuleBasedAnalyzer()
        elif model_type == "llm":
            llm_config = model_config.get("llm", {})
            self.analyzer = LLMAnalyzer(
                provider=llm_config.get("provider", "openai"),
                model_name=llm_config.get("model_name", "gpt-3.5-turbo"),
                api_key=llm_config.get("api_key", ""),
                temperature=llm_config.get("temperature", 0.3)
            )
        else:
            raise ValueError(f"지원하지 않는 모델 타입: {model_type}")
        
        self.model_type = model_type
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        텍스트 감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감정 분석 결과
        """
        result = self.analyzer.analyze(text)
        result["model_type"] = self.model_type
        return result
    
    def analyze_batch(self, texts: list) -> list:
        """
        배치 텍스트 감정 분석
        
        Args:
            texts: 텍스트 리스트
            
        Returns:
            감정 분석 결과 리스트
        """
        results = self.analyzer.analyze_batch(texts)
        for result in results:
            result["model_type"] = self.model_type
        return results

