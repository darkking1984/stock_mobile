from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import stock, auth
from app.database import engine, SessionLocal
from app.models import user
from app.core.security import get_password_hash
from datetime import datetime

# 데이터베이스 테이블 생성
user.Base.metadata.create_all(bind=engine)

# 테스트 사용자 자동 생성
def create_test_user():
    try:
        db = SessionLocal()
        
        # 기존 사용자 확인
        existing_user = db.query(user.User).filter(user.User.username == "coase").first()
        
        if not existing_user:
            # 테스트 사용자 생성
            test_user = user.User(
                username="coase",
                email="coase@example.com",
                hashed_password=get_password_hash("password123")
            )
            db.add(test_user)
            db.commit()
            print("✅ 테스트 사용자 생성 완료: coase / password123")
            print(f"✅ 사용자 ID: {test_user.id}")
        else:
            print("✅ 기존 사용자 존재: coase")
            print(f"✅ 사용자 ID: {existing_user.id}")
            
        # 모든 사용자 목록 출력
        all_users = db.query(user.User).all()
        print(f"✅ 총 사용자 수: {len(all_users)}")
        for u in all_users:
            print(f"   - {u.username} ({u.email})")
            
        db.close()
    except Exception as e:
        print(f"⚠️ 사용자 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()

# 애플리케이션 시작 시 테스트 사용자 생성
create_test_user()

app = FastAPI(
    title="Stock Dashboard API",
    description="미국 주식 정보 대시보드 API",
    version="1.0.0"
)

# CORS 설정 - Render 배포용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://stock-mobile.vercel.app",  # Vercel 프론트엔드 URL
        "https://stock-mobile-adxqa4s20-boris-projects-ee8b76c6.vercel.app",  # 이전 Vercel URL
        "https://stock-mobile-fpkad4kro-boris-projects-ee8b76c6.vercel.app",  # 현재 Vercel URL
        "https://*.vercel.app",  # Vercel 프리뷰 URL
        "https://*.onrender.com",  # Render 백엔드 URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 라우터 등록
app.include_router(auth.router, prefix="/api/v1", tags=["authentication"])
app.include_router(stock.router, prefix="/api/v1", tags=["stock"])

@app.get("/")
async def root():
    return {"message": "Stock Dashboard API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/v1/health")
async def api_health_check():
    return {"status": "healthy", "api_version": "1.0.0", "timestamp": datetime.utcnow().isoformat()} 