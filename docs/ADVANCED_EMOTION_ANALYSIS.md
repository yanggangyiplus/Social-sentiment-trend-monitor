# 고급 감정 분석 기능

이 문서는 Social Sentiment & Trend Monitor의 고급 감정 분석 기능에 대해 설명합니다.

## 개요

기본적인 긍정/부정/중립 분류 외에도, 다음과 같은 고급 감정 분석 기능을 제공합니다:

1. **9가지 감정 분류**: Ekman의 기본 감정과 Plutchik의 감정 휠을 기반으로 한 세밀한 감정 분류
2. **토픽-감정 동시 분석**: BERTopic을 사용한 토픽 모델링 및 토픽별 감정 분석

---

## 9가지 감정 분류

### 지원 감정

다음 9가지 감정을 분류합니다:

| 감정 (영어) | 감정 (한국어) | 설명 |
|------------|-------------|------|
| anger | 분노 | 화나고 짜증나는 감정 |
| fear | 공포 | 무서워하고 두려워하는 감정 |
| joy | 기쁨 | 행복하고 즐거운 감정 |
| sadness | 슬픔 | 슬프고 우울한 감정 |
| surprise | 놀람 | 놀라고 신기해하는 감정 |
| disgust | 혐오 | 역겨워하고 싫어하는 감정 |
| trust | 신뢰 | 믿고 확신하는 감정 |
| anticipation | 기대 | 기대하고 설레는 감정 |
| neutral | 중립 | 특정 감정이 없는 상태 |

### 구현 방식

`src/sentiment/emotion_classifier.py`의 `EmotionClassifier` 클래스가 키워드 매칭 기반으로 감정을 분류합니다.

각 감정별로 한국어 키워드 리스트를 정의하고, 텍스트에서 해당 키워드가 나타나는 빈도를 기반으로 감정 점수를 계산합니다.

### 사용 방법

#### 설정 파일에서 활성화

`configs/config_sentiment.yaml` 파일에서 활성화:

```yaml
advanced:
  enable_emotion_classification: true
```

#### 코드에서 직접 사용

```python
from src.sentiment.emotion_classifier import EmotionClassifier

classifier = EmotionClassifier()
result = classifier.classify_emotion("정말 좋아요! 기쁩니다!")

print(result["predicted_emotion"])  # "joy"
print(result["emotion_scores"])     # {"joy": 0.8, "neutral": 0.2, ...}
print(result["confidence"])         # 0.8
```

#### UI에서 확인

Streamlit 대시보드에서 각 비디오의 댓글 섹션에 "9가지 감정 분류" 차트가 표시됩니다.

---

## 토픽-감정 동시 분석

### 개요

BERTopic을 사용하여 댓글을 토픽으로 그룹화하고, 각 토픽별로 평균 감정 점수를 계산합니다.

### 구현 방식

`src/sentiment/topic_sentiment_analyzer.py`의 `TopicSentimentAnalyzer` 클래스가 토픽 모델링과 감정 분석을 통합합니다.

#### BERTopic 사용 (권장)

BERTopic이 설치되어 있으면 자동으로 사용됩니다:

```bash
pip install bertopic sentence-transformers umap-learn hdbscan
```

BERTopic은 다음 단계로 작동합니다:
1. Sentence Transformers로 텍스트 임베딩 생성
2. UMAP으로 차원 축소
3. HDBSCAN으로 클러스터링
4. 각 클러스터의 대표 키워드 추출

#### 키워드 기반 분석 (Fallback)

BERTopic이 설치되지 않았거나 초기화에 실패하면, 키워드 빈도 기반의 간단한 토픽 분석을 사용합니다.

### 사용 방법

#### 설정 파일에서 활성화

`configs/config_sentiment.yaml` 파일에서 활성화:

```yaml
advanced:
  enable_topic_sentiment: true
  use_bertopic: true  # false면 키워드 기반 사용
```

#### 코드에서 직접 사용

```python
from src.sentiment.topic_sentiment_analyzer import TopicSentimentAnalyzer

analyzer = TopicSentimentAnalyzer(use_bertopic=True)

texts = ["아이폰 배터리가 좋아요", "아이폰 카메라가 최고예요", "아이폰이 너무 비싸요"]
sentiments = [
    {"positive_score": 0.8, "negative_score": 0.1, "neutral_score": 0.1},
    {"positive_score": 0.9, "negative_score": 0.05, "neutral_score": 0.05},
    {"positive_score": 0.1, "negative_score": 0.8, "neutral_score": 0.1}
]

result = analyzer.analyze_topics_and_sentiment(texts, sentiments)

print(result["topics"])  # 토픽 리스트
print(result["method"])  # "bertopic" or "keyword_based"
```

#### UI에서 확인

Streamlit 대시보드에서 각 비디오의 댓글 섹션에 "토픽별 감정 분석" 차트가 표시됩니다.

---

## 서비스 레이어 통합

`app/services/emotion_service.py`의 `EmotionService` 클래스가 고급 감정 분석 기능을 통합합니다.

### 주요 메서드

- `analyze_emotions_batch(texts)`: 배치 텍스트에 대한 9가지 감정 분류
- `get_emotion_statistics(emotion_results)`: 감정 분류 결과 통계 계산
- `analyze_topics_with_sentiment(texts, sentiments, use_bertopic)`: 토픽-감정 동시 분석
- `get_emotion_label_kr(emotion)`: 감정 영어명을 한국어로 변환

---

## 시각화

### 9가지 감정 분포 차트

`app/utils/visualization.py`의 `create_emotion_distribution_chart()` 함수가 감정별 개수와 비율을 Bar Chart로 표시합니다.

### 토픽별 감정 분석 차트

`app/utils/visualization.py`의 `create_topic_sentiment_chart()` 함수가 토픽별 평균 감정 점수를 Stacked Bar Chart로 표시합니다.

---

## 성능 고려사항

### BERTopic 초기화 시간

BERTopic 모델을 처음 초기화할 때는 시간이 걸릴 수 있습니다 (약 10-30초). 이후에는 재사용되므로 빠릅니다.

### 메모리 사용량

BERTopic은 텍스트 임베딩을 메모리에 저장하므로, 대량의 텍스트를 분석할 때는 메모리 사용량이 증가할 수 있습니다.

### 권장 사항

- 실시간 분석: 키워드 기반 분석 사용 (`use_bertopic: false`)
- 배치 분석: BERTopic 사용 (`use_bertopic: true`)
- 대량 데이터: 텍스트를 청크로 나누어 처리

---

## 참고 자료

- [BERTopic 공식 문서](https://maartengr.github.io/BERTopic/)
- [Ekman의 기본 감정](https://en.wikipedia.org/wiki/Emotion_classification)
- [Plutchik의 감정 휠](https://en.wikipedia.org/wiki/Plutchik%27s_wheel_of_emotions)

