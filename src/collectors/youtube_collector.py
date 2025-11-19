"""
YouTube 데이터 수집기
Search API + CommentThreads API 조합으로 실제 댓글 수집
"""
from typing import List, Dict, Any, Optional
import requests
import time
from .base_collector import BaseCollector


class YouTubeCollector(BaseCollector):
    """
    YouTube 댓글 및 제목 수집기
    Search API로 비디오 검색 → CommentThreads API로 댓글 수집
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        YouTube 수집기 초기화
        
        Args:
            config: YouTube 설정 딕셔너리
        """
        super().__init__(config)
        self.api_key = config.get("api_key", "")
        self.max_results = config.get("max_results", 50)
        self.max_comments_per_video = config.get("max_comments_per_video", 20)
        self.language = config.get("language", "ko")
        self.api_base_url = "https://www.googleapis.com/youtube/v3"
    
    def collect(self, keyword: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        YouTube에서 키워드 기반 데이터 수집
        Search API로 비디오 검색 → Videos API로 상세 정보 수집 → 각 비디오의 댓글 수집
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 수집할 비디오 개수
            
        Returns:
            수집된 데이터 리스트 (댓글 텍스트 + 비디오 정보)
        """
        if not self.enabled or not self.api_key:
            print("YouTube 수집기가 비활성화되었거나 API 키가 없습니다.")
            return []
        
        max_results = max_results or self.max_results
        all_results = []
        
        try:
            # 1단계: Search API로 비디오 검색
            video_ids = self._search_videos(keyword, max_results)
            print(f"검색된 비디오 개수: {len(video_ids)}")
            
            # 2단계: Videos API로 비디오 상세 정보 수집
            video_info_dict = self._get_video_details(video_ids)
            
            # 3단계: 각 비디오의 댓글 수집
            for idx, video_id in enumerate(video_ids, 1):
                print(f"비디오 {idx}/{len(video_ids)} 댓글 수집 중... (Video ID: {video_id})")
                video_info = video_info_dict.get(video_id, {})
                comments = self._collect_comments(video_id, video_info)
                all_results.extend(comments)
                
                # API 할당량 고려하여 딜레이 추가
                time.sleep(0.1)
        
        except Exception as e:
            print(f"YouTube 수집 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"총 {len(all_results)}개 댓글 수집 완료")
        return all_results
    
    def _search_videos(self, keyword: str, max_results: int) -> List[str]:
        """
        Search API를 사용하여 키워드로 비디오 검색
        
        Args:
            keyword: 검색 키워드
            max_results: 최대 검색 결과 개수
            
        Returns:
            비디오 ID 리스트
        """
        video_ids = []
        
        try:
            search_url = f"{self.api_base_url}/search"
            params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "maxResults": min(max_results, 50),  # API 제한: 최대 50개
                "key": self.api_key,
                "relevanceLanguage": self.language,
                "order": "relevance"  # 관련도 순
            }
            
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                video_ids.append(video_id)
            
        except requests.exceptions.RequestException as e:
            print(f"비디오 검색 실패: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"응답 내용: {e.response.text}")
        
        return video_ids
    
    def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Videos API를 사용하여 비디오 상세 정보 수집
        비디오 제목, 채널명, 조회수, 좋아요 수 등을 가져옴
        
        Args:
            video_ids: 비디오 ID 리스트
            
        Returns:
            비디오 ID를 키로 하는 비디오 정보 딕셔너리
            {
                video_id: {
                    "title": "비디오 제목",
                    "channel_name": "채널명",
                    "view_count": 조회수,
                    "like_count": 좋아요 수
                }
            }
        """
        video_info_dict = {}
        
        if not video_ids:
            return video_info_dict
        
        try:
            # Videos API는 최대 50개까지 한 번에 조회 가능
            videos_url = f"{self.api_base_url}/videos"
            params = {
                "part": "snippet,statistics",
                "id": ",".join(video_ids[:50]),  # 최대 50개
                "key": self.api_key
            }
            
            response = requests.get(videos_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("items", []):
                video_id = item["id"]
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                
                video_info_dict[video_id] = {
                    "title": snippet.get("title", ""),
                    "channel_name": snippet.get("channelTitle", ""),
                    "view_count": int(statistics.get("viewCount", 0)),
                    "like_count": int(statistics.get("likeCount", 0)),
                    "published_at": snippet.get("publishedAt", "")
                }
        
        except requests.exceptions.RequestException as e:
            print(f"비디오 상세 정보 수집 실패: {e}")
        
        return video_info_dict
    
    def _collect_comments(self, video_id: str, video_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        CommentThreads API를 사용하여 비디오의 댓글 수집
        
        Args:
            video_id: YouTube 비디오 ID
            
        Returns:
            댓글 데이터 리스트
        """
        comments = []
        
        try:
            comments_url = f"{self.api_base_url}/commentThreads"
            params = {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(self.max_comments_per_video, 100),  # API 제한: 최대 100개
                "key": self.api_key,
                "order": "relevance",  # 관련도 순
                "textFormat": "plainText"
            }
            
            response = requests.get(comments_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 응답 파싱 (비디오 정보 포함)
            parsed_comments = self._parse_comments_response(data, video_id, video_info)
            comments.extend(parsed_comments)
            
        except requests.exceptions.RequestException as e:
            print(f"댓글 수집 실패 (Video ID: {video_id}): {e}")
            if hasattr(e, 'response') and e.response is not None:
                error_data = e.response.json()
                error_message = error_data.get("error", {}).get("message", "알 수 없는 오류")
                print(f"오류 메시지: {error_message}")
        
        return comments
    
    def _parse_comments_response(self, response_data: Dict[str, Any], video_id: str, video_info: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        CommentThreads API 응답 파싱
        
        Args:
            response_data: API 응답 데이터
            video_id: 비디오 ID
            
        Returns:
            파싱된 댓글 데이터 리스트
        """
        parsed_comments = []
        
        for item in response_data.get("items", []):
            snippet = item.get("snippet", {})
            top_level_comment = snippet.get("topLevelComment", {}).get("snippet", {})
            
            comment_text = top_level_comment.get("textDisplay", "")
            if not comment_text:
                continue
            
            author = top_level_comment.get("authorDisplayName", "")
            comment_id = item.get("id", "")
            published_at = top_level_comment.get("publishedAt", "")
            
            result = self._create_result(
                text=comment_text,
                author=author,
                url=f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}",
                source="youtube",
                video_id=video_id,
                comment_id=comment_id,
                published_at=published_at,
                video_title=video_info.get("title", "") if video_info else "",
                channel_name=video_info.get("channel_name", "") if video_info else "",
                view_count=video_info.get("view_count", 0) if video_info else 0,
                like_count=video_info.get("like_count", 0) if video_info else 0
            )
            parsed_comments.append(result)
        
        return parsed_comments
    
    def save_to_db(self, data: List[Dict[str, Any]], keyword: str, db_session):
        """
        수집된 데이터를 데이터베이스에 저장
        
        Args:
            data: 수집된 데이터 리스트
            keyword: 키워드
            db_session: 데이터베이스 세션
        """
        from src.database.models import CollectedText
        
        saved_count = 0
        for item in data:
            try:
                text_obj = CollectedText(
                    keyword=keyword,
                    source=item.get('source', 'youtube'),
                    text=item.get('text', ''),
                    author=item.get('author'),
                    url=item.get('url'),
                    collected_at=item.get('collected_at'),
                    # YouTube 비디오 정보
                    video_id=item.get('video_id'),
                    video_title=item.get('video_title'),
                    channel_name=item.get('channel_name'),
                    view_count=item.get('view_count'),
                    like_count=item.get('like_count')
                )
                db_session.add(text_obj)
                saved_count += 1
            except Exception as e:
                print(f"데이터 저장 실패: {e}")
                continue
        
        try:
            db_session.commit()
            print(f"✅ {saved_count}개 데이터 저장 완료")
        except Exception as e:
            db_session.rollback()
            print(f"❌ 데이터베이스 커밋 실패: {e}")

