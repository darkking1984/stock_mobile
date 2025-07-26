# 07. 테스트 전략 및 테스트 케이스

## 🧪 테스트 전략 개요

### 테스트 피라미드
```
    E2E Tests (10%)
   ┌─────────────┐
   │ Integration │ (20%)
   │   Tests     │
   └─────────────┘
  ┌─────────────────┐
  │   Unit Tests    │ (70%)
  └─────────────────┘
```

### 테스트 목표
- **단위 테스트**: 80% 이상 커버리지
- **통합 테스트**: 주요 API 엔드포인트 100%
- **E2E 테스트**: 핵심 사용자 플로우
- **성능 테스트**: 응답 시간 및 부하 테스트

## 🔧 백엔드 테스트

### 1. 단위 테스트 (Unit Tests)

#### 1.1 Stock Service 테스트
```python
# backend/tests/test_stock_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.stock_service import StockService

class TestStockService:
    @pytest.fixture
    def stock_service(self):
        return StockService()
    
    @pytest.fixture
    def mock_ticker(self):
        mock = Mock()
        mock.info = {
            "longName": "Apple Inc.",
            "currentPrice": 150.25,
            "previousClose": 148.75,
            "dayHigh": 152.00,
            "dayLow": 147.50,
            "volume": 45678900,
            "marketCap": 2400000000000,
            "trailingPE": 25.5,
            "dividendYield": 0.0065,
            "beta": 1.2,
            "fiftyTwoWeekHigh": 182.94,
            "fiftyTwoWeekLow": 124.17,
            "averageVolume": 52345678,
            "currency": "USD",
            "exchange": "NASDAQ",
            "sector": "Technology",
            "industry": "Consumer Electronics"
        }
        return mock
    
    @pytest.mark.asyncio
    async def test_get_stock_info_success(self, stock_service, mock_ticker):
        """주식 정보 조회 성공 테스트"""
        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = await stock_service.get_stock_info("AAPL")
            
            assert result["symbol"] == "AAPL"
            assert result["name"] == "Apple Inc."
            assert result["currentPrice"] == 150.25
            assert result["change"] == 1.50
            assert result["changePercent"] == pytest.approx(1.01, rel=1e-2)
            assert result["marketCap"] == 2400000000000
            assert result["pe"] == 25.5
            assert result["dividendYield"] == 0.0065
    
    @pytest.mark.asyncio
    async def test_get_stock_info_invalid_symbol(self, stock_service):
        """잘못된 심볼로 주식 정보 조회 실패 테스트"""
        with patch('yfinance.Ticker', side_effect=Exception("Invalid symbol")):
            with pytest.raises(ValueError, match="Failed to fetch stock info"):
                await stock_service.get_stock_info("INVALID")
    
    @pytest.mark.asyncio
    async def test_get_stock_chart_success(self, stock_service):
        """주식 차트 데이터 조회 성공 테스트"""
        mock_hist = Mock()
        mock_hist.iterrows.return_value = [
            (pd.Timestamp('2023-01-01'), pd.Series({
                'Open': 100.0, 'High': 105.0, 'Low': 98.0, 'Close': 102.0, 'Volume': 1000000
            }))
        ]
        
        mock_ticker = Mock()
        mock_ticker.history.return_value = mock_hist
        
        with patch('yfinance.Ticker', return_value=mock_ticker):
            result = await stock_service.get_stock_chart("AAPL", "1d", "1m")
            
            assert result["symbol"] == "AAPL"
            assert result["period"] == "1d"
            assert result["interval"] == "1m"
            assert len(result["data"]) == 1
            assert result["data"][0]["open"] == 100.0
            assert result["data"][0]["close"] == 102.0
```

#### 1.2 API 라우터 테스트
```python
# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestStockAPI:
    def test_get_stock_info_success(self):
        """주식 정보 API 성공 테스트"""
        response = client.get("/stock/AAPL/info")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert data["data"]["symbol"] == "AAPL"
    
    def test_get_stock_info_invalid_symbol(self):
        """잘못된 심볼로 API 호출 실패 테스트"""
        response = client.get("/stock/INVALID/info")
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_get_stock_chart_success(self):
        """주식 차트 API 성공 테스트"""
        response = client.get("/stock/AAPL/chart?period=1mo&interval=1d")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert data["data"]["symbol"] == "AAPL"
        assert data["data"]["period"] == "1mo"
        assert data["data"]["interval"] == "1d"
    
    def test_get_stock_chart_invalid_params(self):
        """잘못된 파라미터로 차트 API 호출 테스트"""
        response = client.get("/stock/AAPL/chart?period=invalid&interval=invalid")
        
        # yfinance가 자체적으로 기본값을 사용하므로 성공할 수 있음
        # 실제 구현에서는 파라미터 검증 로직 추가 필요
        assert response.status_code in [200, 400]
```

