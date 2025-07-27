import React from 'react';
import { useStock } from '../../hooks/useStock';
import LoadingSpinner from '../common/LoadingSpinner';

interface StockInfoProps {
  symbol: string;
  className?: string;
}

const StockInfo: React.FC<StockInfoProps> = ({ symbol, className }) => {
  const { data, loading, error } = useStock(symbol);

  if (loading) {
    return (
      <div className={`flex items-center justify-center h-40 ${className}`}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={`text-red-600 p-4 ${className}`}>Error: {error}</div>
    );
  }

  if (!data) {
    return null;
  }

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{data.name} <span className="text-gray-500 text-lg">({data.symbol})</span></h2>
          <div className="text-sm text-gray-500 mt-1">{data.exchange} | {data.sector} | {data.industry}</div>
        </div>
        <div className="mt-4 md:mt-0">
          <span className="text-3xl font-bold text-gray-900">{data.currentPrice?.toLocaleString()} {data.currency}</span>
          <span className={`ml-3 text-lg font-semibold ${data.change > 0 ? 'text-green-600' : data.change < 0 ? 'text-red-600' : 'text-gray-600'}`}>
            {data.change > 0 ? '+' : ''}{data.change.toFixed(2)} ({data.changePercent.toFixed(2)}%)
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-700">
        <div>
          <div className="font-semibold">고가</div>
          <div>{data.high?.toLocaleString()}</div>
        </div>
        <div>
          <div className="font-semibold">저가</div>
          <div>{data.low?.toLocaleString()}</div>
        </div>
        <div>
          <div className="font-semibold">전일종가</div>
          <div>{data.previousClose?.toLocaleString()}</div>
        </div>
        <div>
          <div className="font-semibold">거래량</div>
          <div>{data.volume?.toLocaleString()}</div>
        </div>
        <div>
          <div className="font-semibold">시가총액</div>
          <div>{data.marketCap ? data.marketCap.toLocaleString() : '-'}</div>
        </div>
        <div>
          <div className="font-semibold">PER</div>
          <div>{data.peRatio ?? '-'}</div>
        </div>
        <div>
          <div className="font-semibold">배당수익률</div>
          <div>{data.dividendYield ? (data.dividendYield * 100).toFixed(2) + '%' : '-'}</div>
        </div>
        <div>
          <div className="font-semibold">52주 최고/최저</div>
          <div>{data.fiftyTwoWeekHigh?.toLocaleString()} / {data.fiftyTwoWeekLow?.toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
};

export default StockInfo; 