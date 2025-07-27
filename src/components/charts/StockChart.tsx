import React, { useState } from 'react';
import { ResponsiveContainer, ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, Bar } from 'recharts';
import { useStockChart } from '../../hooks/useStockChart';
import { ChartPeriod, ChartInterval } from '../../types/stock';
import LoadingSpinner from '../common/LoadingSpinner';

interface StockChartProps {
  symbol: string;
  height?: number;
  className?: string;
}

// 커스텀 툴팁
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-900">{data.time}</p>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="text-gray-600">O: {data.open?.toFixed(2)}</div>
          <div className="text-gray-600">H: {data.high?.toFixed(2)}</div>
          <div className="text-gray-600">L: {data.low?.toFixed(2)}</div>
          <div className="text-gray-600">C: {data.close?.toFixed(2)}</div>
        </div>
        <div className="text-sm text-gray-500 mt-1">
          V: {(data.volume / 1000000).toFixed(2)}m
        </div>
      </div>
    );
  }
  return null;
};

// 캔들스틱 컴포넌트
const CandlestickChart = ({ data }: { data: any[] }) => {
  return (
    <g>
      {data.map((item, index) => {
        const isUp = item.close >= item.open;
        const bodyHeight = Math.abs(item.close - item.open);
        const bodyY = Math.min(item.open, item.close);
        const wickY = item.low;
        const wickHeight = item.high - item.low;
        
        return (
          <g key={index}>
            {/* 심지 (wick) */}
            <line
              x1={index + 0.5}
              y1={wickY}
              x2={index + 0.5}
              y2={item.high}
              stroke={isUp ? "#10B981" : "#EF4444"}
              strokeWidth={1}
            />
            {/* 몸통 (body) */}
            <rect
              x={index + 0.1}
              y={bodyY}
              width={0.8}
              height={bodyHeight}
              fill={isUp ? "#10B981" : "#EF4444"}
              stroke={isUp ? "#10B981" : "#EF4444"}
              strokeWidth={1}
            />
          </g>
        );
      })}
    </g>
  );
};

