#!/usr/bin/env python3
"""
SQLite 데이터베이스 확인 스크립트
"""

import sqlite3
import os

def check_database():
    """데이터베이스 상태 확인"""
    db_path = "stock_app.db"
    
    # 데이터베이스 파일 존재 확인
    if not os.path.exists(db_path):
        print(f"❌ 데이터베이스 파일이 존재하지 않습니다: {db_path}")
        return
    
    print(f"✅ 데이터베이스 파일 발견: {db_path}")
    
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 테이블 목록:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # users 테이블이 있는지 확인
        if ('users',) in tables:
            print(f"\n👥 users 테이블 정보:")
            
            # 사용자 수 확인
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"  - 총 사용자 수: {user_count}명")
            
            if user_count > 0:
                # 사용자 목록 확인 (비밀번호는 제외)
                cursor.execute("SELECT id, username, email, created_at FROM users ORDER BY created_at DESC;")
                users = cursor.fetchall()
                
                print(f"\n📝 사용자 목록:")
                for user in users:
                    user_id, username, email, created_at = user
                    print(f"  - ID: {user_id}, 사용자명: {username}, 이메일: {email or '없음'}, 가입일: {created_at}")
        else:
            print(f"\n❌ users 테이블이 존재하지 않습니다.")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ 데이터베이스 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    check_database() 