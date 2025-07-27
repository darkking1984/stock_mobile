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
        setData(stockData);
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