const StockChart: React.FC<StockChartProps> = ({
  symbol,
  height = 400,
  className
}) => {
  const [period, setPeriod] = useState<ChartPeriod>('1d');
  const [interval, setInterval] = useState<ChartInterval>('1h');
  const [showKeyEvents, setShowKeyEvents] = useState(true);
  const [chartType, setChartType] = useState<'line' | 'candle' | 'area'>('area');
  const [selectedRange, setSelectedRange] = useState('1D');

  const { data, loading, error } = useStockChart(symbol, period, interval);

  // 시간 범위 변경 핸들러
  const handleRangeChange = (range: string) => {
    setSelectedRange(range);
    
    // 범위에 따른 period 설정 (백엔드에서 지원하는 기간으로 매핑)
    switch (range) {
      case '1D':
        setPeriod('1d');
        setInterval('1h');
        break;
      case '5D':
        setPeriod('5d');
        setInterval('1d');
        break;
      case '1M':
        setPeriod('1mo');
        setInterval('1d');
        break;
      case '6M':
        setPeriod('6mo');
        setInterval('1d');
        break;
      case 'YTD':
        setPeriod('6mo'); // YTD는 6개월로 대체
        setInterval('1d');
        break;
      case '1Y':
        setPeriod('1y');
        setInterval('1d');
        break;
      case '5Y':
        setPeriod('5y');
        setInterval('1d');
        break;
      case 'All':
        setPeriod('max');
        setInterval('1d');
        break;
      default:
        setPeriod('1d');
        setInterval('1h');
    }
  };

  // 차트 데이터 변환
  const getChartData = () => {
    if (!data || data.length === 0) return [];

    return data.map((item, index) => {
      // 시간 포맷팅 (1일 차트의 경우)
      let timeLabel = '';
      if (period === '1d') {
        const date = new Date(item.timestamp);
        timeLabel = date.toLocaleTimeString('en-US', {
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        });
      } else {
        const date = new Date(item.timestamp);
        timeLabel = date.toLocaleDateString('ko-KR', {
          month: 'short',
          day: 'numeric'
        });
      }
      
      return {
        time: timeLabel,
        close: item.close,
        open: item.open,
        high: item.high,
        low: item.low,
        volume: item.volume,
        timestamp: item.timestamp,
        // Area 차트용 데이터
        areaValue: item.close,
        // 캔들스틱용 데이터
        isUp: item.close >= item.open,
        bodyHeight: Math.abs(item.close - item.open),
        bodyY: Math.min(item.open, item.close)
      };
    });
  };

  const chartData = getChartData();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        <p>Error: {error}</p>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>No chart data available</p>
      </div>
    );
  }

  // 현재 가격과 이전 종가 계산
  const currentPrice = data[data.length - 1]?.close || 0;
  const previousClose = data[0]?.close || 0;
  const priceChange = currentPrice - previousClose;
  const priceChangePercent = previousClose > 0 ? (priceChange / previousClose) * 100 : 0;
  const isPositive = priceChange >= 0;

  // OHLC 정보
  const latestData = data[data.length - 1] || {};
  const open = latestData.open || 0;
  const high = latestData.high || 0;
  const low = latestData.low || 0;
  const close = latestData.close || 0;
  const volume = latestData.volume || 0;

  return (
    <div className={`w-full ${className || ''}`}>
      {/* 상단 정보 섹션 */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{symbol}</h2>
            <div className="flex items-center space-x-4">
              <span className="text-3xl font-bold text-gray-900">${currentPrice.toFixed(2)}</span>
              <div className="flex items-center space-x-2">
                <span className={`text-lg font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  {isPositive ? '+' : ''}{priceChange.toFixed(2)}
                </span>
                <span className={`text-lg font-semibold ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
                  ({isPositive ? '+' : ''}{priceChangePercent.toFixed(2)}%)
                </span>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-1">As of {new Date().toLocaleTimeString('en-US', { hour12: true })}. Market Open.</p>
          </div>
        </div>

        {/* 차트 컨트롤 */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            <select 
              value={chartType}
              onChange={(e) => setChartType(e.target.value as 'line' | 'candle' | 'area')}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="area">Mountain</option>
              <option value="candle">Candle</option>
              <option value="line">Line</option>
            </select>
            
            <div className="flex items-center space-x-2">
              <button className="p-1 text-gray-600 hover:text-gray-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </button>
              <button className="p-1 text-gray-600 hover:text-gray-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
              <button className="p-1 text-gray-600 hover:text-gray-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </button>
              <button className="p-1 text-gray-600 hover:text-gray-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button className="p-1 text-gray-600 hover:text-gray-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              </button>
              <button className="p-1 text-gray-600 hover:text-gray-700">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* OHLC 정보 */}
        <div className="bg-gray-50 rounded-lg p-3 mb-4">
          <div className="grid grid-cols-5 gap-4 text-sm">
            <div>
              <span className="text-gray-500">O:</span>
              <span className="font-semibold ml-1">${open.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">H:</span>
              <span className="font-semibold ml-1">${high.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">L:</span>
              <span className="font-semibold ml-1">${low.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">C:</span>
              <span className="font-semibold ml-1">${close.toFixed(2)}</span>
            </div>
            <div>
              <span className="text-gray-500">V:</span>
              <span className="font-semibold ml-1">{(volume / 1000000).toFixed(2)}m</span>
            </div>
          </div>
        </div>

        {/* 시간 범위 선택기 */}
        <div className="flex items-center justify-between">
          <div className="flex space-x-1">
            {['1D', '5D', '1M', '3M', '6M', 'YTD', '1Y', '5Y', 'All'].map((range) => (
              <button
                key={range}
                onClick={() => handleRangeChange(range)}
                className={`px-3 py-1 text-sm font-medium rounded transition-colors ${
                  selectedRange === range ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {range}
              </button>
            ))}
          </div>

          <div className="flex items-center space-x-4">
            <button className="p-1 text-gray-600 hover:text-gray-700">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
            <select className="px-3 py-1 border border-gray-300 rounded text-sm">
              <option value="1m">Interval: 1 min</option>
              <option value="5m">Interval: 5 min</option>
              <option value="15m">Interval: 15 min</option>
              <option value="1h">Interval: 1 hour</option>
              <option value="1d">Interval: 1 day</option>
            </select>
          </div>
        </div>
      </div>
      
      {/* 차트 */}
      <div className="w-full border border-gray-200 rounded-lg p-4 bg-white relative" style={{ height: `${height}px` }}>
        {/* Yahoo Finance 워터마크 */}
        <div className="absolute top-2 right-2 text-gray-300 text-xs font-semibold z-10">
          yahoo!finance
        </div>
        
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="time" 
              stroke="#666" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false}
              tickFormatter={(value) => {
                if (period === '1d') {
                  return value;
                }
                return value;
              }}
            />
            <YAxis 
              stroke="#666" 
              fontSize={12} 
              tickLine={false} 
              axisLine={false} 
              tickFormatter={(value) => `$${value.toFixed(2)}`}
              domain={['dataMin - 1', 'dataMax + 1']}
              orientation="right"
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* 현재 가격 참조선 */}
            <ReferenceLine 
              y={currentPrice} 
              stroke={isPositive ? "#10B981" : "#EF4444"} 
              strokeDasharray="3 3"
              label={{ value: currentPrice.toFixed(2), position: 'right', fill: isPositive ? "#10B981" : "#EF4444" }}
            />
            
            {/* 볼륨 바 (하단) */}
            <Bar 
              dataKey="volume" 
              fill={isPositive ? "#10B981" : "#EF4444"} 
              opacity={0.3}
              yAxisId={1}
            />
            
            {/* 차트 타입에 따른 렌더링 */}
            {chartType === 'candle' && (
              <CandlestickChart data={chartData} />
            )}
            
            {chartType === 'area' && (
              <Area 
                type="monotone" 
                dataKey="areaValue" 
                stroke={isPositive ? "#10B981" : "#EF4444"} 
                fill={isPositive ? "#10B981" : "#EF4444"} 
                fillOpacity={0.3}
                strokeWidth={2}
              />
            )}
            
            {chartType === 'line' && (
              <Line 
                type="monotone" 
                dataKey="close" 
                stroke={isPositive ? "#10B981" : "#EF4444"} 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, fill: isPositive ? "#10B981" : "#EF4444" }}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
        
        {/* 줌 컨트롤 */}
        <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 flex space-x-2">
          <button className="w-6 h-6 bg-white border border-gray-300 rounded text-xs flex items-center justify-center hover:bg-gray-50">
            -
          </button>
          <button className="w-6 h-6 bg-white border border-gray-300 rounded text-xs flex items-center justify-center hover:bg-gray-50">
            +
          </button>
        </div>
      </div>
    </div>
  );
};

export default StockChart; 