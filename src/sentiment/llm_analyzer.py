"""
LLM 기반 감정 분석 모듈
"""
from typing import Dict, List, Any
import openai
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class LLMAnalyzer:
    """
    LLM 기반 감정 분석 클래스
    """
    
    def __init__(self, provider: str = "openai", model_name: str = "gpt-3.5-turbo", 
                 api_key: str = "", temperature: float = 0.3):
        """
        LLM 분석기 초기화
        
        Args:
            provider: LLM 제공자 ("openai" or "anthropic")
            model_name: 모델 이름
            api_key: API 키
            temperature: 생성 온도
        """
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        
        if provider == "openai":
            if api_key:
                openai.api_key = api_key
            self.client = openai
        else:
            raise ValueError(f"지원하지 않는 제공자: {provider}")
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        단일 텍스트 감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감정 분석 결과 딕셔너리
        """
        prompt = f"""다음 텍스트의 감정을 분석하여 긍정(positive), 부정(negative), 중립(neutral) 중 하나로 분류하고, 각 감정의 점수를 0.0~1.0 사이의 실수로 제공해주세요. 점수의 합은 1.0이어야 합니다.

텍스트: {text}

응답 형식:
positive_score: [0.0~1.0]
negative_score: [0.0~1.0]
neutral_score: [0.0~1.0]
predicted_sentiment: [positive/negative/neutral]
"""
        
        try:
            if self.provider == "openai":
                response = self.client.ChatCompletion.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "당신은 감정 분석 전문가입니다."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature
                )
                
                content = response.choices[0].message.content
                
                # 응답 파싱 (간단한 구현)
                result = self._parse_response(content)
                return result
        
        except Exception as e:
            print(f"LLM 감정 분석 중 오류 발생: {e}")
            return {
                "positive_score": 0.33,
                "negative_score": 0.33,
                "neutral_score": 0.34,
                "predicted_sentiment": "neutral"
            }
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        """
        LLM 응답 파싱
        
        Args:
            content: LLM 응답 텍스트
            
        Returns:
            파싱된 감정 분석 결과
        """
        # 간단한 파싱 구현 (실제로는 더 정교한 파싱 필요)
        positive_score = 0.33
        negative_score = 0.33
        neutral_score = 0.34
        predicted_sentiment = "neutral"
        
        # 키워드 기반 간단한 파싱
        lines = content.lower().split('\n')
        for line in lines:
            if 'positive_score' in line:
                try:
                    positive_score = float(line.split(':')[1].strip())
                except:
                    pass
            elif 'negative_score' in line:
                try:
                    negative_score = float(line.split(':')[1].strip())
                except:
                    pass
            elif 'neutral_score' in line:
                try:
                    neutral_score = float(line.split(':')[1].strip())
                except:
                    pass
            elif 'predicted_sentiment' in line:
                sentiment = line.split(':')[1].strip()
                if 'positive' in sentiment:
                    predicted_sentiment = "positive"
                elif 'negative' in sentiment:
                    predicted_sentiment = "negative"
                else:
                    predicted_sentiment = "neutral"
        
        return {
            "positive_score": positive_score,
            "negative_score": negative_score,
            "neutral_score": neutral_score,
            "predicted_sentiment": predicted_sentiment
        }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        배치 텍스트 감정 분석
        
        Args:
            texts: 텍스트 리스트
            
        Returns:
            감정 분석 결과 리스트
        """
        return [self.analyze(text) for text in texts]

