import { useState, useEffect } from 'react';
import { stockService } from '../services/stockService';
import { StockInfo } from '../types/stock';

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
        console.log('🔄 useStock: Raw stock data:', stockData);
        // API 응답 구조에 맞게 data 필드 추출
        if (stockData && stockData.success && stockData.data) {
          console.log('✅ useStock: Setting stock data:', stockData.data);
          setData(stockData.data);
        } else {
          console.error('❌ useStock: Invalid stock data structure:', stockData);
          setError('Invalid data structure received');
        }
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