# 08. 배포 가이드 및 운영 문서

## 🚀 배포 아키텍처

### 전체 배포 구조
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Vercel)      │◄──►│   (Render)      │◄──►│   (PostgreSQL)  │
│                 │    │                 │    │                 │
│   - React App   │    │   - FastAPI     │    │   - User Data   │
│   - Static      │    │   - yfinance    │    │   - Cache       │
│   - CDN         │    │   - Redis       │    │   - Logs        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 환경별 배포 전략
- **Development**: 로컬 환경 (Docker Compose)
- **Staging**: Render (Preview Deployments)
- **Production**: Vercel + Render + PostgreSQL

## 📦 프론트엔드 배포 (Vercel)

### 1. Vercel 설정

#### 1.1 프로젝트 설정
```json
// frontend/vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ],
  "env": {
    "REACT_APP_API_URL": "@api-url"
  }
}
```

#### 1.2 환경 변수 설정
```bash
# Vercel CLI로 환경 변수 설정
vercel env add REACT_APP_API_URL production
vercel env add REACT_APP_API_URL preview
vercel env add REACT_APP_API_URL development
```

#### 1.3 빌드 최적화
```javascript
// frontend/package.json
{
  "scripts": {
    "build": "GENERATE_SOURCEMAP=false react-scripts build",
    "build:analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

### 2. 배포 프로세스

#### 2.1 자동 배포 설정
```yaml
# .github/workflows/deploy-frontend.yml
name: Deploy Frontend

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm test -- --coverage --watchAll=false
    
    - name: Build
      run: |
        cd frontend
        npm run build
      env:
        REACT_APP_API_URL: ${{ secrets.REACT_APP_API_URL }}
    
    - name: Deploy to Vercel
      uses: amondnet/vercel-action@v25
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
        working-directory: ./frontend
```

#### 2.2 수동 배포
```bash
# Vercel CLI 설치
npm install -g vercel

# 로그인
vercel login

# 프로젝트 초기화
cd frontend
vercel

# 프로덕션 배포
vercel --prod
```

## 🔧 백엔드 배포 (Render)

### 1. Render 설정

#### 1.1 서비스 설정
```yaml
# backend/render.yaml
services:
  - type: web
    name: stock-dashboard-api
    env: python
    plan: starter
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production
    healthCheckPath: /health
    autoDeploy: true
```

#### 1.2 Docker 배포 (선택사항)
```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

# 시스템 패키지 업데이트
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 1.3 환경 변수 설정
```bash
# Render 대시보드에서 설정
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://user:password@host:port
SECRET_KEY=your-secret-key-here
ENVIRONMENT=production
CORS_ORIGINS=https://your-domain.vercel.app
```

### 2. 데이터베이스 설정

#### 2.1 PostgreSQL 설정
```sql
-- 데이터베이스 생성
CREATE DATABASE stock_dashboard;

-- 사용자 생성
CREATE USER stock_user WITH PASSWORD 'secure_password';

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE stock_dashboard TO stock_user;

-- 확장 활성화
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### 2.2 마이그레이션 실행
```bash
# Alembic 마이그레이션
cd backend
alembic upgrade head

# 초기 데이터 삽입
python scripts/seed_data.py
```

### 3. Redis 설정

#### 3.1 Redis 클러스터 설정
```yaml
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

#### 3.2 Redis 연결 설정
```python
# backend/app/core/redis.py
import redis
from app.core.config import settings

redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30
)

# 연결 테스트
def test_redis_connection():
    try:
        redis_client.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False
```

## 🔒 보안 설정

### 1. SSL/TLS 설정

#### 1.1 Vercel SSL 설정
```json
// frontend/vercel.json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        }
      ]
    }
  ]
}
```

#### 1.2 FastAPI 보안 설정
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 신뢰할 수 있는 호스트 설정
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.vercel.app"]
)

# HTTPS 리다이렉트 (프로덕션에서만)
if settings.ENVIRONMENT == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 2. 환경 변수 보안

