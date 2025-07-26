# 04. 프론트엔드 설계 및 컴포넌트 구조

## 🎨 UI/UX 설계 원칙

### 디자인 시스템
- **Color Palette**: 다크/라이트 테마 지원
- **Typography**: 시스템 폰트 스택 사용
- **Spacing**: 4px 그리드 시스템
- **Components**: 재사용 가능한 컴포넌트 라이브러리

### 반응형 디자인
- **Mobile First**: 모바일 우선 설계
- **Breakpoints**: sm(640px), md(768px), lg(1024px), xl(1280px)
- **Touch Friendly**: 최소 44px 터치 타겟

## 📱 페이지 구조

### 라우팅 구조
```
/                    # 홈페이지 (검색 + 인기 종목)
/search              # 검색 결과 페이지
/stock/:symbol       # 주식 상세 페이지
  ├── overview       # 기본 정보
  ├── chart          # 차트 뷰
  ├── financials     # 재무 정보
  ├── dividends      # 배당 정보
  └── news           # 뉴스
/favorites           # 즐겨찾기 목록
/compare             # 종목 비교
/profile             # 사용자 프로필
```

## 🧩 컴포넌트 아키텍처

### 컴포넌트 계층 구조
```
src/
├── components/
│   ├── common/           # 공통 컴포넌트
│   │   ├── Button/
│   │   ├── Input/
│   │   ├── Modal/
│   │   ├── Loading/
│   │   └── ErrorBoundary/
│   ├── layout/           # 레이아웃 컴포넌트
│   │   ├── Header/
│   │   ├── Sidebar/
│   │   ├── Footer/
│   │   └── Navigation/
│   ├── stock/            # 주식 관련 컴포넌트
│   │   ├── StockCard/
│   │   ├── StockChart/
│   │   ├── StockInfo/
│   │   ├── StockSearch/
│   │   └── StockComparison/
│   ├── charts/           # 차트 컴포넌트
│   │   ├── LineChart/
│   │   ├── CandlestickChart/
│   │   ├── VolumeChart/
│   │   └── TechnicalIndicators/
│   └── financials/       # 재무 정보 컴포넌트
│       ├── FinancialTable/
│       ├── RatioCard/
│       └── TrendChart/
```

## 🎯 핵심 컴포넌트 설계

### 1. StockSearch 컴포넌트
```typescript
interface StockSearchProps {
  onSearch: (query: string) => void;
  onSelect: (symbol: string) => void;
  placeholder?: string;
  className?: string;
}

const StockSearch: React.FC<StockSearchProps> = ({
  onSearch,
  onSelect,
  placeholder = "종목명 또는 티커 검색...",
  className
}) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<StockSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // 검색 로직
  const handleSearch = useCallback(
    debounce(async (searchQuery: string) => {
      if (searchQuery.length < 2) {
        setSuggestions([]);
        return;
      }
      
      setIsLoading(true);
      try {
        const results = await searchStocks(searchQuery);
        setSuggestions(results);
      } catch (error) {
        console.error("Search error:", error);
      } finally {
        setIsLoading(false);
      }
    }, 300),
    []
  );
  
  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            handleSearch(e.target.value);
          }}
          placeholder={placeholder}
          className="w-full px-4 py-3 pl-12 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400" />
        {isLoading && (
          <LoadingSpinner className="absolute right-3 top-1/2 transform -translate-y-1/2 w-6 h-6" />
        )}
      </div>
      
      {/* 검색 제안 */}
      {suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.symbol}
              onClick={() => {
                onSelect(suggestion.symbol);
                setQuery("");
                setSuggestions([]);
              }}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-900">
                    {suggestion.symbol}
                  </div>
                  <div className="text-sm text-gray-600">
                    {suggestion.name}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {suggestion.exchange}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
```

### 2. StockChart 컴포넌트
```typescript
interface StockChartProps {
  symbol: string;
  period: ChartPeriod;
  interval: ChartInterval;
  chartType: 'line' | 'candlestick' | 'area';
  showVolume?: boolean;
  showIndicators?: boolean;
  height?: number;
  className?: string;
}

const StockChart: React.FC<StockChartProps> = ({
  symbol,
  period,
  interval,
  chartType,
  showVolume = true,
  showIndicators = false,
  height = 400,
  className
}) => {
  const { data, isLoading, error } = useStockChart(symbol, period, interval);
  
  if (isLoading) {
    return <ChartSkeleton height={height} />;
  }
  
  if (error) {
    return <ChartError error={error} />;
  }
  
  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            {symbol} 차트
          </h3>
          <ChartControls
            period={period}
            interval={interval}
            chartType={chartType}
            onPeriodChange={setPeriod}
            onIntervalChange={setInterval}
            onChartTypeChange={setChartType}
          />
        </div>
      </div>
      
      <div className="p-4">
        {chartType === 'candlestick' ? (
          <CandlestickChart
            data={data}
            height={height}
            showVolume={showVolume}
            showIndicators={showIndicators}
          />
        ) : (
          <LineChart
            data={data}
            height={height}
            showVolume={showVolume}
            showIndicators={showIndicators}
            type={chartType}
          />
        )}
      </div>
    </div>
  );
};
```

