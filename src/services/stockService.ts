import api from './api';
import { StockInfo, ChartData, ChartPeriod, ChartInterval } from '../types/stock';

export const stockService = {
  async getStockInfo(symbol: string): Promise<StockInfo> {
    const response = await api.get(`/api/v1/stock/${symbol}/info`);
    return response.data.data;
  },
  
  async getStockChart(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> { // Changed from ApiResponse to any as ApiResponse is no longer imported
    console.log('API call params:', { symbol, period, interval });
    const response = await api.get(`/api/v1/stock/${symbol}/chart`, {
      params: { period, interval }
    });
    
    console.log('Raw API response:', response);
    console.log('Response data:', response.data);
    console.log('Response data type:', typeof response.data);
    console.log('Response data keys:', Object.keys(response.data));
    
    // 응답 데이터 구조 확인 및 새로운 객체 생성
    if (response.data && response.data.success && response.data.data) {
      console.log('Response data.data:', response.data.data);
      console.log('Response data.data type:', typeof response.data.data);
      console.log('Response data.data keys:', Object.keys(response.data.data));
      
      if (response.data.data.data) {
        console.log('Response data.data.data:', response.data.data.data);
        console.log('Response data.data.data type:', typeof response.data.data.data);
        console.log('Response data.data.data length:', response.data.data.data?.length);
        
        if (Array.isArray(response.data.data.data) && response.data.data.data.length > 0) {
          console.log('First data point:', response.data.data.data[0]);
          console.log('First data point keys:', Object.keys(response.data.data.data[0]));
          console.log('First data point values:', Object.values(response.data.data.data[0]));
          
          // 데이터 유효성 검사
          const validData = response.data.data.data.filter((point: any) => {
            const isValid = point && 
                          typeof point.timestamp === 'string' &&
                          typeof point.open === 'number' &&
                          typeof point.high === 'number' &&
                          typeof point.low === 'number' &&
                          typeof point.close === 'number' &&
                          typeof point.volume === 'number';
            
            if (!isValid) {
              console.warn('Invalid data point:', point);
            }
            return isValid;
          });
          
          console.log('Valid data points:', validData.length);
          if (validData.length > 0) {
            console.log('Sample valid data point:', validData[0]);
          }
          
          // 새로운 응답 객체 생성 (원본 객체 수정 대신)
          const newResponse = {
            success: response.data.success,
            data: {
              symbol: response.data.data.symbol,
              period: response.data.data.period,
              interval: response.data.data.interval,
              data: validData
            },
            message: response.data.message,
            timestamp: response.data.timestamp
          };
          
          console.log('New response object:', newResponse);
          console.log('New response data length:', newResponse.data.data.length);
          
          return newResponse;
        }
      }
    }
    
    // 백엔드 응답 구조: { success: true, data: { symbol, period, interval, data: [...] } }
    return response.data;
  },
  
  async searchStocks(query: string): Promise<any[]> { // Changed from StockSuggestion to any[]
    const response = await api.get(`/api/v1/stock/search`, {
      params: { query }
    });
    return response.data.data.suggestions;
  },
  
  async getPopularStocks(): Promise<any[]> { // Changed from StockSuggestion to any[]
    const response = await api.get('/api/v1/stock/popular');
    return response.data.data;
  },

  getTopMarketCapStocks: async (): Promise<any> => {
    try {
      const response = await api.get('/api/v1/stock/top-market-cap');
      return response.data;
    } catch (error) {
      console.error('Error fetching top market cap stocks:', error);
      throw error;
    }
  },

  // 회사 상세설명 조회
  async getCompanyDescription(symbol: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/stock/${symbol}/description`);
      return response.data;
    } catch (error) {
      console.error('Error fetching company description:', error);
      throw error;
    }
  },

  // 지수별 주식 데이터 조회
  async getIndexStocks(indexName: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/stock/index/${indexName}/stocks`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${indexName} stocks:`, error);
      throw error;
    }
  }
}; 