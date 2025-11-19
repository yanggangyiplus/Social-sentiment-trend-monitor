"""
데이터베이스 관리 모듈
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Optional
import os

from .models import Base, CollectedText, SentimentAnalysis, TrendAlert


class DatabaseManager:
    """
    데이터베이스 관리 클래스
    """
    
    def __init__(self, database_url: str):
        """
        데이터베이스 매니저 초기화
        
        Args:
            database_url: 데이터베이스 URL (예: "sqlite:///data/database/sentiment.db")
        """
        # SQLite의 경우 디렉토리 생성
        if database_url.startswith("sqlite"):
            db_path = database_url.replace("sqlite:///", "")
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # SQLite 연결 풀 설정
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            self.engine = create_engine(database_url, echo=False)
        
        # 세션 팩토리 생성
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 테이블 생성
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        데이터베이스 세션 반환
        
        Returns:
            Session: 데이터베이스 세션
        """
        return self.SessionLocal()
    
    def close(self):
        """
        데이터베이스 연결 종료
        """
        self.engine.dispose()


# 전역 데이터베이스 매니저 인스턴스
_db_manager: Optional[DatabaseManager] = None


def init_database(database_url: str):
    """
    데이터베이스 초기화
    
    Args:
        database_url: 데이터베이스 URL
    """
    global _db_manager
    _db_manager = DatabaseManager(database_url)


def get_db() -> Session:
    """
    데이터베이스 세션 반환 (의존성 주입용)
    
    Returns:
        Session: 데이터베이스 세션
    """
    if _db_manager is None:
        raise RuntimeError("데이터베이스가 초기화되지 않았습니다. init_database()를 먼저 호출하세요.")
    
    db = _db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

