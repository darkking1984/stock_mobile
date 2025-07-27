# Render 백엔드 배포 가이드

## 1. Render 계정 생성

1. [Render.com](https://render.com) 접속
2. "Get Started" 클릭
3. GitHub 계정으로 로그인 (권장)

## 2. 새 Web Service 생성

1. Dashboard에서 "New +" 클릭
2. "Web Service" 선택
3. GitHub 저장소 연결:
   - "Connect a repository" 클릭
   - `stock_mobile` 저장소 선택
   - "Connect" 클릭

## 3. 서비스 설정

### 기본 설정
- **Name**: `stock-backend` (또는 원하는 이름)
- **Environment**: `Python 3`
- **Region**: `Oregon (US West)` (가장 빠름)
- **Branch**: `main`
- **Root Directory**: `backend` (중요!)

### 빌드 설정
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 환경 변수 설정
- **PYTHON_VERSION**: `3.11`
- **PORT**: `8000`

## 4. 고급 설정

### Auto-Deploy
- ✅ "Auto-Deploy" 활성화
- Branch: `main`

### Health Check Path
- **Health Check Path**: `/health`

## 5. 배포 실행

1. "Create Web Service" 클릭
2. 배포 진행 상황 모니터링
3. 배포 완료 후 URL 확인

## 6. 배포 후 설정

### 환경 변수 추가
배포 완료 후 "Environment" 탭에서 추가 설정:

```
DATABASE_URL=sqlite:///./stock_app.db
SECRET_KEY=your-secret-key-here
```

### 데이터베이스 초기화
배포 후 터미널에서:
```bash
python init_db.py
```

## 7. Vercel 프론트엔드 연결

### 환경 변수 업데이트
Vercel 프로젝트 설정에서:
```
REACT_APP_API_URL=https://your-render-app.onrender.com
```

## 8. 문제 해결

### 일반적인 오류
1. **Module not found**: requirements.txt 확인
2. **Port binding error**: `$PORT` 환경변수 사용 확인
3. **Database error**: SQLite 파일 경로 확인

### 로그 확인
- Render Dashboard → Logs 탭
- 실시간 로그 모니터링 가능

## 9. 비용

- **완전 무료** (월 750시간)
- 신용카드 등록 불필요
- 자동 스케일링 지원

## 10. 성능 최적화

### 캐싱 설정
```python
# app/main.py에 추가
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
```

### 데이터베이스 최적화
- SQLite 대신 PostgreSQL 고려 (무료 티어 제공)
- 연결 풀링 설정 