# 05. 차트 컴포넌트 상세 설계

## 📊 차트 라이브러리 선택

### Recharts 선택 이유
- **React Native 지원**: 모바일 앱 확장 가능
- **TypeScript 지원**: 타입 안정성
- **커스터마이징**: 높은 자유도
- **성능**: 가상화 및 최적화
- **커뮤니티**: 활발한 개발 및 지원

### 대안 고려사항
- **Chart.js**: 더 많은 차트 타입, 하지만 React 래퍼 필요
- **D3.js**: 최고의 커스터마이징, 하지만 학습 곡선
- **TradingView**: 전문적이지만 라이선스 비용

## 🎯 차트 타입별 구현

### 1. 라인 차트 (Line Chart)
```typescript
interface LineChartProps {
  data: ChartData[];
  height: number;
  showVolume?: boolean;
  showIndicators?: boolean;
  type?: 'line' | 'area';
  color?: string;
}

const LineChart: React.FC<LineChartProps> = ({
  data,
  height,
  showVolume = true,
  showIndicators = false,
  type = 'line',
  color = '#3B82F6'
}) => {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.timestamp),
      price: item.close,
      volume: item.volume,
      sma20: item.sma20,
      sma50: item.sma50,
      ema12: item.ema12,
      ema26: item.ema26
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        
        <XAxis
          dataKey="date"
          type="category"
          scale="band"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <YAxis
          domain={['dataMin - 1', 'dataMax + 1']}
          tickFormatter={(value) => `$${value.toFixed(2)}`}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                  <p className="font-semibold text-gray-900 mb-2">
                    {format(new Date(label), 'yyyy-MM-dd')}
                  </p>
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="text-gray-600">가격:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        ${data.price.toFixed(2)}
                      </span>
                    </p>
                    {showVolume && (
                      <p className="text-sm">
                        <span className="text-gray-600">거래량:</span>
                        <span className="font-medium text-gray-900 ml-2">
                          {formatVolume(data.volume)}
                        </span>
                      </p>
                    )}
                    {showIndicators && data.sma20 && (
                      <p className="text-sm">
                        <span className="text-blue-600">SMA20:</span>
                        <span className="font-medium text-gray-900 ml-2">
                          ${data.sma20.toFixed(2)}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        
        {/* 메인 차트 라인 */}
        {type === 'area' ? (
          <Area
            type="monotone"
            dataKey="price"
            stroke={color}
            fill={color}
            fillOpacity={0.1}
            strokeWidth={2}
            dot={false}
          />
        ) : (
          <Line
            type="monotone"
            dataKey="price"
            stroke={color}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: color }}
          />
        )}
        
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
              strokeWidth={1.5}
              dot={false}
              name="SMA 20"
            />
            <Line
              type="monotone"
              dataKey="sma50"
              stroke="#F59E0B"
              strokeWidth={1.5}
              dot={false}
              name="SMA 50"
            />
            <Line
              type="monotone"
              dataKey="ema12"
              stroke="#10B981"
              strokeWidth={1.5}
              dot={false}
              name="EMA 12"
            />
            <Line
              type="monotone"
              dataKey="ema26"
              stroke="#8B5CF6"
              strokeWidth={1.5}
              dot={false}
              name="EMA 26"
            />
          </>
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
};
```

