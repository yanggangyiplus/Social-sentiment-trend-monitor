# 감정 분석 모델 설정 가이드

## 모델 선택

본 프로젝트는 AI 허브 한국어 감정 데이터셋을 기반으로 학습된 모델을 사용합니다.

### 1. KcBERT-base (권장)

**모델**: `beomi/KcBERT-base`

**특징**:
- 한국어 특화 BERT 모델
- AI 허브 한국어 감정 데이터셋으로 fine-tuning 가능
- 무료, 안정적, 신뢰 가능

**사용 방법**:
```yaml
# configs/config_sentiment.yaml
model:
  type: "kcbert"
  model_name: "beomi/KcBERT-base"
```

### 2. Fine-tuning된 모델 사용

AI 허브 한국어 감정 데이터셋으로 fine-tuning한 모델을 사용하려면:

#### 방법 1: HuggingFace 모델 사용
```yaml
model:
  type: "kcbert"
  model_name: "beomi/KcBERT-base"
  fine_tuned_model_path: "alsgyu/sentiment-analysis-fine-tuned-model"  # HuggingFace 모델명
```

#### 방법 2: 로컬 모델 사용
```yaml
model:
  type: "kcbert"
  model_name: "beomi/KcBERT-base"
  fine_tuned_model_path: "./models/fine_tuned_sentiment"  # 로컬 경로
```

### 3. 모델 Fine-tuning (선택사항)

자체 데이터셋으로 fine-tuning하려면:

1. **데이터셋 준비**
   - AI 허브 한국어 감정 데이터셋 다운로드
   - 형식: JSON (text, label)

2. **Fine-tuning 스크립트 실행**
   ```python
   from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
   from datasets import Dataset
   
   # 모델 및 토크나이저 로드
   tokenizer = AutoTokenizer.from_pretrained("beomi/KcBERT-base")
   model = AutoModelForSequenceClassification.from_pretrained(
       "beomi/KcBERT-base",
       num_labels=3  # positive, negative, neutral
   )
   
   # 데이터셋 준비 및 학습
   # ... (상세 코드는 참고 링크 참조)
   ```

3. **모델 저장**
   ```python
   model.save_pretrained("./models/fine_tuned_sentiment")
   tokenizer.save_pretrained("./models/fine_tuned_sentiment")
   ```

## 참고 자료

- [KcBERT-base 모델](https://huggingface.co/beomi/KcBERT-base)
- [Fine-tuning 예제](https://github.com/alsgyu/finetunning_huggingface/blob/main/Untitled2.ipynb)
- [AI 허브 한국어 감정 데이터셋](https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=271)

## 성능 비교

| 모델 | 정확도 | 속도 | 비용 |
|------|--------|------|------|
| KcBERT-base (기본) | 중간 | 빠름 | 무료 |
| KcBERT-base (Fine-tuned) | 높음 | 빠름 | 무료 |
| OpenAI GPT-3.5 | 매우 높음 | 중간 | 유료 |
| OpenAI GPT-4 | 최고 | 느림 | 매우 유료 |

## 권장 설정

### 비용 절약 모드
```yaml
model:
  type: "kcbert"
  model_name: "beomi/KcBERT-base"
```

### 정확도 모드
```yaml
model:
  type: "llm"
  llm:
    provider: "openai"
    model_name: "gpt-3.5-turbo"
    api_key: "YOUR_API_KEY"
```

