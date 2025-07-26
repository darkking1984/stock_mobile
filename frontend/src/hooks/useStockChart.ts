import { useState, useEffect } from 'react';
import { stockService } from '../services/stockService';
import { ChartPeriod, ChartInterval } from '../types/stock';

export const useStockChart = (
  symbol: string,
  period: ChartPeriod = '1y',
  interval: ChartInterval = '1d'
) => {
  const [data, setData] = useState<any[]>([]); // Changed type to any[] as ChartData is removed
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('useStockChart: useEffect triggered with symbol:', symbol, 'period:', period, 'interval:', interval);
    
    const fetchChartData = async () => {
      if (!symbol) {
        console.log('useStockChart: No symbol provided, returning');
        return;
      }
      
      console.log('useStockChart: Starting to fetch data');
      setLoading(true);
      setError(null);
      
      try {
        console.log('useStockChart: Fetching data for', symbol, period, interval);
        const response = await stockService.getStockChart(symbol, period, interval);
        console.log('useStockChart: Raw response', response);
        
        if (response && response.success && response.data && response.data.data && Array.isArray(response.data.data)) {
          console.log('useStockChart: Setting data', response.data.data);
          console.log('useStockChart: Data length:', response.data.data.length);
          
          // 빈 배열인 경우 처리
          if (response.data.data.length === 0) {
            console.log('useStockChart: Empty data array');
            setData([]);
            return;
          }
          
          console.log('useStockChart: First data point', response.data.data[0]);
          console.log('useStockChart: First data point keys:', Object.keys(response.data.data[0]));
          console.log('useStockChart: First data point values:', Object.values(response.data.data[0]));
          // Data re-validation
          const validData = response.data.data.filter((point: any) => {
            return point &&
                   typeof point.timestamp === 'string' &&
                   typeof point.open === 'number' &&
                   typeof point.high === 'number' &&
                   typeof point.low === 'number' &&
                   typeof point.close === 'number' &&
                   typeof point.volume === 'number';
          });
          console.log('useStockChart: Valid data after filtering:', validData.length);
          if (validData.length > 0) {
            console.log('useStockChart: Sample valid data:', validData[0]);
          }
          setData(validData);
        } else {
          console.error('useStockChart: Invalid response structure', response);
          setError('Invalid chart data structure');
        }
      } catch (err) {
        console.error('useStockChart: Error fetching data', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch chart data');
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [symbol, period, interval]);

  return { data, loading, error };
}; 