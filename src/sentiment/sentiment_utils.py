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
from .emotion_classifier import EmotionClassifier
from .topic_sentiment_analyzer import TopicSentimentAnalyzer


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
        
        # 고급 분석 기능 초기화
        advanced_config = self.config.get("advanced", {})
        self.enable_emotion_classification = advanced_config.get("enable_emotion_classification", False)
        self.enable_topic_sentiment = advanced_config.get("enable_topic_sentiment", False)
        
        if self.enable_emotion_classification:
            self.emotion_classifier = EmotionClassifier()
        else:
            self.emotion_classifier = None
        
        if self.enable_topic_sentiment:
            use_bertopic = advanced_config.get("use_bertopic", True)
            self.topic_sentiment_analyzer = TopicSentimentAnalyzer(use_bertopic=use_bertopic)
        else:
            self.topic_sentiment_analyzer = None
    
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
        
        # 9가지 감정 분류 추가
        if self.enable_emotion_classification and self.emotion_classifier:
            emotion_result = self.emotion_classifier.classify_emotion(text)
            result["emotion"] = emotion_result
        
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
            
            # 9가지 감정 분류 추가
            if self.enable_emotion_classification and self.emotion_classifier:
                text_idx = results.index(result)
                if text_idx < len(texts):
                    emotion_result = self.emotion_classifier.classify_emotion(texts[text_idx])
                    result["emotion"] = emotion_result
        
        return results
    
    def analyze_topics_and_sentiment(self, texts: list, sentiments: list = None) -> Dict[str, Any]:
        """
        토픽 모델링 및 토픽별 감정 분석
        
        Args:
            texts: 텍스트 리스트
            sentiments: 감정 분석 결과 리스트 (선택사항)
        
        Returns:
            토픽 및 감정 분석 결과
        """
        if not self.enable_topic_sentiment or not self.topic_sentiment_analyzer:
            return {
                "topics": [],
                "topic_sentiments": {},
                "method": "none",
                "message": "토픽 분석이 비활성화되어 있습니다."
            }
        
        return self.topic_sentiment_analyzer.analyze_topics_and_sentiment(texts, sentiments)

