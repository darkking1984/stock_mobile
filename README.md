# 📈 주식 대시보드 (Stock Dashboard)

실시간 주식 정보를 제공하는 웹 애플리케이션입니다.

## 🚀 기능

- **실시간 주식 데이터**: yfinance를 통한 실시간 주식 정보
- **인터랙티브 차트**: 다양한 차트 타입 지원 (캔들, 라인, 영역)
- **사용자 인증**: JWT 기반 로그인/회원가입 시스템
- **반응형 디자인**: 모바일 및 데스크톱 지원
- **캐싱 시스템**: 성능 최적화를 위한 데이터 캐싱

## 🛠️ 기술 스택

### Frontend
- **React 18** + TypeScript
- **Tailwind CSS** - 스타일링
- **Chart.js** - 차트 라이브러리
- **React Router** - 라우팅

### Backend
- **FastAPI** - Python 웹 프레임워크
- **SQLAlchemy** - ORM
- **SQLite** - 데이터베이스 (개발)
- **PostgreSQL** - 데이터베이스 (프로덕션)
- **JWT** - 인증
- **bcrypt** - 비밀번호 해싱

## 📦 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd stock
```

### 2. 백엔드 설정
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 데이터베이스 초기화
python init_db.py

# 서버 실행
python -m uvicorn app.main:app --reload
```

### 3. 프론트엔드 설정
```bash
cd frontend
npm install
npm start
```

## 🌐 배포

### Vercel 배포
1. GitHub 저장소에 코드 푸시
2. [Vercel](https://vercel.com)에서 프로젝트 연결
3. 환경 변수 설정
4. 자동 배포 완료

### 백엔드 배포 (Railway)
1. [Railway](https://railway.app)에서 프로젝트 생성
2. GitHub 저장소 연결
3. 환경 변수 설정
4. 자동 배포 완료

## 🔧 환경 변수

### Frontend (.env)
```
REACT_APP_API_BASE_URL=http://localhost:8000
```

### Backend (.env)
```
DATABASE_URL=sqlite:///./stock_app.db
SECRET_KEY=your-secret-key
```

## 📱 모바일 지원

- 반응형 디자인
- 터치 친화적 인터페이스
- 모바일 최적화된 차트

## 🔒 보안

- JWT 토큰 기반 인증
- bcrypt 비밀번호 해싱
- CORS 설정
- 입력 검증

## 📊 API 문서

FastAPI 자동 생성 문서:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 기여

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 개발자

© 2025 bori company 