# YouTube API 설정 가이드

## YouTube Data API v3 키 발급

### 1. Google Cloud Console 접속
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택

### 2. YouTube Data API v3 활성화
1. **API 및 서비스** > **라이브러리** 이동
2. "YouTube Data API v3" 검색
3. **사용 설정** 클릭

### 3. API 키 생성
1. **API 및 서비스** > **사용자 인증 정보** 이동
2. **사용자 인증 정보 만들기** > **API 키** 선택
3. 생성된 API 키 복사

### 4. API 키 제한 설정 (권장)
1. 생성된 API 키 클릭
2. **애플리케이션 제한사항** 설정:
   - **HTTP 리퍼러(웹사이트)** 선택 (웹 애플리케이션인 경우)
   - 또는 **IP 주소(웹 서버, cron 작업 등)** 선택 (서버 애플리케이션인 경우)
3. **API 제한사항** 설정:
   - **키 제한** 선택
   - **YouTube Data API v3**만 선택

### 5. 설정 파일에 API 키 입력

`configs/config_collector.yaml` 파일을 열고:

```yaml
sources:
  youtube:
    enabled: true
    api_key: "YOUR_API_KEY_HERE"  # 여기에 API 키 입력
    max_results: 10
    max_comments_per_video: 20
```

## API 할당량

- **일일 할당량**: 기본 10,000 units/day
- **Search API**: 100 units/request
- **CommentThreads API**: 1 unit/request

### 할당량 계산 예시
- 비디오 10개 검색: 10 × 100 = 1,000 units
- 댓글 200개 수집: 200 × 1 = 200 units
- **총 1,200 units** (일일 할당량의 12%)

## 사용 방법

### 기본 사용
```bash
python scripts/run_collector.py --keyword "아이폰" --max-results 10
```

### 설정 변경
`configs/config_collector.yaml`에서 다음 설정 조정 가능:
- `max_results`: 검색할 비디오 개수 (기본값: 10, 최대: 50)
- `max_comments_per_video`: 비디오당 댓글 개수 (기본값: 20, 최대: 100)

## 문제 해결

### API 키 오류
- API 키가 올바른지 확인
- YouTube Data API v3가 활성화되었는지 확인
- API 키 제한 설정 확인

### 할당량 초과
- 일일 할당량 확인: [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
- 할당량 증가 요청 또는 다음 날까지 대기

### 댓글 수집 실패
- 일부 비디오는 댓글이 비활성화되어 있을 수 있음
- 비디오가 삭제되었거나 비공개일 수 있음

