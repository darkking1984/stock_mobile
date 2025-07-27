import React from 'react';
import { StockInfo } from '../../types/stock';

interface InfoCardProps {
  stock: StockInfo;
  className?: string;
}

const InfoCard: React.FC<InfoCardProps> = ({ stock, className }) => {
  const formatValue = (value: any, formatter?: (val: any) => string) => {
    if (value === null || value === undefined || value === 0) return '-';
    return formatter ? formatter(value) : value.toString();
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;
  const formatMarketCap = (value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
    return `$${value.toLocaleString()}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">기본 정보</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-gray-500">회사명</div>
            <div className="text-sm text-gray-900">{stock.name}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">거래소</div>
            <div className="text-sm text-gray-900">{stock.exchange}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">섹터</div>
            <div className="text-sm text-gray-900">{formatValue(stock.sector)}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">산업</div>
            <div className="text-sm text-gray-900">{formatValue(stock.industry)}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">통화</div>
            <div className="text-sm text-gray-900">{stock.currency}</div>
          </div>
        </div>
        
        <div className="space-y-3">
          <div>
            <div className="text-sm font-medium text-gray-500">시가총액</div>
            <div className="text-sm text-gray-900">{formatValue(stock.marketCap, formatMarketCap)}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">PER</div>
            <div className="text-sm text-gray-900">{formatValue(stock.peRatio)}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">배당수익률</div>
            <div className="text-sm text-gray-900">{formatValue(stock.dividendYield, formatPercentage)}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">베타</div>
            <div className="text-sm text-gray-900">{formatValue(stock.beta)}</div>
          </div>
          
          <div>
            <div className="text-sm font-medium text-gray-500">52주 범위</div>
            <div className="text-sm text-gray-900">
              {formatValue(stock.fiftyTwoWeekLow, formatCurrency)} - {formatValue(stock.fiftyTwoWeekHigh, formatCurrency)}
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="font-medium text-gray-500">평균 거래량</div>
            <div className="text-gray-900">{formatValue(stock.avgVolume, (val) => val.toLocaleString())}</div>
          </div>
          <div>
            <div className="font-medium text-gray-500">전일 종가</div>
            <div className="text-gray-900">{formatValue(stock.previousClose, formatCurrency)}</div>
          </div>
          <div>
            <div className="font-medium text-gray-500">오늘 고가</div>
            <div className="text-gray-900">{formatValue(stock.high, formatCurrency)}</div>
          </div>
          <div>
            <div className="font-medium text-gray-500">오늘 저가</div>
            <div className="text-gray-900">{formatValue(stock.low, formatCurrency)}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InfoCard; 