# 고급 트렌드 분석 알고리즘 가이드

## 개요

이 프로젝트는 시계열 기반 이상 탐지 솔루션으로, 여러 고급 변화점 탐지 알고리즘을 지원합니다.

## 지원 알고리즘

### 1. SimpleChangeDetector (기본)
- **설명**: 간단한 변화율 기반 탐지
- **장점**: 빠른 처리 속도, 직관적인 결과
- **단점**: 노이즈에 민감할 수 있음
- **사용 시나리오**: 빠른 프로토타이핑, 간단한 모니터링

### 2. CUSUM (Cumulative Sum)
- **설명**: 누적 합을 사용하여 평균의 변화를 감지
- **장점**: 점진적 변화 감지에 우수, 통계적으로 검증된 방법
- **단점**: 파라미터 튜닝 필요
- **사용 시나리오**: 서서히 변화하는 트렌드 감지, 제조업 품질 관리

### 3. Z-score
- **설명**: 통계적 이상치 탐지를 통한 변화점 감지
- **장점**: 표준편차 기반으로 정규화된 탐지, 이상치 탐지에 특화
- **단점**: 정규 분포 가정 필요
- **사용 시나리오**: 급격한 변화 감지, 이상치 탐지

### 4. Bayesian Change Point Detection
- **설명**: 베이지안 방법론을 사용한 변화점 탐지
- **장점**: 불확실성 정량화, 사전 지식 활용 가능
- **단점**: 계산 비용이 높을 수 있음
- **사용 시나리오**: 정확도가 중요한 경우, 불확실성 정량화 필요 시

## 설정 방법

### 설정 파일 (`configs/config_trend.yaml`)

```yaml
change_detection:
  method: "simple"  # simple, cusum, zscore, bayesian
  
  # CUSUM 설정
  cusum_threshold: 5.0
  drift: 0.5
  
  # Z-score 설정
  z_threshold: 2.5
  window_size: 10
  
  # Bayesian 설정
  prior_probability: 0.01
  min_segment_length: 5
```

### UI에서 선택

Streamlit 대시보드의 사이드바에서 알고리즘을 선택할 수 있습니다:
- 📊 간단한 방법 (기본)
- 📈 CUSUM (누적 합)
- 📉 Z-score (통계적 이상치)
- 🧠 Bayesian (베이지안)

## 알고리즘 비교

| 알고리즘 | 속도 | 정확도 | 노이즈 저항력 | 파라미터 튜닝 |
|---------|------|--------|--------------|--------------|
| Simple | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | 쉬움 |
| CUSUM | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 보통 |
| Z-score | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 쉬움 |
| Bayesian | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 어려움 |

## 사용 예시

### Python 코드에서 사용

```python
from app.services import trend_service

# CUSUM 알고리즘 사용
result = trend_service.analyze_trend_with_change_points(
    sentiment_list,
    method="cusum"
)

# Z-score 알고리즘 사용
result = trend_service.analyze_trend_with_change_points(
    sentiment_list,
    method="zscore"
)
```

### API에서 사용

```bash
# 설정 파일의 기본 알고리즘 사용
GET /api/trend/changes?keyword=아이폰&hours=24

# 특정 알고리즘 지정 (향후 확장)
GET /api/trend/changes?keyword=아이폰&hours=24&method=cusum
```

## 성능 고려사항

- **데이터 크기**: Bayesian은 대용량 데이터에서 느릴 수 있음
- **실시간성**: Simple, CUSUM, Z-score는 실시간 처리에 적합
- **정확도**: Bayesian이 가장 정확하지만 계산 비용이 높음

## 향후 확장

- Ruptures 라이브러리 통합 (PELT, Binseg, Dynp)
- ADTK (Anomaly Detection Toolkit) 통합
- Kats (Facebook의 시계열 분석 라이브러리) 통합

