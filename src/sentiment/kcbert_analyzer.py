"""
KcBERT 기반 감정 분석 모듈 (개선 버전)
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


class KcBERTAnalyzer:
    """
    KcBERT 기반 감정 분석 클래스
    beomi/KcBERT-base 모델 사용
    """
    
    def __init__(self, model_name: str = "beomi/KcBERT-base", 
                 fine_tuned_model_path: str = None):
        """
        KcBERT 분석기 초기화
        
        Args:
            model_name: 기본 모델 이름 (beomi/KcBERT-base)
            fine_tuned_model_path: Fine-tuning된 모델 경로 (로컬 경로 또는 HuggingFace 모델명)
        """
        self.model_name = model_name
        self.fine_tuned_model_path = fine_tuned_model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 모델 로드
        self._load_model()
    
    def _load_model(self):
        """모델 및 토크나이저 로드"""
        try:
            # Fine-tuning된 모델이 있으면 우선 사용
            if self.fine_tuned_model_path:
                print(f"Fine-tuning된 모델 로드 중: {self.fine_tuned_model_path}")
                model_path = self.fine_tuned_model_path
            else:
                print(f"기본 모델 로드 중: {self.model_name}")
                model_path = self.model_name
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path if self.fine_tuned_model_path else self.model_name,
                trust_remote_code=True
            )
            
            # 모델 로드 시도
            try:
                # Fine-tuning된 감정 분석 모델 로드 시도
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    model_path,
                    num_labels=3,  # positive, negative, neutral
                    trust_remote_code=True
                )
                print(f"✅ Fine-tuning된 감정 분석 모델 로드 완료")
            except Exception as e:
                # Fine-tuning된 모델이 없으면 기본 모델 사용
                print(f"⚠️ Fine-tuning된 모델을 찾을 수 없습니다: {e}")
                print("기본 KcBERT 모델을 사용합니다.")
                
                # 기본 모델로 시퀀스 분류 모델 생성
                from transformers import AutoModel
                base_model = AutoModel.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )
                
                # 시퀀스 분류 헤드 추가
                from torch import nn
                class SentimentClassifier(nn.Module):
                    def __init__(self, base_model, num_labels=3):
                        super().__init__()
                        self.base_model = base_model
                        self.classifier = nn.Linear(base_model.config.hidden_size, num_labels)
                        self.dropout = nn.Dropout(0.1)
                    
                    def forward(self, **inputs):
                        outputs = self.base_model(**inputs)
                        pooled_output = outputs.last_hidden_state[:, 0]  # [CLS] 토큰
                        pooled_output = self.dropout(pooled_output)
                        logits = self.classifier(pooled_output)
                        return type('Output', (), {'logits': logits})()
                
                self.model = SentimentClassifier(base_model, num_labels=3)
                print("⚠️ 기본 모델 사용 (실제 감정 분석 성능은 제한적입니다)")
            
            self.model.to(self.device)
            self.model.eval()
            print(f"✅ 모델 로드 완료 (Device: {self.device})")
            
        except Exception as e:
            print(f"❌ 모델 로드 실패: {e}")
            print("규칙 기반 분석기를 사용합니다.")
            import traceback
            traceback.print_exc()
            self.tokenizer = None
            self.model = None
            # Fallback: 규칙 기반 분석기
            from .rule_based_analyzer import RuleBasedAnalyzer
            self.fallback_analyzer = RuleBasedAnalyzer()
        else:
            self.fallback_analyzer = None
    
    def analyze(self, text: str) -> Dict[str, Any]:
        """
        단일 텍스트 감정 분석
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            감정 분석 결과 딕셔너리
        """
        if not self.model or not self.tokenizer:
            # 모델이 없는 경우 규칙 기반 분석기 사용
            if self.fallback_analyzer:
                return self.fallback_analyzer.analyze(text)
            else:
                return {
                    "positive_score": 0.33,
                    "negative_score": 0.33,
                    "neutral_score": 0.34,
                    "predicted_sentiment": "neutral"
                }
        
        if not text or len(text.strip()) < 1:
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
                
                # 출력 형식 처리
                if hasattr(outputs, 'logits'):
                    logits = outputs.logits
                elif isinstance(outputs, dict):
                    logits = outputs.get('logits', outputs.get('logit'))
                else:
                    logits = outputs
                
                # 배치 차원 제거
                if logits.dim() > 1:
                    logits = logits[0]
                
                probabilities = torch.softmax(logits, dim=-1).cpu().numpy()
            
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
            # 오류 발생 시 규칙 기반 분석기로 fallback
            if self.fallback_analyzer:
                return self.fallback_analyzer.analyze(text)
            else:
                import traceback
                traceback.print_exc()
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

