# Social Sentiment & Trend Monitor

실시간 감정 분석 & 트렌드 변화 탐지 서비스

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 프로젝트 미리보기

*Streamlit 대시보드 화면 - 실시간 감정 트렌드 모니터링 및 변화점 탐지*

## 핵심 성과 요약

| 항목 | 성과 |
|:---:|:---:|
| **데이터 수집** | YouTube API 연동 완료 (Search + CommentThreads + Videos API) |
| **감정 분석** | Rule-based 기본 적용 (한국어 키워드 100+), KoBERT/KcBERT 옵션 모듈 |
| **변화점 탐지** | 4가지 알고리즘 지원 (Simple, CUSUM, Z-score, Bayesian) |
| **대시보드** | Streamlit 기반 실시간 모니터링 UI |
| **구현 범위** | 수집부터 시각화까지 End-to-End 구현 |

## 문제 정의 & 해결 목적

온라인 텍스트 기반의 감정 흐름을 실시간으로 모니터링하고, 트렌드 변화를 자동으로 감지하는 시스템이 필요했습니다. SNS, 뉴스, 블로그 등 다양한 소스에서 수집한 텍스트 데이터를 분석하여 여론 변화를 조기 감지합니다.

기존 도구들은 주로 단순 감정 분석에 그치며, 시계열 트렌드 분석과 변화점 탐지 기능이 부족했습니다. 이 프로젝트는 실시간 데이터 수집부터 감정 분석, 트렌드 분석, 변화점 탐지까지 End-to-End 파이프라인을 제공합니다.

## 프로젝트 개요

### 목적
YouTube, X(트위터), 뉴스, 블로그에서 특정 키워드와 관련된 텍스트 데이터를 실시간 또는 준실시간으로 수집하고, 감정 분석 + 시계열 트렌드 분석 + 변화(이상) 탐지를 통해 사람들의 반응 변화를 시각적으로 확인할 수 있는 서비스를 구축합니다.

### 주요 특징
- 다양한 소스 지원: YouTube, X(트위터), 뉴스, 블로그
- 실시간 감정 분석: Rule-based Analyzer 기본 적용 (즉시 사용 가능), KoBERT/KcBERT는 옵션 모듈 (Fine-tuning 필요)
- 트렌드 변화 탐지: Change Point Detection 알고리즘으로 급격한/점진적 변화 구간 탐지 (4가지 알고리즘 지원)
- 시각화 대시보드: Streamlit 기반 실시간 모니터링 UI
- RESTful API: FastAPI 기반 데이터 서비스

## 시스템 아키텍처

### 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (User)                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
        ┌──────────────────────────────────────┐
        │     Streamlit Dashboard              │
        │   실시간 감정 모니터링 UI              │
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         FastAPI Backend             │
        │      RESTful API 서버                │
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │     Data Collection Pipeline         │
        │  YouTube/X/뉴스/블로그 수집            │
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │      Text Preprocessing              │
        │   정제, 중복제거, 언어필터링           │
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │      Sentiment Analysis              │
        │  Rule-based 기본 / KoBERT/KcBERT 옵션│
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │    Trend Detection Engine            │
        │  시계열 분석, 변화점 탐지              │
        └──────────────────┬───────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         Database                    │
        │  SQLite/PostgreSQL                  │
        │  수집 데이터 및 분석 결과 저장        │
        └──────────────────────────────────────┘
```

### 데이터 파이프라인

```
Raw Data (YouTube/X/뉴스/블로그)
    │
    ▼
┌──────────────────────────┐
│   Data Collection       │
│  - API 호출              │
│  - 텍스트 추출            │
└───────────┬──────────────┘
            │
            ▼