### 3. StockInfo 컴포넌트
```typescript
interface StockInfoProps {
  symbol: string;
  className?: string;
}

const StockInfo: React.FC<StockInfoProps> = ({ symbol, className }) => {
  const { data, isLoading, error } = useStockInfo(symbol);
  
  if (isLoading) {
    return <StockInfoSkeleton />;
  }
  
  if (error) {
    return <StockInfoError error={error} />;
  }
  
  return (
    <div className={`bg-white rounded-lg shadow-sm border ${className}`}>
      {/* 헤더 */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {data.symbol}
            </h1>
            <p className="text-lg text-gray-600">{data.name}</p>
            <p className="text-sm text-gray-500">
              {data.exchange} • {data.sector}
            </p>
          </div>
          <FavoriteButton symbol={symbol} />
        </div>
      </div>
      
      {/* 가격 정보 */}
      <div className="p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <PriceCard
            label="현재가"
            value={data.currentPrice}
            change={data.change}
            changePercent={data.changePercent}
            isMain={true}
          />
          <InfoCard label="시가총액" value={formatMarketCap(data.marketCap)} />
          <InfoCard label="PER" value={data.pe} />
          <InfoCard label="배당수익률" value={`${data.dividendYield}%`} />
        </div>
        
        {/* 추가 정보 */}
        <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-4">
          <InfoCard label="52주 최고" value={data.fiftyTwoWeekHigh} />
          <InfoCard label="52주 최저" value={data.fiftyTwoWeekLow} />
          <InfoCard label="거래량" value={formatVolume(data.volume)} />
          <InfoCard label="평균거래량" value={formatVolume(data.avgVolume)} />
          <InfoCard label="베타" value={data.beta} />
          <InfoCard label="통화" value={data.currency} />
        </div>
      </div>
    </div>
  );
};
```

## 📊 차트 컴포넌트 상세

### CandlestickChart 컴포넌트
```typescript
interface CandlestickChartProps {
  data: ChartData[];
  height: number;
  showVolume?: boolean;
  showIndicators?: boolean;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  height,
  showVolume = true,
  showIndicators = false
}) => {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.timestamp),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume
    }));
  }, [data]);
  
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          type="category"
          scale="band"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
        />
        <YAxis
          domain={['dataMin - 1', 'dataMax + 1']}
          tickFormatter={(value) => `$${value.toFixed(2)}`}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                  <p className="font-semibold">
                    {format(new Date(label), 'yyyy-MM-dd')}
                  </p>
                  <p>Open: ${data.open}</p>
                  <p>High: ${data.high}</p>
                  <p>Low: ${data.low}</p>
                  <p>Close: ${data.close}</p>
                  <p>Volume: {formatVolume(data.volume)}</p>
                </div>
              );
            }
            return null;
          }}
        />
        
        {/* 캔들스틱 */}
        <Bar
          dataKey="high"
          fill="transparent"
          stroke="transparent"
          strokeWidth={0}
        />
        <Bar
          dataKey="low"
          fill="transparent"
          stroke="transparent"
          strokeWidth={0}
        />
        
        {/* 캔들스틱 바디 */}
        {chartData.map((entry, index) => {
          const isGreen = entry.close >= entry.open;
          const bodyHeight = Math.abs(entry.close - entry.open);
          const bodyY = Math.min(entry.open, entry.close);
          
          return (
            <g key={index}>
              {/* 위꼬리 */}
              <line
                x1={index + 0.5}
                y1={entry.low}
                x2={index + 0.5}
                y2={Math.min(entry.open, entry.close)}
                stroke={isGreen ? '#10B981' : '#EF4444'}
                strokeWidth={1}
              />
              
              {/* 바디 */}
              <rect
                x={index + 0.1}
                y={bodyY}
                width={0.8}
                height={bodyHeight}
                fill={isGreen ? '#10B981' : '#EF4444'}
                stroke={isGreen ? '#10B981' : '#EF4444'}
                strokeWidth={1}
              />
              
              {/* 아래꼬리 */}
              <line
                x1={index + 0.5}
                y1={Math.max(entry.open, entry.close)}
                x2={index + 0.5}
                y2={entry.high}
                stroke={isGreen ? '#10B981' : '#EF4444'}
                strokeWidth={1}
              />
            </g>
          );
        })}
        
        {/* 거래량 */}
        {showVolume && (
          <Bar
            dataKey="volume"
            fill="#6B7280"
            opacity={0.3}
            yAxisId={1}
          />
        )}
        
        {/* 기술적 지표 */}
        {showIndicators && (
          <>
            <Line
              type="monotone"
              dataKey="sma20"
              stroke="#3B82F6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="sma50"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={false}
            />
          </>
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
};
```