#### 2.1 민감한 정보 관리
```bash
# .env.production (절대 커밋하지 않음)
DATABASE_URL=postgresql://user:password@host:port/database
REDIS_URL=redis://user:password@host:port
SECRET_KEY=your-super-secret-key-here
API_KEYS={"yfinance": "your-api-key"}
```

#### 2.2 시크릿 관리
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Dict, Any
import json

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    API_KEYS: str = "{}"
    
    @property
    def api_keys(self) -> Dict[str, str]:
        return json.loads(self.API_KEYS)
    
    class Config:
        env_file = ".env"

settings = Settings()
```

## 📊 모니터링 및 로깅

### 1. 로깅 설정

#### 1.1 FastAPI 로깅
```python
# backend/app/core/logging.py
import logging
import sys
from loguru import logger
from app.core.config import settings

# 로그 설정
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO" if settings.ENVIRONMENT == "production" else "DEBUG"
)

# 파일 로깅 (프로덕션)
if settings.ENVIRONMENT == "production":
    logger.add(
        "logs/app.log",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )

# FastAPI 로거 설정
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )

logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
```

#### 1.2 API 로깅 미들웨어
```python
# backend/app/middleware/logging.py
import time
import json
from fastapi import Request, Response
from loguru import logger

async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 요청 로깅
    logger.info(f"Request: {request.method} {request.url}")
    
    # 요청 본문 로깅 (POST/PUT만)
    if request.method in ["POST", "PUT"]:
        try:
            body = await request.body()
            if body:
                logger.debug(f"Request body: {body.decode()}")
        except Exception as e:
            logger.warning(f"Failed to log request body: {e}")
    
    # 응답 처리
    response = await call_next(request)
    
    # 응답 시간 계산
    process_time = time.time() - start_time
    
    # 응답 로깅
    logger.info(
        f"Response: {response.status_code} - {process_time:.3f}s"
    )
    
    # 응답 헤더에 처리 시간 추가
    response.headers["X-Process-Time"] = str(process_time)
    
    return response
```

### 2. 헬스체크 엔드포인트

#### 2.1 헬스체크 구현
```python
# backend/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.redis import redis_client
import yfinance as yf

router = APIRouter()

