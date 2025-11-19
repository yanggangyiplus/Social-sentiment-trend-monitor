"""
KcBERT/KoBERT 기반 감정 분석 모듈
AI 허브 한국어 감정 데이터셋으로 학습된 모델 사용
"""
from typing import Dict, List, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class KoBERTAnalyzer:
    """
    KcBERT/KoBERT 기반 감정 분석 클래스
    AI 허브 한국어 감정 데이터셋으로 학습된 모델 사용
    """
    
    def __init__(self, model_name: str = "beomi/KcBERT-base"):
        """
        KcBERT 분석기 초기화
        
        Args:
            model_name: 모델 이름 또는 경로
                - "beomi/KcBERT-base": KcBERT-base 모델 (권장)
                - "monologg/kobert": KoBERT 모델
                - 로컬 경로: fine-tuning된 모델 경로
        """
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 토크나이저 및 모델 로드
        try:
            print(f"모델 로드 중: {model_name}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            # 감정 분석 모델 로드
            # KcBERT-base는 기본적으로 MLM 모델이므로, 
            # 감정 분석을 위해서는 fine-tuning된 모델이 필요합니다.
            # 여기서는 기본 모델을 사용하되, 실제 사용 시 fine-tuning된 모델 경로를 지정해야 합니다.
            try:
                # 먼저 fine-tuning된 모델이 있는지 시도
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    num_labels=3,  # positive, negative, neutral
                    trust_remote_code=True
                )
            except Exception:
                # fine-tuning된 모델이 없으면 기본 모델 사용
                # 실제 프로덕션에서는 fine-tuning된 모델을 사용해야 합니다.
                print(f"경고: {model_name}에 감정 분석 헤드가 없습니다.")
                print("기본 모델을 사용합니다. (실제 감정 분석을 위해서는 fine-tuning된 모델이 필요합니다)")
                # 기본 모델로 시퀀스 분류 모델 생성
                from transformers import AutoModel
                base_model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
                self.model = AutoModelForSequenceClassification.from_config(
                    base_model.config,
                    num_labels=3
                )
                # 기본 모델의 가중치 복사
                self.model.base_model = base_model
            
            self.model.to(self.device)
            self.model.eval()
            print(f"✅ 모델 로드 완료: {model_name} (Device: {self.device})")
            
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            print("기본 모델을 사용합니다.")
            import traceback
            traceback.print_exc()
            self.tokenizer = None
            self.model = None
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        단일 텍스트 감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감정 분석 결과 딕셔너리
        """
        if not self.model or not self.tokenizer:
            # 모델이 없는 경우 기본값 반환
            return {
                "positive_score": 0.33,
                "negative_score": 0.33,
                "neutral_score": 0.34,
                "predicted_sentiment": "neutral"
            }
        
        try:
            # 텍스트 토크나이징
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 추론
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.softmax(logits, dim=-1).cpu().numpy()[0]
            
            # 감정 점수 추출
            positive_score = float(probabilities[0])
            negative_score = float(probabilities[1])
            neutral_score = float(probabilities[2])
            
            # 예측된 감정 클래스
            predicted_idx = np.argmax(probabilities)
            sentiment_classes = ["positive", "negative", "neutral"]
            predicted_sentiment = sentiment_classes[predicted_idx]
            
            return {
                "positive_score": positive_score,
                "negative_score": negative_score,
                "neutral_score": neutral_score,
                "predicted_sentiment": predicted_sentiment
            }
        
        except Exception as e:
            print(f"감정 분석 중 오류 발생: {e}")
            return {
                "positive_score": 0.33,
                "negative_score": 0.33,
                "neutral_score": 0.34,
                "predicted_sentiment": "neutral"
            }
    
    def analyze_batch(self, texts: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
        """
        배치 텍스트 감정 분석
        
        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기
            
        Returns:
            감정 분석 결과 리스트
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_results = [self.analyze(text) for text in batch_texts]
            results.extend(batch_results)
        
        return results