### 2. 캔들스틱 차트 (Candlestick Chart)
```typescript
interface CandlestickChartProps {
  data: ChartData[];
  height: number;
  showVolume?: boolean;
  showIndicators?: boolean;
  showBollinger?: boolean;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  height,
  showVolume = true,
  showIndicators = false,
  showBollinger = false
}) => {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.timestamp),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume,
      sma20: item.sma20,
      sma50: item.sma50,
      bollingerUpper: item.bollingerUpper,
      bollingerMiddle: item.bollingerMiddle,
      bollingerLower: item.bollingerLower
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        
        <XAxis
          dataKey="date"
          type="category"
          scale="band"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <YAxis
          domain={['dataMin - 1', 'dataMax + 1']}
          tickFormatter={(value) => `$${value.toFixed(2)}`}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              const isGreen = data.close >= data.open;
              
              return (
                <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                  <p className="font-semibold text-gray-900 mb-2">
                    {format(new Date(label), 'yyyy-MM-dd')}
                  </p>
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="text-gray-600">Open:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        ${data.open.toFixed(2)}
                      </span>
                    </p>
                    <p className="text-sm">
                      <span className="text-gray-600">High:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        ${data.high.toFixed(2)}
                      </span>
                    </p>
                    <p className="text-sm">
                      <span className="text-gray-600">Low:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        ${data.low.toFixed(2)}
                      </span>
                    </p>
                    <p className="text-sm">
                      <span className="text-gray-600">Close:</span>
                      <span className={`font-medium ml-2 ${isGreen ? 'text-green-600' : 'text-red-600'}`}>
                        ${data.close.toFixed(2)}
                      </span>
                    </p>
                    {showVolume && (
                      <p className="text-sm">
                        <span className="text-gray-600">Volume:</span>
                        <span className="font-medium text-gray-900 ml-2">
                          {formatVolume(data.volume)}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        
        {/* 볼린저 밴드 */}
        {showBollinger && (
          <>
            <Area
              type="monotone"
              dataKey="bollingerUpper"
              stroke="#3B82F6"
              fill="#3B82F6"
              fillOpacity={0.1}
              strokeWidth={1}
              dot={false}
              name="Bollinger Upper"
            />
            <Line
              type="monotone"
              dataKey="bollingerMiddle"
              stroke="#6B7280"
              strokeWidth={1}
              dot={false}
              name="Bollinger Middle"
            />
            <Area
              type="monotone"
              dataKey="bollingerLower"
              stroke="#3B82F6"
              fill="#3B82F6"
              fillOpacity={0.1}
              strokeWidth={1}
              dot={false}
              name="Bollinger Lower"
            />
          </>
        )}
        
        {/* 캔들스틱 렌더링 */}
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
              strokeWidth={1.5}
              dot={false}
              name="SMA 20"
            />
            <Line
              type="monotone"
              dataKey="sma50"
              stroke="#F59E0B"
              strokeWidth={1.5}
              dot={false}
              name="SMA 50"
            />
          </>
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
};
```

### 3. 거래량 차트 (Volume Chart)
```typescript
interface VolumeChartProps {
  data: ChartData[];
  height: number;
  showPrice?: boolean;
  color?: string;
}

const VolumeChart: React.FC<VolumeChartProps> = ({
  data,
  height,
  showPrice = false,
  color = '#6B7280'
}) => {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.timestamp),
      volume: item.volume,
      price: item.close,
      isGreen: item.close >= item.open
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        
        <XAxis
          dataKey="date"
          type="category"
          scale="band"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <YAxis
          tickFormatter={(value) => formatVolume(value)}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        {showPrice && (
          <YAxis
            yAxisId={1}
            orientation="right"
            tickFormatter={(value) => `$${value.toFixed(2)}`}
            tick={{ fontSize: 12, fill: '#6B7280' }}
            axisLine={{ stroke: '#D1D5DB' }}
          />
        )}
        
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                  <p className="font-semibold text-gray-900 mb-2">
                    {format(new Date(label), 'yyyy-MM-dd')}
                  </p>
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="text-gray-600">Volume:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        {formatVolume(data.volume)}
                      </span>
                    </p>
                    {showPrice && (
                      <p className="text-sm">
                        <span className="text-gray-600">Price:</span>
                        <span className="font-medium text-gray-900 ml-2">
                          ${data.price.toFixed(2)}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        
        {/* 거래량 바 */}
        {chartData.map((entry, index) => (
          <rect
            key={index}
            x={index + 0.1}
            y={0}
            width={0.8}
            height={entry.volume}
            fill={entry.isGreen ? '#10B981' : '#EF4444'}
            opacity={0.7}
          />
        ))}
        
        {/* 가격 라인 */}
        {showPrice && (
          <Line
            type="monotone"
            dataKey="price"
            stroke={color}
            strokeWidth={1}
            dot={false}
            yAxisId={1}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  );
};
```

## 📈 기술적 지표 차트

### 1. RSI 차트
```typescript
interface RSIChartProps {
  data: ChartData[];
  height: number;
  overbought?: number;
  oversold?: number;
}

const RSIChart: React.FC<RSIChartProps> = ({
  data,
  height,
  overbought = 70,
  oversold = 30
}) => {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.timestamp),
      rsi: item.rsi
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        
        <XAxis
          dataKey="date"
          type="category"
          scale="band"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                  <p className="font-semibold text-gray-900 mb-2">
                    {format(new Date(label), 'yyyy-MM-dd')}
                  </p>
                  <p className="text-sm">
                    <span className="text-gray-600">RSI:</span>
                    <span className="font-medium text-gray-900 ml-2">
                      {data.rsi.toFixed(2)}
                    </span>
                  </p>
                </div>
              );
            }
            return null;
          }}
        />
        
        {/* RSI 라인 */}
        <Line
          type="monotone"
          dataKey="rsi"
          stroke="#8B5CF6"
          strokeWidth={2}
          dot={false}
        />
        
        {/* 과매수/과매도 라인 */}
        <ReferenceLine y={overbought} stroke="#EF4444" strokeDasharray="3 3" />
        <ReferenceLine y={oversold} stroke="#10B981" strokeDasharray="3 3" />
        <ReferenceLine y={50} stroke="#6B7280" strokeDasharray="3 3" />
      </LineChart>
    </ResponsiveContainer>
  );
};
```