@router.get("/health")
async def health_check():
    """기본 헬스체크"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """상세 헬스체크"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "checks": {}
    }
    
    # 데이터베이스 체크
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Redis 체크
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # yfinance API 체크
    try:
        ticker = yf.Ticker("AAPL")
        info = ticker.info
        if info:
            health_status["checks"]["yfinance"] = "healthy"
        else:
            health_status["checks"]["yfinance"] = "unhealthy: no data"
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["checks"]["yfinance"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status
```

### 3. 성능 모니터링

#### 3.1 메트릭 수집
```python
# backend/app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# 메트릭 정의
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

# 미들웨어에서 메트릭 수집
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    # 요청 수 증가
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    # 요청 시간 기록
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response
```

## 🔄 백업 및 복구

### 1. 데이터베이스 백업

#### 1.1 자동 백업 스크립트
```bash
#!/bin/bash
# scripts/backup.sh

# 환경 변수 설정
DB_URL="postgresql://user:password@host:port/database"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="stock_dashboard_$DATE.sql"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# PostgreSQL 백업
pg_dump $DB_URL > $BACKUP_DIR/$BACKUP_FILE

# 압축
gzip $BACKUP_DIR/$BACKUP_FILE

# 30일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

#### 1.2 백업 복구 스크립트
```bash
#!/bin/bash
# scripts/restore.sh

# 환경 변수 설정
DB_URL="postgresql://user:password@host:port/database"
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 백업 파일 확인
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# 복구 실행
gunzip -c $BACKUP_FILE | psql $DB_URL

echo "Restore completed from: $BACKUP_FILE"
```

### 2. Redis 백업

#### 2.1 Redis 백업 설정
```bash
# Redis 백업 스크립트
#!/bin/bash
# scripts/redis_backup.sh

REDIS_HOST="localhost"
REDIS_PORT="6379"
BACKUP_DIR="/backups/redis"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Redis 백업
redis-cli -h $REDIS_HOST -p $REDIS_PORT BGSAVE

# 백업 파일 복사
cp /var/lib/redis/dump.rdb $BACKUP_DIR/dump_$DATE.rdb

# 압축
gzip $BACKUP_DIR/dump_$DATE.rdb

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "dump_*.rdb.gz" -mtime +7 -delete

echo "Redis backup completed: dump_$DATE.rdb.gz"
```

## 🚨 장애 대응

### 1. 장애 감지 및 알림

#### 1.1 모니터링 스크립트
```python
# scripts/monitor.py
import requests
import smtplib
from email.mime.text import MIMEText
import time
from loguru import logger

class HealthMonitor:
    def __init__(self, endpoints, email_config):
        self.endpoints = endpoints
        self.email_config = email_config
    
    def check_endpoint(self, url):
        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed for {url}: {e}")
            return False
    
    def send_alert(self, message):
        try:
            msg = MIMEText(message)
            msg['Subject'] = 'Stock Dashboard Alert'
            msg['From'] = self.email_config['from']
            msg['To'] = self.email_config['to']
            
            with smtplib.SMTP(self.email_config['smtp_server']) as server:
                server.starttls()
                server.login(self.email_config['username'], self.email_config['password'])
                server.send_message(msg)
            
            logger.info("Alert email sent")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def run(self):
        while True:
            for name, url in self.endpoints.items():
                if not self.check_endpoint(url):
                    message = f"Health check failed for {name}: {url}"
                    self.send_alert(message)
            
            time.sleep(300)  # 5분마다 체크

if __name__ == "__main__":
    endpoints = {
        "API": "https://your-api.render.com/health",
        "Frontend": "https://your-app.vercel.app"
    }
    
    email_config = {
        "smtp_server": "smtp.gmail.com",
        "username": "your-email@gmail.com",
        "password": "your-app-password",
        "from": "your-email@gmail.com",
        "to": "admin@your-domain.com"
    }
    
    monitor = HealthMonitor(endpoints, email_config)
    monitor.run()
```

### 2. 자동 복구 스크립트

#### 2.1 서비스 재시작 스크립트
```bash
#!/bin/bash
# scripts/restart_service.sh

SERVICE_NAME="stock-dashboard-api"
MAX_RESTARTS=3
RESTART_COUNT=0

while [ $RESTART_COUNT -lt $MAX_RESTARTS ]; do
    # 서비스 상태 확인
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Service is healthy"
        exit 0
    else
        echo "Service is unhealthy, restarting..."
        RESTART_COUNT=$((RESTART_COUNT + 1))
        
        # 서비스 재시작
        systemctl restart $SERVICE_NAME
        
        # 재시작 대기
        sleep 30
        
        # 헬스체크 재시도
        for i in {1..10}; do
            if curl -f http://localhost:8000/health > /dev/null 2>&1; then
                echo "Service recovered after restart"
                exit 0
            fi
            sleep 10
        done
    fi
done

echo "Service failed to recover after $MAX_RESTARTS restarts"
exit 1
```

## 📈 성능 최적화

### 1. 캐싱 전략

#### 1.1 Redis 캐싱 구현
```python
# backend/app/services/cache_service.py
import redis
import json
import pickle
from typing import Any, Optional
from app.core.config import settings

class CacheService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        try:
            data = self.redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        """캐시에 데이터 저장"""
        try:
            data = pickle.dumps(value)
            self.redis.setex(key, ttl, data)
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def delete(self, key: str):
        """캐시에서 데이터 삭제"""
        try:
            self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
    
    def clear_pattern(self, pattern: str):
        """패턴에 맞는 캐시 삭제"""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}")
```

### 2. CDN 설정

#### 2.1 Vercel CDN 최적화
```json
// frontend/vercel.json
{
  "headers": [
    {
      "source": "/static/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=0, must-revalidate"
        }
      ]
    }
  ]
}
```

이제 실제 개발을 시작하겠습니다. 먼저 프로젝트 구조를 생성하고 기본 설정을 진행하겠습니다.
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
run_terminal_cmd