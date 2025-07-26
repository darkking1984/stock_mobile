# 02. API 설계 및 엔드포인트 정의

## 🎯 API 설계 원칙

### RESTful API 설계
- HTTP 메서드의 의미에 맞는 사용
- 리소스 중심의 URL 설계
- 일관된 응답 형식
- 적절한 HTTP 상태 코드 사용

### 성능 최적화
- 캐싱 전략 적용
- 페이지네이션 구현
- 압축 응답 지원
- Rate Limiting 적용

## 📋 API 엔드포인트 정의

### Base URL
```
https://api.stock-dashboard.com/v1
```

### 1. 주식 검색 API

#### 1.1 티커 검색
```http
GET /search/ticker?q={query}&limit={limit}
```

**Request Parameters:**
- `q` (string, required): 검색할 티커 또는 회사명
- `limit` (integer, optional): 결과 개수 (기본값: 10)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "exchange": "NASDAQ",
      "type": "Common Stock",
      "country": "US"
    }
  ],
  "total": 1
}
```

#### 1.2 인기 티커 목록
```http
GET /search/popular
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "change": 2.5,
      "changePercent": 1.2
    }
  ]
}
```

### 2. 주식 정보 API

#### 2.1 기본 주식 정보
```http
GET /stock/{symbol}/info
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "currentPrice": 150.25,
    "previousClose": 148.75,
    "change": 1.50,
    "changePercent": 1.01,
    "high": 152.00,
    "low": 147.50,
    "volume": 45678900,
    "marketCap": 2400000000000,
    "pe": 25.5,
    "dividendYield": 0.65,
    "beta": 1.2,
    "fiftyTwoWeekHigh": 182.94,
    "fiftyTwoWeekLow": 124.17,
    "avgVolume": 52345678,
    "currency": "USD",
    "exchange": "NASDAQ",
    "sector": "Technology",
    "industry": "Consumer Electronics"
  }
}
```

#### 2.2 주가 차트 데이터
```http
GET /stock/{symbol}/chart?period={period}&interval={interval}
```

**Request Parameters:**
- `period` (string, optional): 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
- `interval` (string, optional): 간격 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "period": "1y",
    "interval": "1d",
    "timestamps": ["2023-01-01T00:00:00Z", "2023-01-02T00:00:00Z"],
    "prices": [
      {
        "timestamp": "2023-01-01T00:00:00Z",
        "open": 148.50,
        "high": 150.25,
        "low": 147.80,
        "close": 149.75,
        "volume": 45678900
      }
    ]
  }
}
```

#### 2.3 기술적 지표
```http
GET /stock/{symbol}/indicators?period={period}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "period": "1y",
    "indicators": {
      "sma": {
        "20": [150.25, 149.80],
        "50": [148.50, 147.90],
        "200": [145.20, 144.80]
      },
      "ema": {
        "12": [151.20, 150.90],
        "26": [149.80, 149.40]
      },
      "rsi": [65.5, 62.3],
      "macd": {
        "macd": [2.5, 2.1],
        "signal": [1.8, 1.6],
        "histogram": [0.7, 0.5]
      },
      "bollinger": {
        "upper": [155.20, 154.80],
        "middle": [150.25, 149.80],
        "lower": [145.30, 144.80]
      }
    }
  }
}
```

### 3. 재무 정보 API

#### 3.1 재무제표 요약
```http
GET /stock/{symbol}/financials?type={type}&period={period}
```

**Request Parameters:**
- `type` (string, optional): 재무제표 유형 (income, balance, cashflow)
- `period` (string, optional): 기간 (annual, quarterly)

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "type": "income",
    "period": "annual",
    "statements": [
      {
        "date": "2023-09-30",
        "totalRevenue": 394328000000,
        "grossProfit": 170782000000,
        "operatingIncome": 114301000000,
        "netIncome": 96995000000,
        "ebitda": 130000000000,
        "ebit": 114301000000
      }
    ]
  }
}
```

#### 3.2 재무 비율
```http
GET /stock/{symbol}/ratios
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "ratios": {
      "valuation": {
        "pe": 25.5,
        "forwardPE": 24.2,
        "peg": 1.8,
        "priceToBook": 12.5,
        "priceToSales": 6.8,
        "enterpriseValue": 2500000000000
      },
      "profitability": {
        "grossMargin": 43.3,
        "operatingMargin": 29.0,
        "netMargin": 24.6,
        "roe": 147.9,
        "roa": 19.2,
        "roic": 162.5
      },
      "liquidity": {
        "currentRatio": 1.1,
        "quickRatio": 0.9,
        "cashRatio": 0.3
      },
      "efficiency": {
        "assetTurnover": 0.8,
        "inventoryTurnover": 37.2,
        "receivablesTurnover": 15.6
      }
    }
  }
}
```

### 4. 배당 정보 API

#### 4.1 배당 정보
```http
GET /stock/{symbol}/dividends
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "AAPL",
    "dividendYield": 0.65,
    "dividendRate": 0.96,
    "payoutRatio": 15.8,
    "exDividendDate": "2023-11-10",
    "paymentDate": "2023-11-16",
    "history": [
      {
        "date": "2023-11-16",
        "amount": 0.24,
        "type": "Regular"
      }
    ]
  }
}
```

### 5. 포트폴리오 API

#### 5.1 즐겨찾기 목록
```http
GET /portfolio/favorites
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "currentPrice": 150.25,
      "change": 1.50,
      "changePercent": 1.01,
      "addedAt": "2023-12-01T10:00:00Z"
    }
  ]
}
```

#### 5.2 즐겨찾기 추가/제거
```http
POST /portfolio/favorites
DELETE /portfolio/favorites/{symbol}
```

**Request Body (POST):**
```json
{
  "symbol": "AAPL"
}
```

### 6. 비교 분석 API

#### 6.1 종목 비교
```http
POST /compare/stocks
```

**Request Body:**
```json
{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "metrics": ["price", "pe", "dividendYield", "marketCap"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "comparison": [
      {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "currentPrice": 150.25,
        "pe": 25.5,
        "dividendYield": 0.65,
        "marketCap": 2400000000000
      }
    ]
  }
}
```

## 🔧 공통 응답 형식

### 성공 응답
```json
{
  "success": true,
  "data": {},
  "message": "Success",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

### 에러 응답
```json
{
  "success": false,
  "error": {
    "code": "INVALID_SYMBOL",
    "message": "Invalid stock symbol provided",
    "details": {}
  },
  "timestamp": "2023-12-01T10:00:00Z"
}
```

## 📊 HTTP 상태 코드

| 코드 | 의미 | 사용 사례 |
|------|------|-----------|
| 200 | OK | 성공적인 요청 |
| 201 | Created | 리소스 생성 성공 |
| 400 | Bad Request | 잘못된 요청 파라미터 |
| 401 | Unauthorized | 인증 필요 |
| 404 | Not Found | 리소스를 찾을 수 없음 |
| 429 | Too Many Requests | Rate limit 초과 |
| 500 | Internal Server Error | 서버 내부 오류 |

## 🚀 성능 최적화

### 캐싱 전략
- **Redis**: 자주 조회되는 데이터 캐싱 (TTL: 15분)
- **HTTP Cache**: ETag 및 Last-Modified 헤더 활용
- **CDN**: 정적 리소스 캐싱

### Rate Limiting
- **IP 기반**: 분당 100회 요청
- **API Key 기반**: 분당 1000회 요청
- **Burst 허용**: 짧은 시간 내 추가 요청 허용

### 압축
- **Gzip**: 모든 응답 압축
- **Brotli**: 지원하는 클라이언트에 대해 우선 적용 