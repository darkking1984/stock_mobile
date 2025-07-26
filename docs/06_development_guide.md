# 06. 개발 가이드 및 구현 단계

## 🚀 개발 환경 설정

### 필수 요구사항
- **Node.js**: 18.x 이상
- **Python**: 3.9 이상
- **Git**: 최신 버전
- **Docker**: (선택사항) 컨테이너화 개발

### 초기 설정
```bash
# 1. 프로젝트 클론
git clone <repository-url>
cd stock

# 2. 프론트엔드 설정
cd frontend
npm install

# 3. 백엔드 설정
cd ../backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일 편집
```

## 📋 구현 단계별 가이드

### Phase 1: 프로젝트 구조 및 기본 설정 (1주차)

#### 1.1 프로젝트 초기화
```bash
# 프로젝트 구조 생성
mkdir -p frontend backend docs
mkdir -p frontend/src/{components,pages,hooks,services,utils,types,styles}
mkdir -p backend/app/{api,models,services,utils}
mkdir -p backend/tests
```

#### 1.2 프론트엔드 초기 설정
```bash
cd frontend
npx create-react-app . --template typescript
npm install @types/node @types/react @types/react-dom
npm install tailwindcss @tailwindcss/forms @tailwindcss/typography
npm install recharts axios react-query react-router-dom
npm install -D @types/jest @testing-library/react @testing-library/jest-dom
```

#### 1.3 백엔드 초기 설정
```bash
cd ../backend
pip install fastapi uvicorn sqlalchemy alembic
pip install yfinance pandas numpy redis
pip install pytest pytest-asyncio httpx
pip install python-multipart python-jose[cryptography] passlib[bcrypt]
```

#### 1.4 기본 설정 파일 생성
```python
# backend/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
yfinance==0.2.18
pandas==2.1.3
numpy==1.25.2
redis==5.0.1
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
```

### Phase 2: 백엔드 API 개발 (2주차)

#### 2.1 데이터베이스 모델 구현
```python
# backend/app/models/base.py
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

#### 2.2 yfinance 서비스 구현
```python
# backend/app/services/stock_service.py
import yfinance as yf
from typing import Optional, Dict, Any
import pandas as pd

