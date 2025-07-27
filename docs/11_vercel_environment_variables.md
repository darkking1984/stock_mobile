# Vercel 환경변수 설정 가이드

## 1. Vercel Dashboard 접속

1. [vercel.com](https://vercel.com) 접속
2. 로그인 후 Dashboard로 이동
3. **`stock_mobile`** 프로젝트 클릭

## 2. 프로젝트 설정

### **Settings 탭으로 이동**
1. 프로젝트 페이지에서 **"Settings"** 탭 클릭
2. 왼쪽 사이드바에서 **"Environment Variables"** 클릭

## 3. 환경변수 추가

### **새 환경변수 추가**
1. **"Add New"** 버튼 클릭
2. 다음 정보 입력:

```
Name: REACT_APP_API_URL
Value: https://stock-backend-6e1s.onrender.com
Environment: Production, Preview, Development (모두 체크)
```

### **환경변수 설정**
- **Name**: `REACT_APP_API_URL`
- **Value**: `https://stock-backend-6e1s.onrender.com`
- **Environment**: 
  - ✅ **Production** (체크)
  - ✅ **Preview** (체크)
  - ✅ **Development** (체크)

## 4. 저장 및 재배포

1. **"Save"** 버튼 클릭
2. **"Redeploy"** 버튼 클릭 (자동으로 나타남)
3. 재배포 완료 대기

## 5. 확인 방법

### **재배포 완료 후 Console 확인**
```
=== API Configuration ===
NODE_ENV: production
REACT_APP_API_URL: https://stock-backend-6e1s.onrender.com
API Base URL: https://stock-backend-6e1s.onrender.com
========================
```

### **로그인 테스트**
- 아이디: `coase`
- 비밀번호: `password123`

## 6. 문제 해결

### **환경변수가 적용되지 않는 경우**
1. **"Redeploy"** 버튼 클릭
2. **"Deployments"** 탭에서 배포 상태 확인
3. **"Ready"** 상태가 될 때까지 대기

### **여전히 오류가 발생하는 경우**
1. **"Settings"** → **"General"** → **"Build & Development Settings"**
2. **"Environment Variables"** 섹션에서 변수 확인
3. 필요시 **"Redeploy"** 클릭

## 7. 예상 결과

환경변수 설정 완료 후:
- ✅ API Base URL이 올바른 Render URL로 설정됨
- ✅ 로그인 요청이 Render 백엔드로 전송됨
- ✅ `405 Method Not Allowed` 오류 해결
- ✅ 로그인 기능 정상 작동 