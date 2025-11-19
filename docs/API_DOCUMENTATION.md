# API 문서

## 기본 정보

- **Base URL**: `http://localhost:8000`
- **API 버전**: v1.0.0
- **문서**: `http://localhost:8000/docs` (Swagger UI)

---

## 엔드포인트

### 1. 루트 엔드포인트

**GET** `/`

API 기본 정보 반환

**응답**:
```json
{
  "message": "Social Sentiment & Trend Monitor API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### 2. 헬스 체크

**GET** `/health`

서버 상태 확인

**응답**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00"
}
```

---

### 3. 최근 감정 분석 결과 조회

**GET** `/sentiment/recent`

최근 감정 분석 결과를 조회합니다.

**쿼리 파라미터**:
- `keyword` (optional): 키워드 필터
- `source` (optional): 소스 필터 (youtube, twitter, news, blog)
- `limit` (optional): 최대 반환 개수 (기본값: 100, 최대: 1000)

**예시**:
```bash
GET /sentiment/recent?keyword=아이폰&source=youtube&limit=50
```

**응답**:
```json
[
  {
    "id": 1,
    "keyword": "아이폰",
    "source": "youtube",
    "positive_score": 0.7,
    "negative_score": 0.2,
    "neutral_score": 0.1,
    "predicted_sentiment": "positive",
    "analyzed_at": "2024-01-01T00:00:00"
  }
]
```

---

### 4. 트렌드 조회

**GET** `/trend/{keyword}`

특정 키워드의 트렌드를 조회합니다.

**경로 파라미터**:
- `keyword`: 분석할 키워드

**쿼리 파라미터**:
- `hours` (optional): 분석 기간 (시간, 기본값: 24, 최대: 168)

**예시**:
```bash
GET /trend/아이폰?hours=48
```

**응답**:
```json
{
  "keyword": "아이폰",
  "trend_direction": "increasing",
  "change_points": [
    "2024-01-01T12:00:00",
    "2024-01-01T18:00:00"
  ],
  "alerts": [
    {
      "change_point": "2024-01-01T12:00:00",
      "change_type": "increase",
      "change_rate": 25.5,
      "previous_sentiment": 0.3,
      "current_sentiment": 0.5
    }
  ]
}
```

---

### 5. 알림 조회

**GET** `/alerts`

변화 감지 알림을 조회합니다.

**쿼리 파라미터**:
- `keyword` (optional): 키워드 필터
- `limit` (optional): 최대 반환 개수 (기본값: 50, 최대: 500)

**예시**:
```bash
GET /alerts?keyword=아이폰&limit=10
```

**응답**:
```json
[
  {
    "id": 1,
    "keyword": "아이폰",
    "change_type": "increase",
    "change_rate": 25.5,
    "change_point": "2024-01-01T12:00:00",
    "previous_sentiment": 0.3,
    "current_sentiment": 0.5
  }
]
```

---

### 6. 데이터 수집 시작

**POST** `/collect`

데이터 수집을 시작합니다.

**쿼리 파라미터**:
- `keyword`: 수집할 키워드
- `max_results` (optional): 소스당 최대 수집 개수 (기본값: 50, 최대: 500)

**예시**:
```bash
POST /collect?keyword=아이폰&max_results=100
```

**응답**:
```json
{
  "message": "키워드 '아이폰'에 대한 데이터 수집이 시작되었습니다.",
  "keyword": "아이폰",
  "max_results": 100,
  "status": "started"
}
```

---

### 7. 키워드 목록 조회

**GET** `/keywords`

등록된 키워드 목록을 조회합니다.

**쿼리 파라미터**:
- `limit` (optional): 최대 반환 개수 (기본값: 100, 최대: 1000)

**예시**:
```bash
GET /keywords?limit=50
```

**응답**:
```json
[
  "아이폰",
  "애플",
  "구글"
]
```

---

## 에러 응답

모든 에러는 다음 형식으로 반환됩니다:

```json
{
  "detail": "에러 메시지"
}
```

### 주요 HTTP 상태 코드

- `200`: 성공
- `400`: 잘못된 요청
- `404`: 리소스를 찾을 수 없음
- `500`: 서버 오류

---

## 인증

현재 버전에서는 인증이 필요하지 않습니다. 프로덕션 환경에서는 API 키 기반 인증을 추가하는 것을 권장합니다.

