"""
YouTube 데이터 서비스
비디오별 댓글 및 감정 분석 데이터 조회 최적화
"""
from typing import Dict, List, Tuple
from collections import defaultdict

from src.database.db_manager import get_db_session
from src.database.models import CollectedText, SentimentAnalysis
from app.web.utils.logger_config import youtube_logger as logger


def get_all_video_data(keyword: str) -> Tuple[List[Dict], Dict[str, List], Dict[int, Dict]]:
    """
    한 번의 DB 세션으로 모든 비디오 데이터 조회 (성능 최적화)
    
    Args:
        keyword: 검색 키워드
    
    Returns:
        (비디오 리스트, {video_id: [댓글 리스트]}, {text_id: 감정 분석 결과}) 튜플
    """
    try:
        with get_db_session() as db:
            # 모든 댓글 및 감정 분석 결과를 한 번에 조회
            all_comments = db.query(CollectedText).filter(
                CollectedText.keyword == keyword,
                CollectedText.source == "youtube",
                CollectedText.video_id.isnot(None)
            ).order_by(CollectedText.collected_at.desc()).all()
            
            # 비디오별로 그룹화
            videos_dict = {}
            comments_by_video = defaultdict(list)
            
            for comment in all_comments:
                video_id = comment.video_id
                if video_id and video_id not in videos_dict:
                    videos_dict[video_id] = {
                        "video_id": video_id,
                        "title": comment.video_title or "제목 없음",
                        "channel_name": comment.channel_name or "채널명 없음",
                        "view_count": comment.view_count or 0,
                        "like_count": comment.like_count or 0,
                        "url": comment.url or f"https://www.youtube.com/watch?v={video_id}"
                    }
                comments_by_video[video_id].append(comment)
            
            # 모든 감정 분석 결과 조회
            comment_ids = [c.id for c in all_comments]
            sentiments_dict = {}
            if comment_ids:
                sentiments = db.query(SentimentAnalysis).filter(
                    SentimentAnalysis.text_id.in_(comment_ids)
                ).all()
                # 딕셔너리로 변환 (세션 종료 전에)
                sentiments_dict = {sent.text_id: sent for sent in sentiments}
            
            videos_list = list(videos_dict.values())
            
            return videos_list, dict(comments_by_video), sentiments_dict
            
    except Exception as e:
        logger.error(f"YouTube 데이터 조회 실패 (키워드: {keyword}): {e}", exc_info=True)
        return [], {}, {}