class StockService:
    def __init__(self):
        self.cache = {}
    
    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """주식 기본 정보 조회"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "currentPrice": info.get("currentPrice", 0),
                "previousClose": info.get("previousClose", 0),
                "change": info.get("currentPrice", 0) - info.get("previousClose", 0),
                "changePercent": ((info.get("currentPrice", 0) - info.get("previousClose", 0)) / info.get("previousClose", 1)) * 100,
                "high": info.get("dayHigh", 0),
                "low": info.get("dayLow", 0),
                "volume": info.get("volume", 0),
                "marketCap": info.get("marketCap", 0),
                "pe": info.get("trailingPE", 0),
                "dividendYield": info.get("dividendYield", 0),
                "beta": info.get("beta", 0),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh", 0),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow", 0),
                "avgVolume": info.get("averageVolume", 0),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", "")
            }
        except Exception as e:
            raise ValueError(f"Failed to fetch stock info for {symbol}: {str(e)}")
    
    async def get_stock_chart(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """주식 차트 데이터 조회"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            data = []
            for index, row in hist.iterrows():
                data.append({
                    "timestamp": index.isoformat(),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
            
            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data
            }
        except Exception as e:
            raise ValueError(f"Failed to fetch chart data for {symbol}: {str(e)}")
```

#### 2.3 API 라우터 구현
```python
# backend/app/api/stock.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from ..services.stock_service import StockService

router = APIRouter(prefix="/stock", tags=["stock"])
stock_service = StockService()

@router.get("/{symbol}/info")
async def get_stock_info(symbol: str):
    """주식 기본 정보 조회"""
    try:
        data = await stock_service.get_stock_info(symbol.upper())
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{symbol}/chart")
async def get_stock_chart(
    symbol: str,
    period: str = Query("1y", description="Chart period"),
    interval: str = Query("1d", description="Chart interval")
):
    """주식 차트 데이터 조회"""
    try:
        data = await stock_service.get_stock_chart(symbol.upper(), period, interval)
        return {"success": True, "data": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### 2.4 메인 앱 설정
```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import stock

app = FastAPI(
    title="Stock Dashboard API",
    description="미국 주식 정보 조회 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(stock.router)

@app.get("/")
async def root():
    return {"message": "Stock Dashboard API"}
```

### Phase 3: 프론트엔드 컴포넌트 개발 (3주차)

#### 3.1 기본 컴포넌트 구현
```typescript
// frontend/src/components/common/Button.tsx
import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled = false,
  onClick,
  className = ''
}) => {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  };
  
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;
  
  return (
    <button
      className={classes}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  );
};

export default Button;
```

#### 3.2 API 서비스 구현
```typescript
// frontend/src/services/api.ts
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    // 로딩 상태 관리
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 에러 처리
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default api;
```

#### 3.3 주식 서비스 구현
```typescript
// frontend/src/services/stockService.ts
import api from './api';

export interface StockInfo {
  symbol: string;
  name: string;
  currentPrice: number;
  previousClose: number;
  change: number;
  changePercent: number;
  high: number;
  low: number;
  volume: number;
  marketCap: number;
  pe: number;
  dividendYield: number;
  beta: number;
  fiftyTwoWeekHigh: number;
  fiftyTwoWeekLow: number;
  avgVolume: number;
  currency: string;
  exchange: string;
  sector: string;
  industry: string;
}

export interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const stockService = {
  async getStockInfo(symbol: string): Promise<StockInfo> {
    const response = await api.get(`/stock/${symbol}/info`);
    return response.data.data;
  },
  
  async getStockChart(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<{ data: ChartData[] }> {
    const response = await api.get(`/stock/${symbol}/chart`, {
      params: { period, interval }
    });
    return response.data.data;
  },
  
  async searchStocks(query: string): Promise<any[]> {
    // 검색 기능 구현 (향후 확장)
    return [];
  }
};
```

#### 3.4 커스텀 훅 구현
```typescript
// frontend/src/hooks/useStock.ts
import { useState, useEffect } from 'react';
import { stockService, StockInfo } from '../services/stockService';

export const useStock = (symbol: string) => {
  const [data, setData] = useState<StockInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStock = async () => {
      if (!symbol) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const stockData = await stockService.getStockInfo(symbol);
        setData(stockData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch stock data');
      } finally {
        setLoading(false);
      }
    };

    fetchStock();
  }, [symbol]);

  return { data, loading, error };
};
```

### Phase 4: 차트 및 시각화 구현 (4주차)

#### 4.1 차트 컴포넌트 구현
```typescript
// frontend/src/components/charts/StockChart.tsx
import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Bar } from 'recharts';
import { stockService, ChartData } from '../../services/stockService';

interface StockChartProps {
  symbol: string;
  period?: string;
  interval?: string;
  height?: number;
}

const StockChart: React.FC<StockChartProps> = ({
  symbol,
  period = '1y',
  interval = '1d',
  height = 400
}) => {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChartData = async () => {
      if (!symbol) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const chartData = await stockService.getStockChart(symbol, period, interval);
        setData(chartData.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch chart data');
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [symbol, period, interval]);

  if (loading) {
    return <div className="flex items-center justify-center h-96">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  const chartData = data.map(item => ({
    ...item,
    date: new Date(item.timestamp).toLocaleDateString(),
    price: item.close
  }));

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <h3 className="text-lg font-semibold mb-4">{symbol} Chart</h3>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={['dataMin - 1', 'dataMax + 1']} />
          <Tooltip />
          <Line type="monotone" dataKey="price" stroke="#3B82F6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;
```

#### 4.2 메인 페이지 구현
```typescript
// frontend/src/pages/HomePage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import StockSearch from '../components/stock/StockSearch';
import StockChart from '../components/charts/StockChart';

const HomePage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const navigate = useNavigate();

  const handleStockSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  const handleStockClick = (symbol: string) => {
    navigate(`/stock/${symbol}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            미국 주식 정보 대시보드
          </h1>
          
          <div className="mb-8">
            <StockSearch
              onSearch={() => {}}
              onSelect={handleStockSelect}
              placeholder="종목명 또는 티커 검색..."
            />
          </div>
          
          {selectedSymbol && (
            <div className="mb-8">
              <StockChart symbol={selectedSymbol} />
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 인기 종목 카드들 */}
            {['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META'].map((symbol) => (
              <div
                key={symbol}
                className="bg-white rounded-lg shadow-sm border p-4 cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => handleStockClick(symbol)}
              >
                <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
                <p className="text-sm text-gray-600">Click to view details</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
```

## 🧪 테스트 구현

### 백엔드 테스트
```python
# backend/tests/test_stock_service.py
import pytest
from app.services.stock_service import StockService

@pytest.fixture
def stock_service():
    return StockService()

@pytest.mark.asyncio
async def test_get_stock_info(stock_service):
    """주식 정보 조회 테스트"""
    result = await stock_service.get_stock_info("AAPL")
    
    assert result["symbol"] == "AAPL"
    assert "name" in result
    assert "currentPrice" in result
    assert result["currentPrice"] > 0

@pytest.mark.asyncio
async def test_get_stock_chart(stock_service):
    """주식 차트 데이터 조회 테스트"""
    result = await stock_service.get_stock_chart("AAPL", "1mo", "1d")
    
    assert result["symbol"] == "AAPL"
    assert "data" in result
    assert len(result["data"]) > 0
    assert "timestamp" in result["data"][0]
    assert "close" in result["data"][0]
```

### 프론트엔드 테스트
```typescript
// frontend/src/components/__tests__/StockChart.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import StockChart from '../charts/StockChart';

// Mock the stock service
jest.mock('../../services/stockService', () => ({
  stockService: {
    getStockChart: jest.fn()
  }
}));

describe('StockChart', () => {
  it('renders loading state initially', () => {
    render(<StockChart symbol="AAPL" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders chart when data is loaded', async () => {
    const mockData = [
      {
        timestamp: '2023-01-01',
        open: 100,
        high: 105,
        low: 98,
        close: 102,
        volume: 1000000
      }
    ];

    // Mock the service response
    const { stockService } = require('../../services/stockService');
    stockService.getStockChart.mockResolvedValue({ data: mockData });

    render(<StockChart symbol="AAPL" />);
    
    // Wait for the chart to load
    await screen.findByText('AAPL Chart');
    expect(screen.getByText('AAPL Chart')).toBeInTheDocument();
  });
});
```

## 🚀 배포 가이드

### 프론트엔드 배포 (Vercel)
```bash
# 1. Vercel CLI 설치
npm install -g vercel

# 2. 프로젝트 빌드
cd frontend
npm run build

# 3. Vercel 배포
vercel --prod
```

### 백엔드 배포 (Render)
```bash
# 1. requirements.txt 확인
cd backend
pip freeze > requirements.txt

# 2. Dockerfile 생성
cat > Dockerfile << EOF
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 3. Render에 배포 (웹 대시보드 사용)
```

## 🔧 개발 팁

### 성능 최적화
1. **React.memo 사용**: 불필요한 리렌더링 방지
2. **useMemo/useCallback**: 계산 결과 메모이제이션
3. **코드 스플리팅**: 라우트별 번들 분리
4. **이미지 최적화**: WebP 포맷 사용

### 디버깅 팁
1. **React DevTools**: 컴포넌트 상태 확인
2. **Redux DevTools**: 상태 관리 디버깅
3. **Network 탭**: API 요청/응답 확인
4. **Console 로그**: 에러 추적

### 코드 품질
1. **ESLint**: 코드 스타일 통일
2. **Prettier**: 코드 포맷팅
3. **TypeScript**: 타입 안정성
4. **Jest**: 단위 테스트
5. **Cypress**: E2E 테스트 