#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 스크립트
기존 데이터베이스에 새로운 컬럼 추가
"""
import sqlite3
from pathlib import Path
import sys

# 프로젝트 루트를 경로에 추가
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = PROJECT_ROOT / "data" / "database" / "sentiment.db"


def migrate_database():
    """데이터베이스 마이그레이션 실행"""
    if not DB_PATH.exists():
        print(f"데이터베이스 파일이 없습니다: {DB_PATH}")
        print("데이터베이스를 초기화합니다...")
        from src.database.db_manager import init_database
        init_database(f"sqlite:///{DB_PATH}")
        print("✅ 데이터베이스 초기화 완료")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 기존 컬럼 확인
        cursor.execute("PRAGMA table_info(collected_texts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"기존 컬럼: {columns}")
        
        # 새 컬럼 추가
        new_columns = {
            "video_id": "VARCHAR(50)",
            "video_title": "VARCHAR(500)",
            "channel_name": "VARCHAR(200)",
            "view_count": "INTEGER",
            "like_count": "INTEGER"
        }
        
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE collected_texts ADD COLUMN {col_name} {col_type}")
                    print(f"✅ 컬럼 추가: {col_name}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ 컬럼 {col_name} 추가 실패 (이미 존재할 수 있음): {e}")
            else:
                print(f"ℹ️ 컬럼 {col_name} 이미 존재")
        
        # 인덱스 추가
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON collected_texts(video_id)")
            print("✅ 인덱스 추가: idx_video_id")
        except sqlite3.OperationalError as e:
            print(f"⚠️ 인덱스 추가 실패: {e}")
        
        conn.commit()
        print("\n✅ 데이터베이스 마이그레이션 완료")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 마이그레이션 실패: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_database()