┌─────────────────────────┐
│   Text Preprocessing    │
│  - 언어 필터링           │
│  - 정제 및 정규화         │
│  - 중복 제거             │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Sentiment Analysis    │
│  - Rule-based 기본      │
│  - KoBERT/KcBERT 옵션   │
│  - 감정 점수 산출         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Trend Detection       │
│  - 시계열 집계           │
│  - Change Point 탐지     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Database Storage      │
│  - 결과 저장             │
│  - 대시보드 제공          │
└─────────────────────────┘
```

## 모델/기술 스택

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Backend** | FastAPI | 고성능 API 서버, 자동 문서화(Swagger UI) 제공 |
| **Frontend** | Streamlit | 빠른 프로토타이핑 및 실시간 모니터링 UI 구축 |
| **NLP** | 규칙 기반 분석기, KcBERT-base, OpenAI API (옵션) | Rule-based는 즉시 사용 가능, KoBERT/KcBERT는 Fine-tuning 가능, LLM은 실시간 파이프라인에서 비활성화 (API latency 고려) |
| **토픽 모델링** | BERTopic, Sentence Transformers | 토픽-감정 동시 분석 기능 제공 |
| **Database** | SQLite (PostgreSQL 지원 가능) | 빠른 프로토타이핑에 적합, 프로덕션 환경에서는 PostgreSQL 확장 가능 |
| **데이터 처리** | Pandas, NumPy | 데이터 처리 및 통계 분석 |
| **시각화** | Plotly, WordCloud, Matplotlib | 인터랙티브 차트 및 시각화 제공 |
| **APIs** | YouTube Data API v3 | 실제 API 연동으로 실시간 데이터 수집 |
| **배포** | Docker (선택사항) | 일관된 배포 환경 제공 |

## 실험 결과

### 감정 분석 성능

| 분석기 | 특징 | 정확도 | 처리 속도 |
|--------|------|--------|----------|
| **Rule-based** | 한국어 키워드 매칭 (100+ 키워드) | 중간 | 매우 빠름 |
| **KoBERT/KcBERT** | Fine-tuning 필요 | 높음 | 중간 |
| **LLM** | OpenAI API 기반 | 매우 높음 | 느림 (API latency) |

### 변화점 탐지 알고리즘 비교

| 알고리즘 | 특성 | 사용 시기 | 처리 속도 |
|---------|------|----------|----------|
| **SimpleChangeDetector** | 기준선 대비 급격한 변화 감지 | 실시간 모니터링 (기본값) | 빠름 |
| **CUSUM** | 누적 변화가 일정 threshold 넘을 때 변화 감지 | 점진적 변화 감지 필요 시 | 중간 |
| **Z-score** | 분포 기반 이상치 탐지 | 급격한 변화 감지 필요 시 | 빠름 |
| **Bayesian** | 급격 + 점진 변화 둘 다 처리 가능하나 비용이 큼 | 정밀 분석 필요 시 | 느림 |

## 핵심 기술 설명

### Rule-based Analyzer 선택 이유

Rule-based Analyzer는 한국어 키워드 매칭 기반으로, Fine-tuning 불필요하고 즉시 사용 가능합니다. 빠르고 안정적이며, 정확도는 중간 수준입니다. 실시간 파이프라인에서 기본 분석기로 사용하기에 적합합니다.

### KoBERT/KcBERT 옵션 모듈 구성

KoBERT/KcBERT는 옵션 모듈 형태로 구성되어 있습니다. Fine-tuning된 모델이 필요하며, Fine-tuning 모델이 없으면 자동으로 Rule-based Analyzer로 Fallback합니다. 추후 Fine-tuning 기반으로 확장 가능한 구조입니다.

### LLM 비활성화 이유

LLM(OpenAI API)은 실시간 파이프라인에서 비활성화되어 있습니다. API latency 때문에 실시간 모니터링에는 부적합하며, 배치 분석이나 오프라인 분석 시에만 사용 권장합니다.

### 변화점 탐지 알고리즘 선택 기준

- **실시간 모니터링**: SimpleChangeDetector 또는 Z-score (빠른 처리)
- **점진적 변화 감지**: CUSUM (누적 변화 추적)
- **정밀 분석**: Bayesian (불확실성 정량화)

## 실행 방법

### Quick Start

```bash
# 저장소 클론
git clone https://github.com/yanggangyiplus/Social-sentiment-trend-monitor.git
cd Social-sentiment-trend-monitor

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# YouTube API 키 설정
# configs/config_collector.yaml 파일에 API 키 입력

# 대시보드 실행
streamlit run app/web_demo.py --server.port 8501
```

### 상세 설치 가이드

1. **저장소 클론**
```bash
git clone https://github.com/yanggangyiplus/Social-sentiment-trend-monitor.git
cd Social-sentiment-trend-monitor
```

2. **가상환경 생성 및 활성화**
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **YouTube API 키 설정** (필수)
   - [Google Cloud Console](https://console.cloud.google.com/)에서 YouTube Data API v3 키 발급
   - `configs/config_collector.yaml` 파일에 API 키 입력:
   ```yaml
   sources:
     youtube:
       enabled: true
       api_key: "YOUR_YOUTUBE_API_KEY"  # 여기에 입력
   ```
   - 상세 가이드: [docs/YOUTUBE_SETUP.md](docs/YOUTUBE_SETUP.md)

5. **기타 설정 파일 구성**
   - 설정 파일 예제를 복사하여 사용:
   ```bash
   cp configs/config_collector.example.yaml configs/config_collector.yaml
   cp configs/config_sentiment.example.yaml configs/config_sentiment.yaml
   cp configs/config_trend.example.yaml configs/config_trend.yaml
   cp configs/config_api.example.yaml configs/config_api.yaml
   ```
   - 각 설정 파일에서 필요한 값 입력 (API 키 등)

### 실행

#### 데이터 수집
```bash
python scripts/run_collector.py --keyword "아이폰"
```

#### 감정 분석
```bash
python scripts/run_sentiment_analysis.py --keyword "아이폰"
```

#### 트렌드 탐지
```bash
python scripts/run_trend_detection.py --keyword "아이폰"
```

#### Streamlit 대시보드
```bash
bash scripts/run_streamlit.sh
# 또는
streamlit run app/web_demo.py --server.port 8501
```

#### FastAPI 백엔드
```bash
bash scripts/run_api.sh
# 또는
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

