# 설치 및 실행 가이드

## 목차
- [시스템 요구사항](#시스템-요구사항)
- [설치](#설치)
- [설정](#설정)
- [실행](#실행)
- [문제 해결](#문제-해결)

---

## 시스템 요구사항

- Python 3.11 이상
- 최소 4GB RAM
- 인터넷 연결 (API 호출용)

### 선택 사항
- GPU (KoBERT 모델 가속화용)
- PostgreSQL (대용량 데이터 처리용)

---

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/yanggangyiplus/Social-sentiment-trend-monitor.git
cd Social-sentiment-trend-monitor
```

### 2. 가상 환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

---

## 설정

### 1. API 키 설정

각 설정 파일에 API 키를 입력해야 합니다.

#### `configs/config_collector.yaml`

```yaml
sources:
  youtube:
    enabled: true
    api_key: "YOUR_YOUTUBE_API_KEY"
  
  twitter:
    enabled: true
    api_key: "YOUR_TWITTER_API_KEY"
    api_secret: "YOUR_TWITTER_API_SECRET"
    access_token: "YOUR_ACCESS_TOKEN"
    access_token_secret: "YOUR_ACCESS_TOKEN_SECRET"
```

#### `configs/config_sentiment.yaml`

```yaml
model:
  type: "llm"  # 또는 "kobert"
  llm:
    api_key: "YOUR_OPENAI_API_KEY"
```

### 2. 데이터베이스 설정

기본적으로 SQLite를 사용합니다. PostgreSQL을 사용하려면:

```yaml
# configs/config_api.yaml
database:
  url: "postgresql://user:password@localhost:5432/sentiment_db"
```

---

## 실행

### 1. 데이터 수집

```bash
python scripts/run_collector.py --keyword "아이폰" --max-results 50
```

### 2. 감정 분석

```bash
python scripts/run_sentiment_analysis.py --keyword "아이폰" --hours 24
```

### 3. 트렌드 탐지

```bash
python scripts/run_trend_detection.py --keyword "아이폰" --hours 24
```

### 4. FastAPI 백엔드 실행

```bash
bash scripts/run_api.sh
# 또는
uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Streamlit 대시보드 실행

```bash
bash scripts/run_streamlit.sh
# 또는
streamlit run app/web_demo.py --server.port 8501
```

---

## 문제 해결

### 모듈을 찾을 수 없음

```bash
# 프로젝트 루트에서 실행 확인
pwd
# /path/to/Social-sentiment-trend-monitor

# Python 경로 확인
python -c "import sys; print(sys.path)"
```

### 데이터베이스 오류

```bash
# 데이터베이스 디렉토리 생성
mkdir -p data/database

# 권한 확인
ls -la data/database
```

### API 키 오류

- 설정 파일의 API 키가 올바른지 확인
- API 키의 권한 및 할당량 확인
- 네트워크 연결 확인

---

## 다음 단계

- [API 문서](API_DOCUMENTATION.md) 참조
- [아키텍처 문서](ARCHITECTURE.md) 참조

