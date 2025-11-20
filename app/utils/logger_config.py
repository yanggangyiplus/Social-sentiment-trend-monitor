"""
로깅 설정 모듈
모듈별 로그 파일 분리 및 로깅 설정
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 로그 디렉토리 생성
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)


def setup_logger(name: str, log_file: str, level: int = logging.INFO) -> logging.Logger:
    """
    모듈별 로거 설정
    
    Args:
        name: 로거 이름
        log_file: 로그 파일명
        level: 로깅 레벨
    
    Returns:
        설정된 로거
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거 (중복 방지)
    logger.handlers = []
    
    # 파일 핸들러 (회전 로그)
    file_handler = RotatingFileHandler(
        LOG_DIR / log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # 콘솔에는 WARNING 이상만
    console_formatter = logging.Formatter(
        '%(levelname)s - %(name)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 모듈별 로거 생성
collector_logger = setup_logger('collector', 'collector.log')
sentiment_logger = setup_logger('sentiment', 'sentiment.log')
trend_logger = setup_logger('trend', 'trend.log')
app_logger = setup_logger('app', 'app.log')
youtube_logger = setup_logger('youtube', 'youtube.log')

