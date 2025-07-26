import React, { useState, useEffect, useCallback } from 'react';
import { stockService } from '../../services/stockService';
import StockIcon from './StockIcon';
import LoadingSpinner from '../common/LoadingSpinner';

interface TopStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  marketCap: number;
  volume: number;
}

interface TopStocksGridProps {
  onStockSelect: (symbol: string) => void;
  className?: string;
}

// 지수 정보 정의
const INDEX_INFO = {
  all: { name: '전체', label: '시가총액 상위 10개 주식' },
  dow: { name: '다우존스', label: '다우존스 상위 10개 주식' },
  nasdaq: { name: '나스닥', label: '나스닥 상위 10개 주식' },
  sp500: { name: 'S&P 500', label: 'S&P 500 상위 10개 주식' },
  russell2000: { name: '러셀 2000', label: '러셀 2000 상위 10개 주식' }
};

// 메모리 캐시 인터페이스
interface CacheData {
  data: TopStock[];
  timestamp: Date;
  loading: boolean;
}

const TopStocksGrid: React.FC<TopStocksGridProps> = ({ onStockSelect, className = '' }) => {
  const [topStocks, setTopStocks] = useState<TopStock[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState<string>('all');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  
  // 메모리 캐시 (5분 유효)
  const [cache, setCache] = useState<Record<string, CacheData>>({});
  const CACHE_DURATION = 5 * 60 * 1000; // 5분

  const isCacheValid = useCallback((cacheData: CacheData) => {
    return (Date.now() - cacheData.timestamp.getTime()) < CACHE_DURATION;
  }, []);

  const fetchStocks = useCallback(async (indexName: string) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`Fetching stocks for index: ${indexName}`);
      
      let response;
      if (indexName === 'all') {
        response = await stockService.getTopMarketCapStocks();
      } else {
        response = await stockService.getIndexStocks(indexName);
      }
      
      if (response.success) {
        const stockData = response.data;
        setTopStocks(stockData);
        setLastUpdated(new Date());
        
        // 캐시에 저장
        setCache(prev => ({
          ...prev,
          [indexName]: {
            data: stockData,
            timestamp: new Date(),
            loading: false
          }
        }));
        
        console.log(`Successfully fetched ${stockData.length} stocks for ${indexName}`);
      } else {
        setError('Failed to fetch stocks');
      }
    } catch (err) {
      console.error('Error fetching stocks:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch stocks';
      setError(errorMessage);
      
      // 타임아웃 에러인 경우 특별 메시지
      if (errorMessage.includes('timeout')) {
        setError('데이터 로딩 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const handleIndexChange = useCallback(async (indexName: string) => {
    setSelectedIndex(indexName);
    setError(null);
    
    // 캐시 확인
    const cachedData = cache[indexName];
    
    if (cachedData && isCacheValid(cachedData)) {
      // 유효한 캐시가 있으면 캐시에서 로드
      console.log(`Loading from cache for ${indexName}`);
      setTopStocks(cachedData.data);
      setLastUpdated(cachedData.timestamp);
      setLoading(false);
    } else {
      // 캐시가 없거나 만료되었으면 새로 가져오기
      console.log(`Cache miss for ${indexName}, fetching new data`);
      
      // 로딩 상태를 캐시에 저장
      setCache(prev => ({
        ...prev,
        [indexName]: {
          data: [],
          timestamp: new Date(),
          loading: true
        }
      }));
      
      await fetchStocks(indexName);
    }
  }, [cache, isCacheValid, fetchStocks]);

  const handleManualRefresh = useCallback(async () => {
    // 캐시 무시하고 새로 가져오기
    console.log(`Manual refresh for ${selectedIndex}`);
    await fetchStocks(selectedIndex);
  }, [selectedIndex, fetchStocks]);

  // 초기 로드
  useEffect(() => {
    handleIndexChange('all');
  }, []); // 컴포넌트 마운트 시에만 실행

  const formatNumber = (num: number) => {
    if (!num || isNaN(num)) return '-';
    if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    return num.toFixed(0);
  };

  const formatPrice = (price: number) => {
    return price ? `$${price.toFixed(2)}` : '-';
  };

  const formatChange = (change: number, changePercent: number) => {
    if (!change || isNaN(change)) return '-';
    const sign = change >= 0 ? '+' : '';
    return `${sign}$${change.toFixed(2)} (${sign}${changePercent.toFixed(2)}%)`;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // 현재 선택된 지수의 캐시 상태 확인
  const currentCacheData = cache[selectedIndex];
  const isLoading = loading || (currentCacheData?.loading ?? false);

  if (isLoading) {
    return (
      <div className={`${className}`}>
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {Object.entries(INDEX_INFO).map(([key, info]) => (
              <button
                key={key}
                onClick={() => handleIndexChange(key)}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  selectedIndex === key
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {info.name}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {INDEX_INFO[selectedIndex as keyof typeof INDEX_INFO]?.label}
          </h2>
        </div>
        
        <div className="flex items-center justify-center h-40 bg-white rounded-lg border border-gray-200">
          <div className="text-center">
            <LoadingSpinner />
            <p className="mt-4 text-gray-600">주식 데이터를 불러오는 중...</p>
            <p className="text-sm text-gray-500">잠시만 기다려주세요</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className}`}>
        <div className="mb-6">
          <div className="flex flex-wrap gap-2">
            {Object.entries(INDEX_INFO).map(([key, info]) => (
              <button
                key={key}
                onClick={() => handleIndexChange(key)}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                  selectedIndex === key
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {info.name}
              </button>
            ))}
          </div>
        </div>
        
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            {INDEX_INFO[selectedIndex as keyof typeof INDEX_INFO]?.label}
          </h2>
          <button
            onClick={handleManualRefresh}
            className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>다시 시도</span>
          </button>
        </div>
        
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <div className="flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-red-800 mb-2">데이터 로딩 실패</h3>
          <p className="text-red-700 mb-4">{error}</p>
          <button
            onClick={handleManualRefresh}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`${className} relative`}>
      {/* 지수 선택 탭 */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          {Object.entries(INDEX_INFO).map(([key, info]) => (
            <button
              key={key}
              onClick={() => handleIndexChange(key)}
              className={`px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                selectedIndex === key
                  ? 'bg-blue-600 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {info.name}
            </button>
          ))}
        </div>
      </div>

      {/* 데이터 표시 영역 */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-900">
          {INDEX_INFO[selectedIndex as keyof typeof INDEX_INFO]?.label}
        </h2>
        <div className="flex items-center space-x-4">
          {lastUpdated && (
            <div className="text-sm text-gray-500">
              마지막 업데이트: {formatTime(lastUpdated)}
            </div>
          )}
          <button
            onClick={handleManualRefresh}
            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>새로고침</span>
          </button>
        </div>
      </div>

      {/* 주식 그리드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 min-h-[120px]">
        {topStocks.length === 0 && !loading && !error && (
          <div className="col-span-full flex flex-col items-center justify-center py-8">
            <div className="text-gray-400 mb-2">데이터가 없습니다.</div>
          </div>
        )}
        {topStocks.slice(0, 10).map((stock, index) => (
          <div
            key={stock.symbol}
            onClick={() => onStockSelect(stock.symbol)}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-lg hover:border-blue-400 hover:scale-105 transition-all duration-200 cursor-pointer group relative"
            title={`${stock.symbol} 상세정보 보기`}
          >
            {/* 클릭 힌트 오버레이 */}
            <div className="absolute inset-0 bg-blue-500 bg-opacity-0 group-hover:bg-opacity-5 rounded-lg transition-all duration-200 pointer-events-none"></div>
            
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <StockIcon symbol={stock.symbol} size="sm" />
                <div>
                  <div className="font-bold text-gray-900 group-hover:text-blue-600 transition-colors duration-200">{stock.symbol}</div>
                  <div className="text-xs text-gray-500 truncate max-w-20">
                    {stock.name}
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-400">#{index + 1}</div>
            </div>
            
            <div className="space-y-1">
              <div className="text-lg font-semibold text-gray-900">
                {formatPrice(stock.price)}
              </div>
              <div className={`text-sm font-medium ${
                stock.change >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatChange(stock.change, stock.changePercent)}
              </div>
              <div className="text-xs text-gray-500">
                시총: ${formatNumber(stock.marketCap)}
              </div>
            </div>
            
            {/* 클릭 힌트 아이콘 */}
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
              <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </div>
          </div>
        ))}
      </div>

      {/* 로딩 오버레이 */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-60 z-10">
          <LoadingSpinner />
          <span className="ml-3 text-gray-600">주식 데이터를 불러오는 중...</span>
        </div>
      )}

      {/* 에러 메시지 */}
      {error && (
        <div className="col-span-full flex flex-col items-center justify-center py-8">
          <div className="text-red-600 font-semibold mb-2">{error}</div>
          <button
            onClick={handleManualRefresh}
            className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200"
          >
            다시 시도
          </button>
        </div>
      )}
    </div>
  );
};

export default TopStocksGrid; 