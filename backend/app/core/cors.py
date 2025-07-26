from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List

def get_cors_middleware():
    """동적 CORS 미들웨어 생성"""
    
    def cors_middleware(app):
        @app.middleware("http")
        async def add_cors_header(request: Request, call_next):
            # 요청의 Origin 확인
            origin = request.headers.get("origin")
            
            # 허용할 Origin 목록
            allowed_origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://192.168.0.15:3000",
                "https://your-domain.vercel.app",
            ]
            
            # 개발 환경에서 추가 IP 허용
            if origin and origin.startswith("http://192.168."):
                allowed_origins.append(origin)
            elif origin and origin.startswith("http://10."):
                allowed_origins.append(origin)
            
            response = await call_next(request)
            
            # CORS 헤더 추가
            if origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
            
            return response
        
        return app
    
    return cors_middleware 