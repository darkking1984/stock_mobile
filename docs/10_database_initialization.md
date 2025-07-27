# Render 백엔드 데이터베이스 초기화 가이드

## 1. Render Shell 접속

1. Render Dashboard에서 **"stock-backend"** 프로젝트 클릭
2. 왼쪽 사이드바에서 **"Shell"** 클릭
3. **"Connect"** 버튼 클릭하여 터미널 접속

## 2. 데이터베이스 초기화

### **기본 초기화**
```bash
python init_db.py
```

### **관리자 계정 생성**
```bash
python init_db.py --admin
```

## 3. 테스트 사용자 생성

### **수동으로 사용자 생성**
```bash
python
```

Python 인터프리터에서:
```python
from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

# 테스트 사용자 생성
test_user = User(
    username="testuser",
    email="test@example.com",
    hashed_password=get_password_hash("password123")
)

db.add(test_user)
db.commit()
db.close()

print("테스트 사용자 생성 완료!")
exit()
```

## 4. 데이터베이스 상태 확인

### **사용자 목록 확인**
```bash
python check_db.py
```

### **데이터베이스 파일 확인**
```bash
ls -la *.db
```

## 5. 문제 해결

### **SQLite 파일 권한 문제**
```bash
chmod 666 stock_app.db
```

### **데이터베이스 재생성**
```bash
rm stock_app.db
python init_db.py
```

## 6. 로그 확인

### **애플리케이션 로그**
```bash
tail -f /var/log/app.log
```

### **데이터베이스 연결 테스트**
```bash
python -c "from app.database import engine; print('DB 연결 성공!')"
``` 