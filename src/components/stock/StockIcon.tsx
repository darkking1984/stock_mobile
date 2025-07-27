import React from 'react';

interface StockIconProps {
  symbol: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const StockIcon: React.FC<StockIconProps> = ({ symbol, size = 'md', className = '' }) => {
  // 주식별 아이콘 매핑
  const getStockIcon = (ticker: string) => {
    const iconMap: { [key: string]: string } = {
      'AAPL': '🍎',
      'MSFT': '🪟',
      'GOOGL': '🔍',
      'AMZN': '📦',
      'NVDA': '🎮',
      'META': '📘',
      'TSLA': '🚗',
      'BRK-B': '💰',
      'LLY': '💊',
      'TSM': '🔧',
      'V': '💳',
      'JPM': '🏦',
      'JNJ': '💊',
      'PG': '🧴',
      'UNH': '🏥',
      'HD': '🔨',
      'MA': '💳',
      'DIS': '🏰',
      'PYPL': '💳',
      'BAC': '🏦'
    };
    
    return iconMap[ticker] || '📈';
  };

  const sizeClasses = {
    sm: 'text-lg',
    md: 'text-2xl',
    lg: 'text-4xl'
  };

  return (
    <span className={`${sizeClasses[size]} ${className}`}>
      {getStockIcon(symbol.toUpperCase())}
    </span>
  );
};

export default StockIcon; 