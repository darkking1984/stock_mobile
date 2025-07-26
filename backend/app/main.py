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

# CORS 설정 - 모바일 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://192.168.0.15:3000",
        "http://127.0.0.1:3000",
        "https://your-domain.vercel.app",
        # 모바일 접근을 위한 추가 설정
        "http://192.168.0.15:3000",  # 특정 IP 명시
        "http://192.168.1.100:3000",  # 다른 가능한 IP
        "http://10.0.0.100:3000",     # 다른 가능한 IP
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # 헤더 노출 허용
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