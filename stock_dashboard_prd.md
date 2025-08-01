# 📄 PRD: 미국 주식 정보 조회 웹앱 (yfinance 기반)

## ✅ 개요
미국 주식 정보를 실시간 또는 주기적으로 조회하고 시각화해주는 웹 기반 대시보드 앱을 개발한다. 데이터는 `yfinance` 라이브러리를 활용하며, React + Tailwind로 프론트엔드를 구성하고, Python(FastAPI)을 백엔드로 사용한다. 개발 소스는 GitHub를 통해 버전 관리되며, CI/CD 배포를 고려한다.

---

## 🎯 목표
- 미국 상장 기업의 실시간/과거 주가 정보, 재무정보, 배당정보 등을 사용자에게 시각적으로 제공
- 관심 종목 즐겨찾기 및 포트폴리오 트래킹 기능 제공
- 초기 MVP 단계에서는 티커 검색 → 주가 조회 및 차트 시각화를 중심으로 구현

---

## 🧑‍💼 사용자 페르소나

### 👩 페르소나 1: 초보 개인 투자자 김주식 (28세, 마케터)
- 투자 경험: 1년 미만
- 주요 관심사: 주가 확인, PER/배당 정보, 차트 확인
- 사용 목적: "직장에서 틈틈이 종목 검색하고 투자 정보 참고"
- 요구사항:
  - 모바일에서도 잘 보이는 UI
  - 차트와 수치 정보가 한눈에 들어오게
  - 알기 쉬운 설명/지표 간단 요약

### 👨 페르소나 2: 중급 투자자 이퀀트 (35세, 개발자)
- 투자 경험: 5년 이상, 장기투자 성향
- 주요 관심사: 재무제표, 배당, 멀티 종목 비교
- 사용 목적: "내 포트폴리오 관리에 참고하려고"
- 요구사항:
  - 여러 종목을 비교할 수 있는 기능
  - 최근 배당 이력 및 시세 변동 트렌드
  - 재무제표 연도별 비교표

---

## 📦 핵심 기능 (MVP 기준)

### 1. 티커 검색
- 티커 입력 시 yfinance에서 종목 정보 조회
- 자동완성 또는 기본 인기 티커 추천

### 2. 주가 및 차트 조회
- 현재가, 고가/저가, PER, 시가총액 표시
- 최근 1개월/1년 라인 차트 또는 캔들 차트 시각화 (Recharts 등 활용)

### 3. 재무정보 조회
- 연간 또는 분기 기준 매출, 영업이익, 순이익 등

### 4. 관심 종목 저장
- 간단한 즐겨찾기 기능 (로컬스토리지 또는 DB)
- 추후 로그인 기반 포트폴리오 기능 확장 예정

### 5. GitHub 기반 개발 환경 구성
- GitHub 저장소 구성 및 브랜치 전략 적용 (main/dev/feature)
- GitHub Actions를 통한 테스트 및 배포 자동화 고려

---
#uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

## 🧱 기술 스택
| 계층        | 기술               |
|------------|-------------------|
| 프론트엔드 | React, Tailwind CSS, Axios, Recharts |
| 백엔드     | Python, FastAPI, yfinance, uvicorn |
| DB         | SQLite (MVP용) / PostgreSQL (확장 시) |
| 배포       | Vercel (프론트), Render or Fly.io (백엔드) |
| 형상관리   | Git + GitHub (with Actions) |

---

## 🛣 개발 로드맵 (요약)

| 주차 | 작업 내용 |
|------|-----------|
| 1주차 | 프로젝트 구조 구성, GitHub repo 생성, 기본 페이지 UI 구성 |
| 2주차 | yfinance 연동 API 개발 및 티커 검색 기능 구현 |
| 3주차 | 주가 차트 및 데이터 시각화, 즐겨찾기 기능 구현 |
| 4주차 | 리팩토링 + GitHub Actions 설정 + 배포 + 테스트 |

---

## 🧪 테스트 계획 (요약)
- API 응답 테스트 (단위 테스트)
- 프론트엔드 기능 테스트 (React Testing Library)
- yfinance 호출 실패 대비 예외 처리

---

## 📌 기타 고려 사항
- yfinance는 실시간이 아닌 "지연 데이터"임 (최대 15분 지연)
- 대량 호출 제한이 있으므로 캐싱 또는 비동기 호출 처리 필요
- MVP 이후 사용자 인증, 포트폴리오 관리, 알림 기능 등 확장 가능