### 2. MACD 차트
```typescript
interface MACDChartProps {
  data: ChartData[];
  height: number;
}

const MACDChart: React.FC<MACDChartProps> = ({ data, height }) => {
  const chartData = useMemo(() => {
    return data.map(item => ({
      date: new Date(item.timestamp),
      macd: item.macd,
      signal: item.signal,
      histogram: item.histogram
    }));
  }, [data]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
        
        <XAxis
          dataKey="date"
          type="category"
          scale="band"
          tickFormatter={(value) => format(new Date(value), 'MM/dd')}
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <YAxis
          tick={{ fontSize: 12, fill: '#6B7280' }}
          axisLine={{ stroke: '#D1D5DB' }}
        />
        
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const data = payload[0].payload;
              return (
                <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
                  <p className="font-semibold text-gray-900 mb-2">
                    {format(new Date(label), 'yyyy-MM-dd')}
                  </p>
                  <div className="space-y-1">
                    <p className="text-sm">
                      <span className="text-blue-600">MACD:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        {data.macd.toFixed(3)}
                      </span>
                    </p>
                    <p className="text-sm">
                      <span className="text-orange-600">Signal:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        {data.signal.toFixed(3)}
                      </span>
                    </p>
                    <p className="text-sm">
                      <span className="text-gray-600">Histogram:</span>
                      <span className="font-medium text-gray-900 ml-2">
                        {data.histogram.toFixed(3)}
                      </span>
                    </p>
                  </div>
                </div>
              );
            }
            return null;
          }}
        />
        
        {/* MACD 라인 */}
        <Line
          type="monotone"
          dataKey="macd"
          stroke="#3B82F6"
          strokeWidth={2}
          dot={false}
          name="MACD"
        />
        
        {/* Signal 라인 */}
        <Line
          type="monotone"
          dataKey="signal"
          stroke="#F59E0B"
          strokeWidth={2}
          dot={false}
          name="Signal"
        />
        
        {/* Histogram */}
        <Bar
          dataKey="histogram"
          fill={(entry) => entry.histogram >= 0 ? '#10B981' : '#EF4444'}
          opacity={0.7}
          name="Histogram"
        />
        
        {/* Zero 라인 */}
        <ReferenceLine y={0} stroke="#6B7280" strokeDasharray="3 3" />
      </ComposedChart>
    </ResponsiveContainer>
  );
};
```

## 🎛 차트 컨트롤 컴포넌트

### ChartControls 컴포넌트
```typescript
interface ChartControlsProps {
  period: ChartPeriod;
  interval: ChartInterval;
  chartType: ChartType;
  onPeriodChange: (period: ChartPeriod) => void;
  onIntervalChange: (interval: ChartInterval) => void;
  onChartTypeChange: (type: ChartType) => void;
  showIndicators: boolean;
  onShowIndicatorsChange: (show: boolean) => void;
  showVolume: boolean;
  onShowVolumeChange: (show: boolean) => void;
}

const ChartControls: React.FC<ChartControlsProps> = ({
  period,
  interval,
  chartType,
  onPeriodChange,
  onIntervalChange,
  onChartTypeChange,
  showIndicators,
  onShowIndicatorsChange,
  showVolume,
  onShowVolumeChange
}) => {
  const periods = [
    { value: '1d', label: '1일' },
    { value: '5d', label: '5일' },
    { value: '1mo', label: '1개월' },
    { value: '3mo', label: '3개월' },
    { value: '6mo', label: '6개월' },
    { value: '1y', label: '1년' },
    { value: '2y', label: '2년' },
    { value: '5y', label: '5년' },
    { value: 'max', label: '전체' }
  ];

  const intervals = [
    { value: '1m', label: '1분' },
    { value: '5m', label: '5분' },
    { value: '15m', label: '15분' },
    { value: '30m', label: '30분' },
    { value: '1h', label: '1시간' },
    { value: '1d', label: '1일' },
    { value: '1wk', label: '1주' },
    { value: '1mo', label: '1개월' }
  ];

  const chartTypes = [
    { value: 'line', label: '라인', icon: LineIcon },
    { value: 'candlestick', label: '캔들', icon: CandlestickIcon },
    { value: 'area', label: '영역', icon: AreaIcon }
  ];

  return (
    <div className="flex flex-wrap items-center gap-4 text-sm">
      {/* 기간 선택 */}
      <div className="flex items-center space-x-2">
        <span className="text-gray-600">기간:</span>
        <select
          value={period}
          onChange={(e) => onPeriodChange(e.target.value as ChartPeriod)}
          className="px-3 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {periods.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </div>

      {/* 간격 선택 */}
      <div className="flex items-center space-x-2">
        <span className="text-gray-600">간격:</span>
        <select
          value={interval}
          onChange={(e) => onIntervalChange(e.target.value as ChartInterval)}
          className="px-3 py-1 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {intervals.map((i) => (
            <option key={i.value} value={i.value}>
              {i.label}
            </option>
          ))}
        </select>
      </div>

      {/* 차트 타입 선택 */}
      <div className="flex items-center space-x-2">
        <span className="text-gray-600">차트:</span>
        <div className="flex border border-gray-300 rounded-md">
          {chartTypes.map((type) => (
            <button
              key={type.value}
              onClick={() => onChartTypeChange(type.value as ChartType)}
              className={`px-3 py-1 flex items-center space-x-1 transition-colors ${
                chartType === type.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-50'
              } ${type.value === 'line' ? 'rounded-l-md' : ''} ${
                type.value === 'area' ? 'rounded-r-md' : ''
              }`}
            >
              <type.icon className="w-4 h-4" />
              <span>{type.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 옵션 토글 */}
      <div className="flex items-center space-x-4">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={showIndicators}
            onChange={(e) => onShowIndicatorsChange(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-gray-600">지표</span>
        </label>
        
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={showVolume}
            onChange={(e) => onShowVolumeChange(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-gray-600">거래량</span>
        </label>
      </div>
    </div>
  );
};
```