### 데이터베이스 초기화

프로젝트를 처음 실행할 때 데이터베이스가 자동으로 생성됩니다. 수동으로 초기화하려면:

```bash
python3 -c "from src.database.db_manager import init_database; init_database('sqlite:///data/database/sentiment.db')"
```

또는 대시보드나 API를 실행하면 자동으로 데이터베이스가 생성됩니다.

## 사용 시나리오 (Use Cases)

### 1. 브랜드 여론 모니터링
**시나리오**: 특정 브랜드나 제품에 대한 온라인 여론을 실시간으로 모니터링하고 싶을 때  
**해결책**: 키워드 기반 데이터 수집, 감정 분석, 트렌드 변화 탐지  
**효과**: 브랜드 이미지 변화를 조기 감지하여 대응 전략 수립

### 2. 이슈 트렌드 분석
**시나리오**: 특정 이슈나 사건에 대한 여론 변화를 분석하고 싶을 때  
**해결책**: 시계열 트렌드 분석 및 변화점 탐지 알고리즘 활용  
**효과**: 급격한 여론 변화 구간을 자동으로 탐지하여 인사이트 도출

### 3. 경쟁사 분석
**시나리오**: 경쟁사 제품에 대한 온라인 반응을 분석하고 싶을 때  
**해결책**: 경쟁사 키워드 기반 데이터 수집 및 감정 분석  
**효과**: 경쟁사 제품의 강점과 약점 파악

### 4. 마케팅 캠페인 효과 측정
**시나리오**: 마케팅 캠페인 전후의 여론 변화를 측정하고 싶을 때  
**해결책**: 캠페인 기간 전후 데이터 수집 및 비교 분석  
**효과**: 캠페인 효과를 정량적으로 측정

## 한계 & 개선 방향

### 현재 한계

- **Twitter/X API**: Mock Data 사용 (v2에서 실제 구현 예정)
- **뉴스/블로그**: Mock Data 사용 (v1에서 실제 구현 예정)
- **Fine-tuning 모델**: KoBERT/KcBERT Fine-tuning 모델 미제공
- **토픽 분석**: 실시간 파이프라인에서 비활성화 (처리 비용 문제)
- **LLM 분석**: 실시간 파이프라인에서 비활성화 (API latency)

### 개선 방향

- **v1**: 뉴스/블로그 실제 API 연동, Fine-tuning된 KcBERT 모델 통합
- **v2**: Twitter/X 실제 API 연동, 비동기 데이터 수집 파이프라인
- **토픽 분석 최적화**: 실시간 파이프라인에서 토픽 분석 성능 최적화
- **LLM 분석 최적화**: 배치 처리 또는 캐싱을 통한 LLM 분석 성능 개선
- **다국어 지원**: 영어, 일본어 등 다국어 감정 분석 지원
- **실시간 스트리밍**: Apache Kafka를 활용한 실시간 데이터 스트리밍

## 개인 기여도

이 프로젝트는 **개인 프로젝트**로, 모든 작업을 직접 수행했습니다.

### 엔드투엔드 데이터 파이프라인 설계
- Raw 수집 → 전처리 → 감정 분석 → 시계열 분석 → DB 저장 → UI까지 풀 사이클 개발
- Collector / Preprocessing / Sentiment / Trend / API 계층 완전 분리 구성
- 재사용성과 유지보수성 높은 구조 설계

### API 통신·데이터 엔지니어링
- YouTube Data API 실제 호출 (Search + CommentThreads + Videos API)
- 오류 처리, 재시도 로직, 요청 제한 처리 구현
- DB 구조 설계 (SQLite → PostgreSQL 확장 가능)

