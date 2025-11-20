"""
토픽 + 감정 동시 분석 모듈
BERTopic을 사용한 토픽 모델링 및 토픽별 감정 분석
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

# BERTopic은 선택적 의존성 (설치되어 있으면 사용)
try:
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer
    BERTOPIC_AVAILABLE = True
except ImportError:
    BERTOPIC_AVAILABLE = False
    logger.warning("BERTopic이 설치되지 않았습니다. 간단한 키워드 기반 토픽 분석을 사용합니다.")


class TopicSentimentAnalyzer:
    """
    토픽 모델링 + 감정 분석 통합 클래스
    """
    
    def __init__(self, use_bertopic: bool = True):
        """
        토픽-감정 분석기 초기화
        
        Args:
            use_bertopic: BERTopic 사용 여부 (False면 키워드 기반 사용)
        """
        self.use_bertopic = use_bertopic and BERTOPIC_AVAILABLE
        self.topic_model = None
        
        if self.use_bertopic:
            try:
                # 한국어 모델 사용
                self.embedding_model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
                self.topic_model = BERTopic(
                    embedding_model=self.embedding_model,
                    language='korean',
                    calculate_probabilities=True,
                    verbose=False
                )
                logger.info("BERTopic 모델 초기화 완료")
            except Exception as e:
                logger.warning(f"BERTopic 초기화 실패: {e}. 키워드 기반 분석으로 전환합니다.")
                self.use_bertopic = False
    
    def analyze_topics_and_sentiment(
        self, 
        texts: List[str], 
        sentiments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        토픽 모델링 및 토픽별 감정 분석
        
        Args:
            texts: 텍스트 리스트
            sentiments: 감정 분석 결과 리스트 (선택사항)
        
        Returns:
            토픽 및 감정 분석 결과
        """
        if not texts:
            return {
                "topics": [],
                "topic_sentiments": {},
                "method": "none"
            }
        
        if self.use_bertopic and self.topic_model:
            return self._analyze_with_bertopic(texts, sentiments)
        else:
            return self._analyze_with_keywords(texts, sentiments)
    
    def _analyze_with_bertopic(
        self, 
        texts: List[str], 
        sentiments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        BERTopic을 사용한 토픽 분석
        
        Args:
            texts: 텍스트 리스트
            sentiments: 감정 분석 결과 리스트
        
        Returns:
            토픽 분석 결과
        """
        try:
            # 토픽 모델링
            topics, probs = self.topic_model.fit_transform(texts)
            
            # 토픽 정보 추출
            topic_info = self.topic_model.get_topic_info()
            
            # 토픽별 텍스트 그룹화
            topic_texts = defaultdict(list)
            topic_sentiments = defaultdict(list)
            
            for idx, (text, topic) in enumerate(zip(texts, topics)):
                if topic != -1:  # -1은 이상치 토픽
                    topic_texts[topic].append(text)
                    if sentiments and idx < len(sentiments):
                        topic_sentiments[topic].append(sentiments[idx])
            
            # 토픽별 감정 분석
            topic_sentiment_scores = {}
            for topic_id in topic_texts.keys():
                if topic_sentiments[topic_id]:
                    # 평균 감정 점수 계산
                    avg_positive = np.mean([s.get('positive_score', 0) for s in topic_sentiments[topic_id]])
                    avg_negative = np.mean([s.get('negative_score', 0) for s in topic_sentiments[topic_id]])
                    avg_neutral = np.mean([s.get('neutral_score', 0) for s in topic_sentiments[topic_id]])
                    
                    topic_sentiment_scores[topic_id] = {
                        "avg_positive": float(avg_positive),
                        "avg_negative": float(avg_negative),
                        "avg_neutral": float(avg_neutral),
                        "count": len(topic_sentiments[topic_id])
                    }
            
            # 토픽 키워드 추출
            topic_keywords = {}
            for topic_id in topic_texts.keys():
                topic_words = self.topic_model.get_topic(topic_id)
                if topic_words:
                    topic_keywords[topic_id] = [word for word, _ in topic_words[:5]]  # 상위 5개
            
            return {
                "topics": [
                    {
                        "topic_id": int(topic_id),
                        "keywords": topic_keywords.get(topic_id, []),
                        "count": len(topic_texts[topic_id]),
                        "sentiment": topic_sentiment_scores.get(topic_id, {})
                    }
                    for topic_id in topic_texts.keys()
                ],
                "topic_sentiments": topic_sentiment_scores,
                "method": "bertopic"
            }
            
        except Exception as e:
            logger.error(f"BERTopic 분석 실패: {e}", exc_info=True)
            # 실패 시 키워드 기반으로 전환
            return self._analyze_with_keywords(texts, sentiments)
    
    def _analyze_with_keywords(
        self, 
        texts: List[str], 
        sentiments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        키워드 기반 간단한 토픽 분석
        
        Args:
            texts: 텍스트 리스트
            sentiments: 감정 분석 결과 리스트
        
        Returns:
            토픽 분석 결과
        """
        from collections import Counter
        import re
        
        # 공통 키워드 추출 (2글자 이상)
        all_words = []
        for text in texts:
            # 한국어 단어 추출
            words = re.findall(r'[가-힣]{2,}', text)
            all_words.extend(words)
        
        # 빈도수 기반 토픽 키워드
        word_freq = Counter(all_words)
        top_keywords = [word for word, count in word_freq.most_common(10) if count >= 2]
        
        # 키워드별 텍스트 그룹화
        keyword_texts = defaultdict(list)
        keyword_sentiments = defaultdict(list)
        
        for idx, text in enumerate(texts):
            for keyword in top_keywords:
                if keyword in text:
                    keyword_texts[keyword].append(text)
                    if sentiments and idx < len(sentiments):
                        keyword_sentiments[keyword].append(sentiments[idx])
                    break  # 첫 번째 매칭만
        
        # 키워드별 감정 분석
        keyword_sentiment_scores = {}
        for keyword in keyword_texts.keys():
            if keyword_sentiments[keyword]:
                avg_positive = np.mean([s.get('positive_score', 0) for s in keyword_sentiments[keyword]])
                avg_negative = np.mean([s.get('negative_score', 0) for s in keyword_sentiments[keyword]])
                avg_neutral = np.mean([s.get('neutral_score', 0) for s in keyword_sentiments[keyword]])
                
                keyword_sentiment_scores[keyword] = {
                    "avg_positive": float(avg_positive),
                    "avg_negative": float(avg_negative),
                    "avg_neutral": float(avg_neutral),
                    "count": len(keyword_sentiments[keyword])
                }
        
        return {
            "topics": [
                {
                    "topic_id": idx,
                    "keywords": [keyword],
                    "count": len(keyword_texts[keyword]),
                    "sentiment": keyword_sentiment_scores.get(keyword, {})
                }
                for idx, keyword in enumerate(top_keywords[:5])  # 상위 5개
            ],
            "topic_sentiments": keyword_sentiment_scores,
            "method": "keyword_based"
        }

