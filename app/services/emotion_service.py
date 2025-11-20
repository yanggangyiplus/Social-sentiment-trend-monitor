"""
감정 분석 고급 기능 서비스
9가지 감정 분류 및 토픽-감정 분석 통합
"""
from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.sentiment.sentiment_utils import SentimentAnalyzer
from src.sentiment.emotion_classifier import EmotionClassifier
from src.sentiment.topic_sentiment_analyzer import TopicSentimentAnalyzer
from app.web.utils.logger_config import app_logger as logger


class EmotionService:
    """
    감정 분석 고급 기능 서비스 클래스
    """
    
    def __init__(self, sentiment_analyzer: Optional[SentimentAnalyzer] = None):
        """
        감정 서비스 초기화
        
        Args:
            sentiment_analyzer: SentimentAnalyzer 인스턴스 (선택사항)
        """
        self.sentiment_analyzer = sentiment_analyzer
        self.emotion_classifier = EmotionClassifier()
        self.topic_sentiment_analyzer = None  # 필요시 초기화
    
    def analyze_emotions_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        배치 텍스트에 대한 9가지 감정 분류
        
        Args:
            texts: 분석할 텍스트 리스트
        
        Returns:
            감정 분류 결과 리스트
        """
        results = []
        for text in texts:
            try:
                emotion_result = self.emotion_classifier.classify_emotion(text)
                results.append({
                    "text": text,
                    **emotion_result
                })
            except Exception as e:
                logger.error(f"감정 분류 실패: {e}", exc_info=True)
                results.append({
                    "text": text,
                    "emotion_scores": {},
                    "predicted_emotion": "neutral",
                    "confidence": 0.0
                })
        
        return results
    
    def get_emotion_statistics(self, emotion_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        감정 분류 결과 통계 계산
        
        Args:
            emotion_results: 감정 분류 결과 리스트
        
        Returns:
            감정 통계 딕셔너리
        """
        if not emotion_results:
            return {
                "total": 0,
                "emotion_counts": {},
                "emotion_percentages": {},
                "emotion_distribution": {}
            }
        
        emotion_counts = defaultdict(int)
        total_confidence = defaultdict(float)
        
        for result in emotion_results:
            predicted = result.get("predicted_emotion", "neutral")
            confidence = result.get("confidence", 0.0)
            emotion_counts[predicted] += 1
            total_confidence[predicted] += confidence
        
        total = len(emotion_results)
        emotion_percentages = {
            emotion: (count / total * 100) if total > 0 else 0
            for emotion, count in emotion_counts.items()
        }
        
        # 평균 신뢰도 계산
        emotion_avg_confidence = {
            emotion: (total_confidence[emotion] / count) if count > 0 else 0
            for emotion, count in emotion_counts.items()
        }
        
        return {
            "total": total,
            "emotion_counts": dict(emotion_counts),
            "emotion_percentages": emotion_percentages,
            "emotion_avg_confidence": emotion_avg_confidence,
            "emotion_distribution": emotion_percentages
        }
    
    def analyze_topics_with_sentiment(
        self, 
        texts: List[str], 
        sentiments: Optional[List[Dict[str, Any]]] = None,
        use_bertopic: bool = True
    ) -> Dict[str, Any]:
        """
        토픽 모델링 및 토픽별 감정 분석
        
        Args:
            texts: 텍스트 리스트
            sentiments: 감정 분석 결과 리스트 (선택사항)
            use_bertopic: BERTopic 사용 여부
        
        Returns:
            토픽 및 감정 분석 결과
        """
        if not texts:
            return {
                "topics": [],
                "topic_sentiments": {},
                "method": "none"
            }
        
        # TopicSentimentAnalyzer 초기화 (필요시)
        if self.topic_sentiment_analyzer is None:
            self.topic_sentiment_analyzer = TopicSentimentAnalyzer(use_bertopic=use_bertopic)
        
        try:
            return self.topic_sentiment_analyzer.analyze_topics_and_sentiment(texts, sentiments)
        except Exception as e:
            logger.error(f"토픽-감정 분석 실패: {e}", exc_info=True)
            return {
                "topics": [],
                "topic_sentiments": {},
                "method": "error",
                "error": str(e)
            }
    
    def get_emotion_label_kr(self, emotion: str) -> str:
        """
        감정 영어명을 한국어로 변환
        
        Args:
            emotion: 감정 영어명
        
        Returns:
            한국어 감정명
        """
        return self.emotion_classifier.get_emotion_label_kr(emotion)

