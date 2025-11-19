# 아키텍처 문서

## 시스템 아키텍처 개요

본 프로젝트는 실시간 감정 분석 및 트렌드 모니터링을 위한 마이크로서비스 아키텍처를 따릅니다.

---

## 컴포넌트 구조

### 1. 데이터 수집 계층 (Collection Layer)

**역할**: 다양한 소스에서 텍스트 데이터 수집

**구성 요소**:
- `BaseCollector`: 수집기 기본 클래스
- `YouTubeCollector`: YouTube 데이터 수집
- `TwitterCollector`: Twitter(X) 데이터 수집
- `NewsCollector`: 뉴스 기사 수집
- `BlogCollector`: 블로그 포스트 수집
- `CollectorManager`: 수집기 통합 관리

**특징**:
- 각 소스별 독립적인 수집기 구현
- 설정 기반 활성화/비활성화
- 에러 처리 및 재시도 로직

---

### 2. 전처리 계층 (Preprocessing Layer)

**역할**: 수집된 텍스트 데이터 정제 및 정규화

**구성 요소**:
- `TextCleaner`: 텍스트 정제 (HTML 제거, URL 제거 등)
- `Deduplicator`: 중복 데이터 제거

**처리 단계**:
1. HTML 태그 제거
2. URL 및 이메일 제거
3. 특수 문자 정리
4. 중복 제거 (해시 기반)

---

### 3. 감정 분석 계층 (Sentiment Analysis Layer)

**역할**: 텍스트의 감정 분석 수행

**구성 요소**:
- `KoBERTAnalyzer`: KoBERT 기반 감정 분석
- `LLMAnalyzer`: LLM 기반 감정 분석
- `SentimentAnalyzer`: 통합 감정 분석기

**지원 모델**:
- KoBERT: 한국어 특화 BERT 모델
- OpenAI GPT: 범용 LLM 모델

**출력**:
- 긍정 점수 (0.0 ~ 1.0)
- 부정 점수 (0.0 ~ 1.0)
- 중립 점수 (0.0 ~ 1.0)
- 예측된 감정 클래스

---

### 4. 트렌드 분석 계층 (Trend Analysis Layer)

**역할**: 시계열 데이터 분석 및 변화 탐지

**구성 요소**:
- `TimeSeriesAnalyzer`: 시계열 집계 및 분석
- `ChangeDetector`: 변화점 탐지
- `TrendAnalyzer`: 통합 트렌드 분석기

**알고리즘**:
- 시계열 집계 (시간 단위)
- Change Point Detection (PELT, Window 기반)
- 트렌드 방향 판단 (선형 회귀)

---

### 5. 데이터 저장 계층 (Storage Layer)

**역할**: 데이터 영속성 관리

**구성 요소**:
- `DatabaseManager`: 데이터베이스 연결 관리
- SQLAlchemy ORM 모델

**데이터 모델**:
- `CollectedText`: 수집된 텍스트 데이터
- `SentimentAnalysis`: 감정 분석 결과
- `TrendAlert`: 트렌드 변화 알림

---

### 6. API 계층 (API Layer)

**역할**: RESTful API 제공

**구성 요소**:
- FastAPI 애플리케이션
- 엔드포인트:
  - `/sentiment/recent`: 감정 분석 결과 조회
  - `/trend/{keyword}`: 트렌드 조회
  - `/alerts`: 알림 조회
  - `/collect`: 데이터 수집 시작

---

### 7. 프레젠테이션 계층 (Presentation Layer)

**역할**: 사용자 인터페이스 제공

**구성 요소**:
- Streamlit 대시보드
- 실시간 시각화
- 인터랙티브 필터링

---

## 데이터 흐름

```
1. 데이터 수집
   ↓
2. 전처리 (정제, 중복 제거)
   ↓
3. 데이터베이스 저장 (CollectedText)
   ↓
4. 감정 분석
   ↓
5. 데이터베이스 저장 (SentimentAnalysis)
   ↓
6. 트렌드 분석
   ↓
7. 변화점 탐지 및 알림 생성
   ↓
8. 데이터베이스 저장 (TrendAlert)
   ↓
9. API/대시보드를 통한 조회
```

---

## 확장성 고려사항

### 수평 확장
- 각 수집기는 독립적으로 실행 가능
- API 서버는 여러 인스턴스로 확장 가능
- 데이터베이스는 읽기 전용 복제본 추가 가능

### 수직 확장
- GPU를 통한 감정 분석 가속화
- PostgreSQL로 전환하여 대용량 데이터 처리

---

## 보안 고려사항

1. **API 키 관리**: 환경 변수 또는 시크릿 관리 시스템 사용
2. **입력 검증**: 모든 사용자 입력 검증
3. **Rate Limiting**: API 호출 제한
4. **인증/인가**: 프로덕션 환경에서 API 키 기반 인증 추가

---

## 모니터링 및 로깅

- 로그 파일: `experiments/logs/`
- 로그 레벨: INFO, ERROR
- 구조화된 로깅 (JSON 형식 권장)

---

## 배포 고려사항

### Docker 배포
- 각 컴포넌트별 Dockerfile 제공
- Docker Compose를 통한 통합 배포

### 클라우드 배포
- AWS/GCP/Azure 호환
- 컨테이너 오케스트레이션 지원

