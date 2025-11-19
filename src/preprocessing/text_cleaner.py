"""
텍스트 정제 모듈
감정 분석을 위한 텍스트 전처리
"""
import re
from typing import List, Tuple


class TextCleaner:
    """
    텍스트 정제 클래스
    KoBERT 성능 향상을 위한 전처리
    """
    
    # 이모지 패턴 (유니코드 범위)
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "]+",
        flags=re.UNICODE
    )
    
    # URL 패턴
    URL_PATTERN = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    # 반복 문자 패턴 (예: "와아아아" -> "와아")
    REPEAT_PATTERN = re.compile(r'(.)\1{2,}')
    
    @classmethod
    def clean_text(cls, text: str, remove_emoji: bool = True, 
                   remove_url: bool = True, normalize_repeat: bool = True) -> str:
        """
        텍스트 정제 (개선된 버전)
        
        Args:
            text: 원본 텍스트
            remove_emoji: 이모지 제거 여부
            remove_url: URL 제거 여부
            normalize_repeat: 반복 문자 축약 여부
            
        Returns:
            정제된 텍스트
        """
        if not text:
            return ""
        
        # 1. HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 2. URL 제거
        if remove_url:
            text = cls.URL_PATTERN.sub('', text)
        
        # 3. 이메일 제거
        text = re.sub(r'\S+@\S+', '', text)
        
        # 4. 이모지 제거
        if remove_emoji:
            text = cls.EMOJI_PATTERN.sub('', text)
        
        # 5. 반복 문자 축약 (예: "와아아아" -> "와아")
        if normalize_repeat:
            text = cls.REPEAT_PATTERN.sub(r'\1\1', text)
        
        # 6. 특수 문자 정리 (한글, 영문, 숫자, 기본 구두점, 공백만 유지)
        # 기본 구두점: . , ! ? 포함
        # 한글 자음/모음도 유지 (ㅋ, ㅎ 등 웃음 표현 보존)
        text = re.sub(r'[^\w\s가-힣ㄱ-ㅎㅏ-ㅣ.,!?]', ' ', text)
        
        # 7. 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 8. 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    @classmethod
    def clean_text_for_sentiment(cls, text: str) -> str:
        """
        감정 분석을 위한 텍스트 정제 (최적화된 버전)
        규칙 기반 분석기를 위해 웃음 표현(ㅋ, ㅎ 등) 보존
        
        Args:
            text: 원본 텍스트
            
        Returns:
            감정 분석에 적합한 정제된 텍스트
        """
        if not text:
            return ""
        
        # 1. HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 2. URL 제거
        text = cls.URL_PATTERN.sub('', text)
        
        # 3. 이메일 제거
        text = re.sub(r'\S+@\S+', '', text)
        
        # 4. 이모지 제거 (유니코드 이모지만, 한글 자음/모음은 보존)
        text = cls.EMOJI_PATTERN.sub('', text)
        
        # 5. 반복 문자 축약 (예: "와아아아" -> "와아", "ㅋㅋㅋㅋ" -> "ㅋㅋ")
        text = cls.REPEAT_PATTERN.sub(r'\1\1', text)
        
        # 6. 특수 문자 정리 (한글, 영문, 숫자, 기본 구두점, 공백만 유지)
        # 한글 자음/모음도 유지 (ㅋ, ㅎ 등 웃음 표현 보존)
        # 한글 자음: ㄱ-ㅎ (U+3131-U+314E), 모음: ㅏ-ㅣ (U+314F-U+3163)
        text = re.sub(r'[^\w\s가-힣\u3131-\u3163.,!?]', ' ', text)
        
        # 7. 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 8. 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    @classmethod
    def is_korean_dominant(cls, text: str, threshold: float = 0.5) -> bool:
        """
        한국어가 주된 언어인지 확인
        
        Args:
            text: 텍스트
            threshold: 한국어 비율 임계값
            
        Returns:
            한국어가 주된 언어인지 여부
        """
        if not text:
            return False
        
        korean_pattern = re.compile(r'[가-힣]')
        total_chars = len(re.findall(r'[가-힣a-zA-Z0-9]', text))
        
        if total_chars == 0:
            return False
        
        korean_chars = len(korean_pattern.findall(text))
        korean_ratio = korean_chars / total_chars
        
        return korean_ratio >= threshold
    
    @classmethod
    def get_text_statistics(cls, text: str) -> dict:
        """
        텍스트 통계 정보 반환
        
        Args:
            text: 텍스트
            
        Returns:
            텍스트 통계 딕셔너리
        """
        if not text:
            return {
                "length": 0,
                "emoji_count": 0,
                "url_count": 0,
                "korean_ratio": 0.0,
                "whitespace_ratio": 0.0
            }
        
        emoji_count = len(cls.EMOJI_PATTERN.findall(text))
        url_count = len(cls.URL_PATTERN.findall(text))
        
        korean_pattern = re.compile(r'[가-힣]')
        total_chars = len(re.findall(r'[가-힣a-zA-Z0-9]', text))
        korean_chars = len(korean_pattern.findall(text))
        korean_ratio = korean_chars / total_chars if total_chars > 0 else 0.0
        
        whitespace_ratio = text.count(' ') / len(text) if len(text) > 0 else 0.0
        
        return {
            "length": len(text),
            "emoji_count": emoji_count,
            "url_count": url_count,
            "korean_ratio": korean_ratio,
            "whitespace_ratio": whitespace_ratio
        }
    
    @staticmethod
    def filter_by_length(text: str, min_length: int = 10, max_length: int = 1000) -> bool:
        """
        텍스트 길이 필터링
        
        Args:
            text: 텍스트
            min_length: 최소 길이
            max_length: 최대 길이
            
        Returns:
            필터링 통과 여부
        """
        length = len(text)
        return min_length <= length <= max_length
    
    @staticmethod
    def detect_language(text: str) -> str:
        """
        언어 감지 (간단한 휴리스틱)
        
        Args:
            text: 텍스트
            
        Returns:
            언어 코드 ("ko", "en", "mixed")
        """
        korean_pattern = re.compile(r'[가-힣]')
        english_pattern = re.compile(r'[a-zA-Z]')
        
        korean_count = len(korean_pattern.findall(text))
        english_count = len(english_pattern.findall(text))
        
        if korean_count > english_count * 2:
            return "ko"
        elif english_count > korean_count * 2:
            return "en"
        else:
            return "mixed"
    
    @staticmethod
    def clean_batch(texts: List[str]) -> List[str]:
        """
        배치 텍스트 정제
        
        Args:
            texts: 텍스트 리스트
            
        Returns:
            정제된 텍스트 리스트
        """
        return [TextCleaner.clean_text(text) for text in texts]