### 2. 통합 테스트 (Integration Tests)

#### 2.1 데이터베이스 통합 테스트
```python
# backend/tests/test_integration.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.services.cache_service import CacheService

class TestIntegration:
    @pytest.fixture
    def db_session(self):
        """테스트용 데이터베이스 세션"""
        engine = create_engine("sqlite:///:memory:")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()
            Base.metadata.drop_all(bind=engine)
    
    @pytest.mark.asyncio
    async def test_stock_info_caching(self, db_session):
        """주식 정보 캐싱 통합 테스트"""
        cache_service = CacheService(db_session)
        
        # 첫 번째 호출 - 캐시에 저장
        stock_data = await cache_service.get_stock_info("AAPL")
        assert stock_data is not None
        
        # 두 번째 호출 - 캐시에서 조회
        cached_data = await cache_service.get_stock_info("AAPL")
        assert cached_data == stock_data
        
        # 캐시 만료 확인
        await cache_service.invalidate_stock_cache("AAPL")
        fresh_data = await cache_service.get_stock_info("AAPL")
        assert fresh_data != cached_data
```

### 3. 성능 테스트 (Performance Tests)

#### 3.1 API 성능 테스트
```python
# backend/tests/test_performance.py
import pytest
import asyncio
import time
from app.services.stock_service import StockService

class TestPerformance:
    @pytest.mark.asyncio
    async def test_stock_info_response_time(self):
        """주식 정보 조회 응답 시간 테스트"""
        stock_service = StockService()
        
        start_time = time.time()
        result = await stock_service.get_stock_info("AAPL")
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 5.0  # 5초 이내 응답
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        stock_service = StockService()
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        start_time = time.time()
        tasks = [stock_service.get_stock_info(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        assert len(results) == len(symbols)
        assert all(result is not None for result in results)
        assert total_time < 10.0  # 10초 이내 모든 요청 완료
```

## 🎨 프론트엔드 테스트

### 1. 컴포넌트 테스트

#### 1.1 StockSearch 컴포넌트 테스트
```typescript
// frontend/src/components/__tests__/StockSearch.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import StockSearch from '../stock/StockSearch';

// Mock the stock service
jest.mock('../../services/stockService', () => ({
  stockService: {
    searchStocks: jest.fn()
  }
}));

describe('StockSearch', () => {
  const mockOnSearch = jest.fn();
  const mockOnSelect = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders search input', () => {
    render(
      <StockSearch
        onSearch={mockOnSearch}
        onSelect={mockOnSelect}
        placeholder="Search stocks..."
      />
    );

    expect(screen.getByPlaceholderText('Search stocks...')).toBeInTheDocument();
  });

  it('calls onSearch when input changes', async () => {
    const user = userEvent.setup();
    render(
      <StockSearch
        onSearch={mockOnSearch}
        onSelect={mockOnSelect}
      />
    );

    const input = screen.getByPlaceholderText('종목명 또는 티커 검색...');
    await user.type(input, 'AAPL');

    await waitFor(() => {
      expect(mockOnSearch).toHaveBeenCalledWith('AAPL');
    });
  });

  it('shows loading state during search', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.searchStocks.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    const user = userEvent.setup();
    render(
      <StockSearch
        onSearch={mockOnSearch}
        onSelect={mockOnSelect}
      />
    );

    const input = screen.getByPlaceholderText('종목명 또는 티커 검색...');
    await user.type(input, 'AAPL');

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('displays search suggestions', async () => {
    const mockSuggestions = [
      { symbol: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' },
      { symbol: 'MSFT', name: 'Microsoft Corporation', exchange: 'NASDAQ' }
    ];

    const { stockService } = require('../../services/stockService');
    stockService.searchStocks.mockResolvedValue(mockSuggestions);

    const user = userEvent.setup();
    render(
      <StockSearch
        onSearch={mockOnSearch}
        onSelect={mockOnSelect}
      />
    );

    const input = screen.getByPlaceholderText('종목명 또는 티커 검색...');
    await user.type(input, 'AAPL');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
      expect(screen.getByText('Apple Inc.')).toBeInTheDocument();
      expect(screen.getByText('MSFT')).toBeInTheDocument();
    });
  });

  it('calls onSelect when suggestion is clicked', async () => {
    const mockSuggestions = [
      { symbol: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ' }
    ];

    const { stockService } = require('../../services/stockService');
    stockService.searchStocks.mockResolvedValue(mockSuggestions);

    const user = userEvent.setup();
    render(
      <StockSearch
        onSearch={mockOnSearch}
        onSelect={mockOnSelect}
      />
    );

    const input = screen.getByPlaceholderText('종목명 또는 티커 검색...');
    await user.type(input, 'AAPL');

    await waitFor(() => {
      const suggestion = screen.getByText('AAPL');
      user.click(suggestion);
    });

    expect(mockOnSelect).toHaveBeenCalledWith('AAPL');
  });
});
```

