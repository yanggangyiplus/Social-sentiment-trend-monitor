"""
규칙 기반 감정 분석 모듈
한국어 키워드 매칭을 통한 감정 분석 (기본 사용)

특징:
- Fine-tuning 불필요, 즉시 사용 가능
- 한국어 긍정/부정 키워드 기반 분류
- 키워드 빈도에 따른 점수 계산
- 웃음 표현(ㅋ, ㅎ), 예쁨/귀여움 표현, 불편/피해 표현 등 다양한 키워드 지원

사용 방법:
- config_sentiment.yaml에서 model.type을 "rule_based"로 설정
- KcBERT Fine-tuning 모델이 없을 때 자동 fallback으로도 사용됨
"""
from typing import Dict, Any
import re


class RuleBasedAnalyzer:
    """
    규칙 기반 감정 분석 클래스
    키워드 매칭을 통한 간단한 감정 분석
    """
    
    # 긍정 키워드
    POSITIVE_KEYWORDS = [
        # 기본 긍정 표현
        "좋", "최고", "만족", "추천", "훌륭", "완벽", "대박",
        "좋아", "좋네", "좋아요", "좋습니다", "좋아하는", "좋아할",
        "사랑", "최고의", "최고다", "최고네", "최고예요", "최고입니다",
        "만족", "만족스러", "만족해", "만족합니다", "만족했어",
        "추천", "추천해", "추천합니다", "추천드려", "추천할",
        "훌륭", "훌륭해", "훌륭합니다", "훌륭하네",
        "완벽", "완벽해", "완벽합니다", "완벽하네",
        "대박", "대박이야", "대박이다", "대박이네",
        "감사", "감사해", "감사합니다", "고마워",
        "행복", "행복해", "행복합니다", "행복하네",
        # 예쁨/귀여움 관련
        "예쁘", "예쁘다", "예쁘네", "예쁘네요", "예쁩니다", "예뻐", "예뻐요",
        "귀엽", "귀여", "귀여워", "귀여워요", "귀여웠", "귀여웠어", "귀여웠네",
        "귀", "귀요미", "귀여운", "귀여움",
        "멋있", "멋져", "멋져요", "멋있어", "멋있네", "멋있어요",
        "이쁘", "이쁘다", "이쁘네", "이쁘네요", "이쁩니다", "이뻐", "이뻐요",
        "아름다", "아름다워", "아름다워요", "아름답", "아름답네",
        "사랑스러", "사랑스러워", "사랑스러워요",
        # 웃음 표현 (긍정적 의미)
        "ㅋ", "ㅎ", "하하", "헤헤", "히히", "웃", "웃겨", "웃겨요",
        "재밌", "재미있", "재미있어", "재미있어요", "재미있네", "재미있습니다",
        "재밌어", "재밌어요", "재밌네", "재밌습니다",
        "즐거", "즐거워", "즐거워요", "즐겁", "즐겁네",
        # 칭찬 표현
        "잘했", "잘했어", "잘했어요", "잘했다", "잘했네",
        "훌륭", "훌륭해", "훌륭해요", "훌륭하네",
        "멋지", "멋져", "멋져요", "멋지네",
        "훌륭", "훌륭해", "훌륭해요",
        # 긍정 감탄사
        "와", "우와", "오", "오오", "와우", "헐", "헉",
        "짱", "짱이야", "짱이다", "짱이네", "짱이에요"
    ]
    
    # 부정 키워드
    NEGATIVE_KEYWORDS = [
        # 기본 부정 표현
        "나쁘", "최악", "불만", "비추천", "별로", "안좋", "싫",
        "나쁘", "나빠", "나쁘네", "나빠요", "나쁩니다",
        "최악", "최악이야", "최악이다", "최악이네", "최악이에요",
        "불만", "불만이야", "불만이에요", "불만입니다",
        "비추천", "비추천해", "비추천합니다",
        "별로", "별로야", "별로예요", "별로네", "별로입니다",
        "안좋", "안좋아", "안좋네", "안좋아요", "안좋습니다",
        "싫", "싫어", "싫네", "싫어요", "싫습니다",
        # 불편/피해 관련
        "불편", "불편해", "불편해요", "불편함", "불편하", "불편하다", "불편하네", "불편합니다",
        "피해", "피해를", "피해가", "피해를봤", "피해를봤어", "피해를봤어요", "피해를봤습니다",
        "손해", "손해를", "손해가", "손해봤", "손해봤어", "손해봤어요",
        # 안됨/안돼 관련
        "안돼", "안된다", "안돼요", "안됩니다", "안돼네",
        "안되", "안되어", "안되어요", "안됩니다",
        "안됨", "안됐", "안됐어", "안됐어요", "안됐습니다",
        # 짠함/서러움 관련
        "짠", "짠하", "짠하다", "짠해", "짠해요", "짠합니다", "짠하네",
        "서러", "서러워", "서러워요", "서럽", "서럽네",
        "안타까", "안타까워", "안타까워요", "안타깝", "안타깝네",
        "아쉽", "아쉬워", "아쉬워요", "아쉽네", "아쉽습니다",
        # 쓰레기/망 관련
        "쓰레기", "쓰래기", "쓰레기야", "쓰레기다", "쓰레기네",
        "망", "망했", "망했어", "망했다", "망했네",
        "실망", "실망했", "실망했어", "실망했다", "실망했네",
        # 화/짜증 관련
        "화나", "화났", "화났어", "화났다", "화났네",
        "짜증", "짜증나", "짜증나네", "짜증나요",
        # 기타 부정 표현
        "힘들", "힘들어", "힘들어요", "힘듦", "힘듭니다",
        "어렵", "어려워", "어려워요", "어렵네", "어렵습니다",
        "복잡", "복잡해", "복잡해요", "복잡하", "복잡합니다",
        "답답", "답답해", "답답해요", "답답하", "답답합니다",
        "지겨", "지겨워", "지겨워요", "지겹", "지겹네",
        "지루", "지루해", "지루해요", "지루하", "지루합니다",
        "슬프", "슬퍼", "슬퍼요", "슬프네", "슬픕니다",
        "우울", "우울해", "우울해요", "우울하", "우울합니다",
        "걱정", "걱정돼", "걱정돼요", "걱정되", "걱정됩니다",
        "불안", "불안해", "불안해요", "불안하", "불안합니다"
    ]
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        규칙 기반 감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감정 분석 결과 딕셔너리
        """
        if not text:
            return {
                "positive_score": 0.33,
                "negative_score": 0.33,
                "neutral_score": 0.34,
                "predicted_sentiment": "neutral"
            }
        
        text_lower = text.lower()
        
        # 키워드 매칭
        positive_count = sum(1 for keyword in self.POSITIVE_KEYWORDS if keyword in text_lower)
        negative_count = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in text_lower)
        
        # 점수 계산
        total_keywords = positive_count + negative_count
        
        if total_keywords == 0:
            # 키워드가 없으면 중립
            return {
                "positive_score": 0.33,
                "negative_score": 0.33,
                "neutral_score": 0.34,
                "predicted_sentiment": "neutral"
            }
        
        # 키워드 비율 기반 점수 계산
        positive_ratio = positive_count / total_keywords if total_keywords > 0 else 0.0
        negative_ratio = negative_count / total_keywords if total_keywords > 0 else 0.0
        
        # 점수 계산 (0.0 ~ 1.0)
        # 키워드가 많을수록 해당 감정 점수 증가
        if positive_count > 0 and negative_count == 0:
            # 긍정 키워드만 있는 경우
            positive_score = 0.7 + (positive_count / max(positive_count, 3)) * 0.3
            negative_score = 0.1
            neutral_score = 1.0 - positive_score - negative_score
        elif negative_count > 0 and positive_count == 0:
            # 부정 키워드만 있는 경우
            negative_score = 0.7 + (negative_count / max(negative_count, 3)) * 0.3
            positive_score = 0.1
            neutral_score = 1.0 - positive_score - negative_score
        else:
            # 혼합된 경우
            positive_score = 0.2 + positive_ratio * 0.6
            negative_score = 0.2 + negative_ratio * 0.6
            neutral_score = 1.0 - positive_score - negative_score
        
        # 정규화 (합이 1.0이 되도록, 음수 방지)
        total = max(0.1, positive_score + negative_score + neutral_score)
        positive_score = max(0.0, positive_score / total)
        negative_score = max(0.0, negative_score / total)
        neutral_score = max(0.0, neutral_score / total)
        
        # 최종 정규화
        total = positive_score + negative_score + neutral_score
        if total > 0:
            positive_score /= total
            negative_score /= total
            neutral_score /= total
        else:
            positive_score = 0.33
            negative_score = 0.33
            neutral_score = 0.34
        
        # 예측된 감정 클래스
        if positive_score > negative_score and positive_score > neutral_score:
            predicted_sentiment = "positive"
        elif negative_score > positive_score and negative_score > neutral_score:
            predicted_sentiment = "negative"
        else:
            predicted_sentiment = "neutral"
        
        return {
            "positive_score": positive_score,
            "negative_score": negative_score,
            "neutral_score": neutral_score,
            "predicted_sentiment": predicted_sentiment
        }

