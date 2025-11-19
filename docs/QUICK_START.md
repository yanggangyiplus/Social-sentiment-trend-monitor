# Quick Start 가이드

## 전체 파이프라인 실행 순서

### 1단계: 데이터 수집
```bash
source venv/bin/activate
python scripts/run_collector.py --keyword "아이폰" --max-results 10
```

### 2단계: 데이터 품질 검증
```bash
python scripts/check_data_quality.py --keyword "아이폰" --hours 24
```

### 3단계: 감정 분석
```bash
python scripts/run_sentiment_analysis.py --keyword "아이폰" --hours 24
```

### 4단계: 트렌드 탐지
```bash
python scripts/run_trend_detection.py --keyword "아이폰" --hours 24
```

### 5단계: 대시보드 확인
```bash
streamlit run app/web_demo.py --server.port 8501
```

## 감정 분석 모델 선택

### 옵션 1: KcBERT-base (기본, Fine-tuning 필요)
```yaml
# configs/config_sentiment.yaml
model:
  type: "kcbert"
  model_name: "beomi/KcBERT-base"
```

### 옵션 2: 규칙 기반 분석기 (빠르고 안정적)
```yaml
# configs/config_sentiment.yaml
model:
  type: "rule_based"
```

### 옵션 3: LLM (정확도 최고, 유료)
```yaml
# configs/config_sentiment.yaml
model:
  type: "llm"
  llm:
    provider: "openai"
    model_name: "gpt-3.5-turbo"
    api_key: "YOUR_API_KEY"
```

## Fine-tuning된 모델 사용

AI 허브 한국어 감정 데이터셋으로 학습한 모델을 사용하려면:

```yaml
# configs/config_sentiment.yaml
model:
  type: "kcbert"
  model_name: "beomi/KcBERT-base"
  fine_tuned_model_path: "./models/fine_tuned_sentiment"  # 로컬 경로
  # 또는
  fine_tuned_model_path: "alsgyu/sentiment-analysis-fine-tuned-model"  # HuggingFace 모델명
```

## 문제 해결

### 모델 로드 실패
- 자동으로 규칙 기반 분석기로 fallback됩니다
- Fine-tuning된 모델 경로를 확인하세요

### 데이터가 없음
- 데이터 수집을 먼저 실행하세요
- 키워드가 올바른지 확인하세요

### 감정 분석 결과가 모두 중립
- Fine-tuning된 모델이 필요합니다
- 또는 규칙 기반 분석기 사용 (`type: "rule_based"`)

