import React from 'react';
import { StockInfo } from '../../types/stock';

interface PriceCardProps {
  stock: StockInfo;
  className?: string;
}

const PriceCard: React.FC<PriceCardProps> = ({ stock, className }) => {
  const isPositive = stock.change > 0;
  const isNegative = stock.change < 0;

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-4 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900">{stock.symbol}</h3>
        <span className="text-sm text-gray-500">{stock.exchange}</span>
      </div>
      
      <div className="mb-3">
        <div className="text-2xl font-bold text-gray-900">
          ${stock.currentPrice?.toLocaleString()}
        </div>
        <div className="text-sm text-gray-500">{stock.name}</div>
      </div>

      <div className="flex items-center justify-between">
        <div className={`text-lg font-semibold ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'}`}>
          {isPositive ? '+' : ''}{stock.change?.toFixed(2)}
        </div>
        <div className={`text-sm font-medium ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'}`}>
          {isPositive ? '+' : ''}{stock.changePercent?.toFixed(2)}%
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
          <div>
            <span className="font-medium">고가:</span> ${stock.high?.toLocaleString()}
          </div>
          <div>
            <span className="font-medium">저가:</span> ${stock.low?.toLocaleString()}
          </div>
          <div>
            <span className="font-medium">거래량:</span> {stock.volume?.toLocaleString()}
          </div>
          <div>
            <span className="font-medium">시총:</span> {stock.marketCap ? (stock.marketCap / 1e9).toFixed(1) + 'B' : '-'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PriceCard; 