## 🎨 스타일링 전략

### Tailwind CSS 설정
```javascript
// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        success: {
          50: '#f0fdf4',
          500: '#10b981',
          600: '#059669',
        },
        danger: {
          50: '#fef2f2',
          500: '#ef4444',
          600: '#dc2626',
        },
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#6b7280',
          600: '#4b5563',
          700: '#374151',
          800: '#1f2937',
          900: '#111827',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

### 공통 스타일 클래스
```css
/* styles/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors;
  }
  
  .btn-secondary {
    @apply px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors;
  }
  
  .card {
    @apply bg-white rounded-lg shadow-sm border border-gray-200;
  }
  
  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent;
  }
  
  .loading-spinner {
    @apply animate-spin rounded-full border-2 border-gray-300 border-t-primary-600;
  }
}
```

## 📱 모바일 최적화

### 터치 제스처 지원
```typescript
// hooks/useSwipe.ts
export const useSwipe = (onSwipeLeft?: () => void, onSwipeRight?: () => void) => {
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  
  const minSwipeDistance = 50;
  
  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };
  
  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };
  
  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;
    
    if (isLeftSwipe && onSwipeLeft) {
      onSwipeLeft();
    }
    if (isRightSwipe && onSwipeRight) {
      onSwipeRight();
    }
  };
  
  return {
    onTouchStart,
    onTouchMove,
    onTouchEnd,
  };
};
```

### 반응형 네비게이션
```typescript
const MobileNavigation: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <>
      {/* 모바일 메뉴 버튼 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="md:hidden p-2 rounded-lg hover:bg-gray-100"
      >
        <MenuIcon className="w-6 h-6" />
      </button>
      
      {/* 모바일 메뉴 */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-black bg-opacity-50" onClick={() => setIsOpen(false)} />
          <div className="fixed right-0 top-0 h-full w-64 bg-white shadow-lg">
            <div className="p-4">
              <button
                onClick={() => setIsOpen(false)}
                className="absolute top-4 right-4 p-2 rounded-lg hover:bg-gray-100"
              >
                <XIcon className="w-6 h-6" />
              </button>
              
              <nav className="mt-8">
                <NavLink to="/" className="block py-2 text-gray-900 hover:text-primary-600">
                  홈
                </NavLink>
                <NavLink to="/favorites" className="block py-2 text-gray-900 hover:text-primary-600">
                  즐겨찾기
                </NavLink>
                <NavLink to="/compare" className="block py-2 text-gray-900 hover:text-primary-600">
                  종목 비교
                </NavLink>
              </nav>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
```

## 🚀 성능 최적화

### 코드 스플리팅
```typescript
// App.tsx
import { lazy, Suspense } from 'react';

const HomePage = lazy(() => import('./pages/HomePage'));
const StockDetailPage = lazy(() => import('./pages/StockDetailPage'));
const FavoritesPage = lazy(() => import('./pages/FavoritesPage'));

function App() {
  return (
    <Router>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/stock/:symbol" element={<StockDetailPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
        </Routes>
      </Suspense>
    </Router>
  );
}
```

### 메모이제이션
```typescript
// 컴포넌트 메모이제이션
const StockCard = React.memo<StockCardProps>(({ stock, onFavorite }) => {
  return (
    <div className="card p-4">
      {/* 컴포넌트 내용 */}
    </div>
  );
});

// 계산 메모이제이션
const useMemoizedChartData = (rawData: ChartData[]) => {
  return useMemo(() => {
    return rawData.map(item => ({
      ...item,
      formattedDate: format(new Date(item.timestamp), 'MM/dd'),
      formattedPrice: `$${item.close.toFixed(2)}`,
    }));
  }, [rawData]);
};
``` 