## 📱 모바일 최적화

### 터치 제스처 지원
```typescript
const useChartGestures = (onZoomIn: () => void, onZoomOut: () => void) => {
  const [pinchDistance, setPinchDistance] = useState<number | null>(null);
  
  const handleTouchStart = (e: React.TouchEvent) => {
    if (e.touches.length === 2) {
      const distance = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      setPinchDistance(distance);
    }
  };
  
  const handleTouchMove = (e: React.TouchEvent) => {
    if (e.touches.length === 2 && pinchDistance !== null) {
      const currentDistance = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      
      const threshold = 50;
      if (currentDistance > pinchDistance + threshold) {
        onZoomIn();
        setPinchDistance(currentDistance);
      } else if (currentDistance < pinchDistance - threshold) {
        onZoomOut();
        setPinchDistance(currentDistance);
      }
    }
  };
  
  const handleTouchEnd = () => {
    setPinchDistance(null);
  };
  
  return {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
  };
};
```

### 반응형 차트 크기
```typescript
const useResponsiveChartSize = () => {
  const [chartSize, setChartSize] = useState({ width: 0, height: 400 });
  
  useEffect(() => {
    const updateSize = () => {
      const width = window.innerWidth;
      let height = 400;
      
      if (width < 640) { // sm
        height = 300;
      } else if (width < 768) { // md
        height = 350;
      } else if (width < 1024) { // lg
        height = 400;
      } else { // xl+
        height = 450;
      }
      
      setChartSize({ width, height });
    };
    
    updateSize();
    window.addEventListener('resize', updateSize);
    
    return () => window.removeEventListener('resize', updateSize);
  }, []);
  
  return chartSize;
};
```

## 🚀 성능 최적화

### 차트 데이터 메모이제이션
```typescript
const useMemoizedChartData = (rawData: ChartData[], options: ChartOptions) => {
  return useMemo(() => {
    return rawData.map(item => ({
      ...item,
      date: new Date(item.timestamp),
      formattedDate: format(new Date(item.timestamp), 'MM/dd'),
      formattedPrice: `$${item.close.toFixed(2)}`,
      formattedVolume: formatVolume(item.volume),
      // 기술적 지표 계산
      sma20: calculateSMA(rawData, 20, item.timestamp),
      sma50: calculateSMA(rawData, 50, item.timestamp),
      rsi: calculateRSI(rawData, item.timestamp),
      macd: calculateMACD(rawData, item.timestamp),
    }));
  }, [rawData, options]);
};
```

### 가상화된 차트 렌더링
```typescript
const VirtualizedChart: React.FC<VirtualizedChartProps> = ({ data, height }) => {
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 100 });
  
  const visibleData = useMemo(() => {
    return data.slice(visibleRange.start, visibleRange.end);
  }, [data, visibleRange]);
  
  const handleScroll = (event: any) => {
    // 스크롤 위치에 따라 가시 범위 업데이트
    const scrollLeft = event.target.scrollLeft;
    const containerWidth = event.target.clientWidth;
    const itemWidth = containerWidth / 100; // 가정
    
    const start = Math.floor(scrollLeft / itemWidth);
    const end = Math.min(start + 100, data.length);
    
    setVisibleRange({ start, end });
  };
  
  return (
    <div className="overflow-x-auto" onScroll={handleScroll}>
      <div style={{ width: `${data.length * 10}px` }}>
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={visibleData}>
            {/* 차트 구성 */}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
``` 