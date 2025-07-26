#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import user
from app.core.security import get_password_hash

def init_database():
    """데이터베이스 초기화"""
    
    # 데이터베이스 URL
    database_url = "sqlite:///./stock_app.db"
    
    # 엔진 생성
    engine = create_engine(
        database_url, 
        connect_args={"check_same_thread": False}
    )
    
    try:
        # 테이블 생성
        print("🗄️ 데이터베이스 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        print("✅ 테이블 생성 완료!")
        
        # 세션 생성
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # 기본 관리자 계정 생성 (선택사항)
        try:
            from app.models.user import User
            
            # 관리자 계정이 이미 있는지 확인
            admin_user = db.query(User).filter(User.username == "admin").first()
            
            if not admin_user:
                print("👤 기본 관리자 계정 생성 중...")
                admin_user = User(
                    username="admin",
                    email="admin@example.com",
                    hashed_password=get_password_hash("admin123")
                )
                db.add(admin_user)
                db.commit()
                print("✅ 관리자 계정 생성 완료!")
                print("   - 사용자명: admin")
                print("   - 비밀번호: admin123")
            else:
                print("ℹ️ 관리자 계정이 이미 존재합니다.")
                
        except Exception as e:
            print(f"⚠️ 관리자 계정 생성 중 오류: {e}")
        
        db.close()
        
        print("\n🎉 데이터베이스 초기화 완료!")
        print("📁 데이터베이스 파일: stock_app.db")
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_database() 