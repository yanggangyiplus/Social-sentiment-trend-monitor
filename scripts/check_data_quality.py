#!/usr/bin/env python3
"""
데이터 품질 검증 스크립트
수집된 데이터의 품질을 체크하고 점수를 출력
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
import re

# 프로젝트 루트를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from src.database.db_manager import init_database, get_db
from src.database.models import CollectedText
from src.preprocessing.text_cleaner import TextCleaner
from src.preprocessing.deduplicator import Deduplicator


class DataQualityChecker:
    """
    데이터 품질 검증 클래스
    """
    
    def __init__(self, db_session):
        """
        데이터 품질 검증기 초기화
        
        Args:
            db_session: 데이터베이스 세션
        """
        self.db = db_session
        self.text_cleaner = TextCleaner()
        self.deduplicator = Deduplicator()
    
    def check_all(self, keyword: str = None, hours: int = 24) -> dict:
        """
        전체 데이터 품질 검증
        
        Args:
            keyword: 키워드 필터 (None이면 전체)
            hours: 검증할 시간 범위 (시간)
            
        Returns:
            품질 검증 결과 딕셔너리
        """
        # 데이터 조회
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = self.db.query(CollectedText)
        
        if keyword:
            query = query.filter(CollectedText.keyword == keyword)
        
        query = query.filter(CollectedText.collected_at >= start_time)
        texts = query.all()
        
        if not texts:
            return {"error": "데이터가 없습니다."}
        
        # 각 항목별 검증
        results = {
            "total_count": len(texts),
            "keyword": keyword or "전체",
            "time_range_hours": hours,
            "checks": {}
        }
        
        # 1. 텍스트 품질 체크
        results["checks"]["text_quality"] = self._check_text_quality(texts)
        
        # 2. 타임스탬프 정상 여부
        results["checks"]["timestamp"] = self._check_timestamp(texts)
        
        # 3. 언어 감지
        results["checks"]["language"] = self._check_language(texts)
        
        # 4. 중복 댓글 여부
        results["checks"]["duplicates"] = self._check_duplicates(texts)
        
        # 5. 키워드 포함 여부
        if keyword:
            results["checks"]["keyword_match"] = self._check_keyword_match(texts, keyword)
        
        # 전체 품질 점수 계산
        results["quality_score"] = self._calculate_quality_score(results["checks"])
        
        return results
    
    def _check_text_quality(self, texts: list) -> dict:
        """
        텍스트 품질 체크
        
        Args:
            texts: 텍스트 객체 리스트
            
        Returns:
            텍스트 품질 검증 결과
        """
        total = len(texts)
        empty_count = 0
        emoji_count = 0
        url_count = 0
        whitespace_ratio_sum = 0
        
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map symbols
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        for text_obj in texts:
            text = text_obj.text or ""
            
            if not text.strip():
                empty_count += 1
                continue
            
            # 이모지 체크
            if emoji_pattern.search(text):
                emoji_count += 1
            
            # URL 체크
            if url_pattern.search(text):
                url_count += 1
            
            # 공백 비율 계산
            if len(text) > 0:
                whitespace_ratio = text.count(' ') / len(text)
                whitespace_ratio_sum += whitespace_ratio
        
        avg_whitespace_ratio = whitespace_ratio_sum / total if total > 0 else 0
        
        return {
            "empty_text_ratio": empty_count / total if total > 0 else 0,
            "emoji_text_ratio": emoji_count / total if total > 0 else 0,
            "url_text_ratio": url_count / total if total > 0 else 0,
            "avg_whitespace_ratio": avg_whitespace_ratio,
            "score": 1.0 - min(1.0, (empty_count + emoji_count * 0.3 + url_count * 0.2) / total)
        }
    
    def _check_timestamp(self, texts: list) -> dict:
        """
        타임스탬프 정상 여부 체크
        
        Args:
            texts: 텍스트 객체 리스트
            
        Returns:
            타임스탬프 검증 결과
        """
        total = len(texts)
        null_count = 0
        future_count = 0
        old_count = 0
        
        now = datetime.utcnow()
        one_year_ago = now - timedelta(days=365)
        
        for text_obj in texts:
            if not text_obj.collected_at:
                null_count += 1
                continue
            
            if text_obj.collected_at > now:
                future_count += 1
            
            if text_obj.collected_at < one_year_ago:
                old_count += 1
        
        return {
            "null_timestamp_ratio": null_count / total if total > 0 else 0,
            "future_timestamp_ratio": future_count / total if total > 0 else 0,
            "old_timestamp_ratio": old_count / total if total > 0 else 0,
            "score": 1.0 - min(1.0, (null_count + future_count + old_count) / total)
        }
    
    def _check_language(self, texts: list) -> dict:
        """
        언어 감지 체크
        
        Args:
            texts: 텍스트 객체 리스트
            
        Returns:
            언어 검증 결과
        """
        total = len(texts)
        language_counts = Counter()
        
        for text_obj in texts:
            lang = self.text_cleaner.detect_language(text_obj.text or "")
            language_counts[lang] += 1
        
        korean_ratio = language_counts.get("ko", 0) / total if total > 0 else 0
        
        return {
            "korean_ratio": korean_ratio,
            "english_ratio": language_counts.get("en", 0) / total if total > 0 else 0,
            "mixed_ratio": language_counts.get("mixed", 0) / total if total > 0 else 0,
            "language_distribution": dict(language_counts),
            "score": korean_ratio  # 한국어 비율이 높을수록 좋음
        }
    
    def _check_duplicates(self, texts: list) -> dict:
        """
        중복 댓글 체크
        
        Args:
            texts: 텍스트 객체 리스트
            
        Returns:
            중복 검증 결과
        """
        # 중복 제거 전후 비교
        text_dicts = [
            {"text": text_obj.text, "id": text_obj.id}
            for text_obj in texts
        ]
        
        unique_texts = self.deduplicator.remove_duplicates(text_dicts, key_field="text")
        
        duplicate_count = len(text_dicts) - len(unique_texts)
        duplicate_ratio = duplicate_count / len(text_dicts) if text_dicts else 0
        
        return {
            "total_count": len(text_dicts),
            "unique_count": len(unique_texts),
            "duplicate_count": duplicate_count,
            "duplicate_ratio": duplicate_ratio,
            "score": 1.0 - duplicate_ratio
        }
    
    def _check_keyword_match(self, texts: list, keyword: str) -> dict:
        """
        키워드 포함 여부 체크
        
        Args:
            texts: 텍스트 객체 리스트
            keyword: 검색 키워드
            
        Returns:
            키워드 매칭 검증 결과
        """
        total = len(texts)
        matched_count = 0
        
        keyword_lower = keyword.lower()
        
        for text_obj in texts:
            text_lower = (text_obj.text or "").lower()
            if keyword_lower in text_lower:
                matched_count += 1
        
        match_ratio = matched_count / total if total > 0 else 0
        
        return {
            "matched_count": matched_count,
            "match_ratio": match_ratio,
            "score": match_ratio
        }
    
    def _calculate_quality_score(self, checks: dict) -> float:
        """
        전체 품질 점수 계산
        
        Args:
            checks: 각 검증 항목 결과
            
        Returns:
            전체 품질 점수 (0.0 ~ 1.0)
        """
        weights = {
            "text_quality": 0.25,
            "timestamp": 0.15,
            "language": 0.20,
            "duplicates": 0.20,
            "keyword_match": 0.20
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for check_name, weight in weights.items():
            if check_name in checks and "score" in checks[check_name]:
                total_score += checks[check_name]["score"] * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
    
    def print_report(self, results: dict):
        """
        검증 결과 리포트 출력
        
        Args:
            results: 검증 결과 딕셔너리
        """
        if "error" in results:
            print(f"❌ {results['error']}")
            return
        
        print("=" * 70)
        print("데이터 품질 검증 리포트")
        print("=" * 70)
        print(f"\n📊 기본 정보")
        print(f"  키워드: {results['keyword']}")
        print(f"  총 데이터 수: {results['total_count']:,}개")
        print(f"  시간 범위: 최근 {results['time_range_hours']}시간")
        print(f"  전체 품질 점수: {results['quality_score']:.2%}")
        
        checks = results["checks"]
        
        # 텍스트 품질
        print(f"\n📝 텍스트 품질")
        text_q = checks.get("text_quality", {})
        print(f"  빈 텍스트 비율: {text_q.get('empty_text_ratio', 0):.2%}")
        print(f"  이모지 포함 비율: {text_q.get('emoji_text_ratio', 0):.2%}")
        print(f"  URL 포함 비율: {text_q.get('url_text_ratio', 0):.2%}")
        print(f"  평균 공백 비율: {text_q.get('avg_whitespace_ratio', 0):.2%}")
        print(f"  점수: {text_q.get('score', 0):.2%}")
        
        # 타임스탬프
        print(f"\n⏰ 타임스탬프")
        timestamp = checks.get("timestamp", {})
        print(f"  NULL 타임스탬프 비율: {timestamp.get('null_timestamp_ratio', 0):.2%}")
        print(f"  미래 타임스탬프 비율: {timestamp.get('future_timestamp_ratio', 0):.2%}")
        print(f"  오래된 타임스탬프 비율: {timestamp.get('old_timestamp_ratio', 0):.2%}")
        print(f"  점수: {timestamp.get('score', 0):.2%}")
        
        # 언어
        print(f"\n🌐 언어 분포")
        language = checks.get("language", {})
        print(f"  한국어 비율: {language.get('korean_ratio', 0):.2%}")
        print(f"  영어 비율: {language.get('english_ratio', 0):.2%}")
        print(f"  혼합 비율: {language.get('mixed_ratio', 0):.2%}")
        print(f"  점수: {language.get('score', 0):.2%}")
        
        # 중복
        print(f"\n🔄 중복 검사")
        duplicates = checks.get("duplicates", {})
        print(f"  총 개수: {duplicates.get('total_count', 0):,}개")
        print(f"  고유 개수: {duplicates.get('unique_count', 0):,}개")
        print(f"  중복 개수: {duplicates.get('duplicate_count', 0):,}개")
        print(f"  중복 비율: {duplicates.get('duplicate_ratio', 0):.2%}")
        print(f"  점수: {duplicates.get('score', 0):.2%}")
        
        # 키워드 매칭
        if "keyword_match" in checks:
            print(f"\n🔍 키워드 매칭")
            keyword_match = checks["keyword_match"]
            print(f"  매칭된 개수: {keyword_match.get('matched_count', 0):,}개")
            print(f"  매칭 비율: {keyword_match.get('match_ratio', 0):.2%}")
            print(f"  점수: {keyword_match.get('score', 0):.2%}")
        
        print("\n" + "=" * 70)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="데이터 품질 검증 스크립트")
    parser.add_argument("--keyword", type=str, help="검증할 키워드 (지정하지 않으면 전체)")
    parser.add_argument("--hours", type=int, default=24, help="검증할 시간 범위 (시간, 기본값: 24)")
    
    args = parser.parse_args()
    
    # 데이터베이스 초기화
    init_database("sqlite:///data/database/sentiment.db")
    db = next(get_db())
    
    try:
        # 데이터 품질 검증
        checker = DataQualityChecker(db)
        results = checker.check_all(args.keyword, args.hours)
        
        # 리포트 출력
        checker.print_report(results)
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