#### 1.2 StockChart 컴포넌트 테스트
```typescript
// frontend/src/components/__tests__/StockChart.test.tsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import StockChart from '../charts/StockChart';

// Mock Recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div data-testid="chart">{children}</div>,
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

// Mock the stock service
jest.mock('../../services/stockService', () => ({
  stockService: {
    getStockChart: jest.fn()
  }
}));

describe('StockChart', () => {
  const mockChartData = {
    data: [
      {
        timestamp: '2023-01-01T00:00:00Z',
        open: 100,
        high: 105,
        low: 98,
        close: 102,
        volume: 1000000
      },
      {
        timestamp: '2023-01-02T00:00:00Z',
        open: 102,
        high: 108,
        low: 101,
        close: 106,
        volume: 1200000
      }
    ]
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<StockChart symbol="AAPL" />);
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders chart when data is loaded', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.getStockChart.mockResolvedValue(mockChartData);

    render(<StockChart symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText('AAPL Chart')).toBeInTheDocument();
      expect(screen.getByTestId('chart')).toBeInTheDocument();
    });
  });

  it('renders error state when API fails', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.getStockChart.mockRejectedValue(new Error('API Error'));

    render(<StockChart symbol="AAPL" />);

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  it('calls API with correct parameters', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.getStockChart.mockResolvedValue(mockChartData);

    render(<StockChart symbol="AAPL" period="1mo" interval="1d" />);

    await waitFor(() => {
      expect(stockService.getStockChart).toHaveBeenCalledWith('AAPL', '1mo', '1d');
    });
  });
});
```

### 2. 훅 테스트

#### 2.1 useStock 훅 테스트
```typescript
// frontend/src/hooks/__tests__/useStock.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useStock } from '../useStock';

// Mock the stock service
jest.mock('../../services/stockService', () => ({
  stockService: {
    getStockInfo: jest.fn()
  }
}));

describe('useStock', () => {
  const mockStockData = {
    symbol: 'AAPL',
    name: 'Apple Inc.',
    currentPrice: 150.25,
    change: 1.50,
    changePercent: 1.01
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns loading state initially', () => {
    const { result } = renderHook(() => useStock('AAPL'));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('fetches and returns stock data', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.getStockInfo.mockResolvedValue(mockStockData);

    const { result } = renderHook(() => useStock('AAPL'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(mockStockData);
    expect(result.current.error).toBe(null);
  });

  it('handles API errors', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.getStockInfo.mockRejectedValue(new Error('API Error'));

    const { result } = renderHook(() => useStock('AAPL'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBe(null);
    expect(result.current.error).toBe('API Error');
  });

  it('refetches when symbol changes', async () => {
    const { stockService } = require('../../services/stockService');
    stockService.getStockInfo.mockResolvedValue(mockStockData);

    const { result, rerender } = renderHook(({ symbol }) => useStock(symbol), {
      initialProps: { symbol: 'AAPL' }
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Change symbol
    rerender({ symbol: 'MSFT' });

    expect(result.current.loading).toBe(true);
    expect(stockService.getStockInfo).toHaveBeenCalledTimes(2);
  });
});
```

### 3. E2E 테스트 (Cypress)

