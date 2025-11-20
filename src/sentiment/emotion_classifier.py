"""
9가지 감정 분류기
anger, fear, joy, sadness, surprise, disgust, trust, anticipation, neutral
"""
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class EmotionClassifier:
    """
    9가지 감정 분류 클래스
    Ekman의 기본 감정 + Plutchik의 감정 휠 기반
    """
    
    # 감정별 키워드 매핑 (한국어)
    EMOTION_KEYWORDS = {
        "anger": [
            "화나", "짜증", "분노", "열받", "빡치", "미워", "싫어", "혐오",
            "증오", "욕", "욕설", "개빡", "빡쳐", "빡침", "열받아", "화남"
        ],
        "fear": [
            "무서워", "두려워", "걱정", "불안", "공포", "겁나", "무섭", "불안해",
            "걱정돼", "불안감", "공포감", "두려움", "겁", "무서움"
        ],
        "joy": [
            "기쁘", "행복", "즐거워", "신나", "좋아", "사랑", "만족", "기쁨",
            "행복해", "즐거움", "신남", "좋아해", "사랑해", "만족해", "예쁘", "귀엽"
        ],
        "sadness": [
            "슬퍼", "우울", "서러워", "아쉬워", "후회", "그리워", "슬픔", "우울해",
            "서러움", "아쉬움", "후회돼", "그리움", "슬프", "우울함"
        ],
        "surprise": [
            "놀라", "신기", "대박", "와", "헐", "어", "놀라워", "신기해",
            "놀람", "신기함", "놀라움", "놀랍", "대단", "와우"
        ],
        "disgust": [
            "역겨워", "더러워", "싫어", "혐오", "징그러워", "역겹", "더럽", "혐오스러워",
            "역겨움", "더러움", "혐오감", "징그러움"
        ],
        "trust": [
            "믿어", "신뢰", "확신", "믿음", "신뢰해", "확신해", "믿고", "신뢰감",
            "믿음직", "신뢰할", "확신함"
        ],
        "anticipation": [
            "기대", "설레", "기다려", "기대돼", "설레어", "기다림", "기대감", "설렘",
            "기대해", "설레임", "기다려져"
        ],
        "neutral": [
            # 중립 키워드는 명시적으로 정의하지 않음 (기본값)
        ]
    }
    
    def __init__(self):
        """감정 분류기 초기화"""
        pass
    
    def classify_emotion(self, text: str) -> Dict[str, float]:
        """
        9가지 감정으로 분류
        
        Args:
            text: 분석할 텍스트
        
        Returns:
            감정별 점수 딕셔너리
        """
        text_lower = text.lower()
        
        # 각 감정별 점수 계산
        emotion_scores = {}
        total_matches = 0
        
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            if emotion == "neutral":
                continue
            
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    total_matches += 1
            
            emotion_scores[emotion] = score
        
        # 정규화
        if total_matches > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] = emotion_scores[emotion] / total_matches
        else:
            # 매칭이 없으면 중립
            emotion_scores["neutral"] = 1.0
        
        # 중립 점수 계산 (다른 감정이 약할 때)
        max_other_emotion = max(emotion_scores.values()) if emotion_scores else 0
        emotion_scores["neutral"] = max(0, 1.0 - max_other_emotion)
        
        # 정규화 (합이 1이 되도록)
        total = sum(emotion_scores.values())
        if total > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] = emotion_scores[emotion] / total
        
        # 예측된 감정
        predicted_emotion = max(emotion_scores.items(), key=lambda x: x[1])[0]
        
        return {
            "emotion_scores": emotion_scores,
            "predicted_emotion": predicted_emotion,
            "confidence": emotion_scores[predicted_emotion]
        }
    
    def get_emotion_label_kr(self, emotion: str) -> str:
        """
        감정 영어명을 한국어로 변환
        
        Args:
            emotion: 감정 영어명
        
        Returns:
            한국어 감정명
        """
        mapping = {
            "anger": "분노",
            "fear": "공포",
            "joy": "기쁨",
            "sadness": "슬픔",
            "surprise": "놀람",
            "disgust": "혐오",
            "trust": "신뢰",
            "anticipation": "기대",
            "neutral": "중립"
        }
        return mapping.get(emotion, emotion)

