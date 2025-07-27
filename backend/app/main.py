from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import stock, auth
from app.database import engine
from app.models import user
from datetime import datetime

# 데이터베이스 테이블 생성
user.Base.metadata.create_all(bind=engine)

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
        "https://stock-mobile-adxqa4s20-boris-projects-ee8b76c6.vercel.app",  # 현재 Vercel URL
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