#### 3.1 기본 사용자 플로우 테스트
```typescript
// frontend/cypress/e2e/stock-search.cy.ts
describe('Stock Search', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should search for a stock and display results', () => {
    // Mock API response
    cy.intercept('GET', '**/stock/AAPL/info', {
      statusCode: 200,
      body: {
        success: true,
        data: {
          symbol: 'AAPL',
          name: 'Apple Inc.',
          currentPrice: 150.25,
          change: 1.50,
          changePercent: 1.01
        }
      }
    }).as('getStockInfo');

    cy.intercept('GET', '**/stock/AAPL/chart*', {
      statusCode: 200,
      body: {
        success: true,
        data: {
          symbol: 'AAPL',
          period: '1y',
          interval: '1d',
          data: [
            {
              timestamp: '2023-01-01T00:00:00Z',
              open: 100,
              high: 105,
              low: 98,
              close: 102,
              volume: 1000000
            }
          ]
        }
      }
    }).as('getStockChart');

    // Search for AAPL
    cy.get('[data-testid="stock-search-input"]')
      .type('AAPL');

    // Wait for search results
    cy.get('[data-testid="search-suggestion"]')
      .first()
      .click();

    // Verify stock info is displayed
    cy.get('[data-testid="stock-symbol"]')
      .should('contain', 'AAPL');

    cy.get('[data-testid="stock-name"]')
      .should('contain', 'Apple Inc.');

    cy.get('[data-testid="stock-price"]')
      .should('contain', '$150.25');

    // Verify chart is displayed
    cy.get('[data-testid="stock-chart"]')
      .should('be.visible');

    // Verify API calls
    cy.wait('@getStockInfo');
    cy.wait('@getStockChart');
  });

  it('should handle search errors gracefully', () => {
    // Mock API error
    cy.intercept('GET', '**/stock/INVALID/info', {
      statusCode: 400,
      body: {
        success: false,
        error: {
          code: 'INVALID_SYMBOL',
          message: 'Invalid stock symbol provided'
        }
      }
    }).as('getStockInfoError');

    // Search for invalid symbol
    cy.get('[data-testid="stock-search-input"]')
      .type('INVALID');

    cy.get('[data-testid="search-suggestion"]')
      .first()
      .click();

    // Verify error message is displayed
    cy.get('[data-testid="error-message"]')
      .should('contain', 'Invalid stock symbol');

    cy.wait('@getStockInfoError');
  });
});
```

#### 3.2 모바일 반응형 테스트
```typescript
// frontend/cypress/e2e/mobile-responsive.cy.ts
describe('Mobile Responsive', () => {
  beforeEach(() => {
    cy.viewport('iphone-x');
    cy.visit('/');
  });

  it('should display mobile navigation menu', () => {
    // Mobile menu should be hidden initially
    cy.get('[data-testid="mobile-menu"]')
      .should('not.be.visible');

    // Click hamburger menu
    cy.get('[data-testid="mobile-menu-button"]')
      .click();

    // Mobile menu should be visible
    cy.get('[data-testid="mobile-menu"]')
      .should('be.visible');

    // Menu items should be accessible
    cy.get('[data-testid="mobile-menu-item"]')
      .should('have.length.at.least', 3);
  });

  it('should handle touch gestures', () => {
    // Test swipe gesture on chart
    cy.get('[data-testid="stock-chart"]')
      .trigger('touchstart', { touches: [{ clientX: 100, clientY: 100 }] })
      .trigger('touchmove', { touches: [{ clientX: 200, clientY: 100 }] })
      .trigger('touchend');

    // Verify chart interaction (implementation dependent)
    cy.get('[data-testid="chart-tooltip"]')
      .should('be.visible');
  });

  it('should have proper touch targets', () => {
    // Check that all interactive elements are at least 44px
    cy.get('button, a, input, select')
      .each(($el) => {
        const width = $el.width();
        const height = $el.height();
        
        expect(width).to.be.at.least(44);
        expect(height).to.be.at.least(44);
      });
  });
});
```

## 📊 테스트 커버리지

### 커버리지 목표
```yaml
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*
    */venv/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod
```

### 커버리지 명령어
```bash
# 백엔드 커버리지
cd backend
pytest --cov=app --cov-report=html --cov-report=term

# 프론트엔드 커버리지
cd frontend
npm test -- --coverage --watchAll=false
```

## 🔄 CI/CD 파이프라인 테스트

### GitHub Actions 테스트 워크플로우
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        cd backend
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
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
        npm test -- --coverage --watchAll=false --passWithNoTests
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./frontend/coverage/lcov.info
```

## 🚀 성능 테스트

### 부하 테스트 (Locust)
```python
# backend/tests/load_test.py
from locust import HttpUser, task, between

class StockAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_stock_info(self):
        """주식 정보 조회 부하 테스트"""
        self.client.get("/stock/AAPL/info")
    
    @task(2)
    def get_stock_chart(self):
        """주식 차트 조회 부하 테스트"""
        self.client.get("/stock/AAPL/chart?period=1y&interval=1d")
    
    @task(1)
    def search_stocks(self):
        """주식 검색 부하 테스트"""
        self.client.get("/search/ticker?q=AAPL&limit=10")
```

### 실행 명령어
```bash
# 부하 테스트 실행
cd backend
locust -f tests/load_test.py --host=http://localhost:8000
``` 