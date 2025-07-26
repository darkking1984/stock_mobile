from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token
from fastapi import HTTPException, status
from datetime import timedelta

class AuthService:
    def __init__(self):
        pass

    def create_user(self, db: Session, user: UserCreate) -> User:
        """새 사용자 생성"""
        # 사용자명 중복 확인
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # 이메일 중복 확인 (이메일이 제공된 경우)
        if user.email:
            db_user = db.query(User).filter(User.email == user.email).first()
            if db_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)
        
        # 새 사용자 생성
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def authenticate_user(self, db: Session, username: str, password: str) -> User:
        """사용자 인증"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def login_user(self, db: Session, user_login: UserLogin):
        """사용자 로그인"""
        user = self.authenticate_user(db, user_login.username, user_login.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }

    def get_user_by_username(self, db: Session, username: str) -> User:
        """사용자명으로 사용자 조회"""
        return db.query(User).filter(User.username == username).first() 