### 한국어 NLP 모델 활용
- 규칙 기반 감정 분석기 직접 설계 (키워드 100+)
- KoBERT·KcBERT 등 BERT 기반 모델 적용 가능한 구조 설계
- OpenAI 기반 분석기 확장 기능 내장

### 시계열 분석·변화점 탐지
- 다양한 고급 알고리즘 구현 및 선택 기준 명확화:
  - SimpleChangeDetector: 기준선 대비 급격한 변화 감지
  - CUSUM: 누적 합 기반 변화점 탐지
  - Z-score: 분포 기반 이상치 탐지
  - Bayesian Change Point Detection: 급격 + 점진 변화 둘 다 처리
- 시간 단위 감정 평균 → 고급 알고리즘으로 변화점 감지
- UI에서 사용자가 알고리즘 선택 가능

### 데이터 시각화 & UX
- Streamlit 기반 실시간 대시보드 구현
- Donut / Gauge / Word Cloud / Trend Chart 구현
- 변화점 Highlight(점선/마커)로 인사이트 제공

### 백엔드·서비스 설계
- FastAPI 기반 RESTful API 설계
- Swagger UI 자동 문서화
- Dashboard ↔ API 연동 완성

### 문서화
- 아키텍처 문서 작성
- 설치·실행 가이드 작성
- API 문서 작성
- 구현 상태 문서 작성

## 프로젝트 구조

```
Social-sentiment-trend-monitor/
├── app/                    # 웹 애플리케이션
│   ├── web_demo.py        # Streamlit 대시보드 (트렌드 시각화, Word Cloud, 변화점 Highlight)
│   └── api.py             # FastAPI 백엔드 (RESTful API)
├── configs/               # 설정 파일
│   ├── *.example.yaml     # 설정 파일 예제 (복사하여 사용)
│   ├── config_collector.yaml    # 데이터 수집 설정
│   ├── config_sentiment.yaml    # 감정 분석 설정
│   ├── config_trend.yaml        # 트렌드 분석 설정
│   └── config_api.yaml          # API 서버 설정
├── data/                  # 데이터
│   ├── raw/              # 원본 수집 데이터
│   ├── processed/        # 전처리된 데이터
│   └── database/          # 데이터베이스 파일
├── src/                   # 소스 코드
│   ├── collectors/       # 데이터 수집
│   │   ├── base_collector.py
│   │   ├── youtube_collector.py
│   │   ├── twitter_collector.py
│   │   ├── news_collector.py
│   │   ├── blog_collector.py
│   │   └── collector_manager.py
│   ├── preprocessing/    # 전처리
│   │   ├── text_cleaner.py
│   │   └── deduplicator.py
│   ├── sentiment/        # 감정 분석
│   │   ├── rule_based_analyzer.py  # 규칙 기반 분석기 (기본 사용)
│   │   ├── kcbert_analyzer.py      # KcBERT 분석기
│   │   ├── kobert_analyzer.py      # KoBERT 분석기 (호환성)
│   │   ├── llm_analyzer.py         # LLM 분석기 (OpenAI API)
│   │   └── sentiment_utils.py      # 감정 분석 통합 유틸리티
│   ├── trend/            # 트렌드 분석
│   │   ├── time_series.py           # 시계열 집계
│   │   ├── simple_change_detector.py # 간단한 변화점 탐지 (v0)
│   │   ├── change_detection.py      # 전문 변화점 탐지 (v1, ruptures)
│   │   └── trend_utils.py           # 트렌드 분석 통합 유틸리티
│   ├── database/         # 데이터베이스
│   │   ├── models.py
│   │   └── db_manager.py
│   └── utils/           # 유틸리티
│       ├── config.py
│       ├── logger.py
│       └── seed.py
├── scripts/              # 실행 스크립트
│   ├── run_collector.py
│   ├── run_sentiment_analysis.py
│   ├── run_trend_detection.py
│   ├── run_streamlit.sh
│   └── run_api.sh
├── experiments/          # 실험 결과
├── docs/                 # 문서
├── README.md             # 프로젝트 설명
├── requirements.txt      # 의존성 목록
└── setup.py              # 패키지 설정
```

## 라이선스 & 작성자

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

**작성자**: yanggangyi

- GitHub: [@yanggangyiplus](https://github.com/yanggangyiplus)

## 상세 문서

- [설치 및 실행 가이드](docs/INSTALL_AND_RUN.md)
- [YouTube API 설정 가이드](docs/YOUTUBE_SETUP.md)
- [API 문서](docs/API_DOCUMENTATION.md)
- [아키텍처 문서](docs/ARCHITECTURE.md)
