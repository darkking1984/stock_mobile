import api from './api';
import { StockInfo, ChartData, ChartPeriod, ChartInterval } from '../types/stock';

export const stockService = {
  // 주식 정보 조회
  async getStockInfo(symbol: string): Promise<any> {
    try {
      console.log(`🔄 Fetching stock info for ${symbol}...`);
      const response = await api.get(`/api/v1/stocks/${symbol}/info`);
      console.log(`✅ Stock info response for ${symbol}:`, response.data);
      console.log(`📊 Stock info data:`, response.data.data);
      return response.data;
    } catch (error) {
      console.error(`❌ Error fetching stock info for ${symbol}:`, error);
      throw error;
    }
  },
  
  // 주식 차트 데이터 조회
  async getStockChart(
    symbol: string,
    period: string = '1y',
    interval: string = '1d'
  ): Promise<any> { // Changed from ApiResponse to any as ApiResponse is no longer imported
    console.log('API call params:', { symbol, period, interval });
    try {
      const response = await api.get(`/api/v1/stocks/${symbol}/chart`, {
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
    } catch (error) {
      console.error('Error fetching stock chart:', error);
      throw error;
    }
  },
  
  // 주식 검색
  async searchStocks(query: string): Promise<any> { // Changed from StockSuggestion to any[]
    try {
      console.log(`🔍 Frontend: Searching for '${query}'`);
      const response = await api.get(`/api/v1/stocks/search`, {
        params: { query }
      });
      console.log(`✅ Frontend: Search response:`, response.data);
      
      // API 응답 구조에 맞게 data 필드 추출
      if (response.data && response.data.success && response.data.data) {
        console.log(`📊 Frontend: Found ${response.data.data.suggestions?.length || 0} suggestions`);
        return response.data.data.suggestions || [];
      } else {
        console.log(`⚠️ Frontend: Invalid response structure:`, response.data);
        return [];
      }
    } catch (error) {
      console.error('❌ Frontend: Error searching stocks:', error);
      throw error;
    }
  },
  
  // 인기 주식 조회
  async getPopularStocks(): Promise<any[]> { // Changed from StockSuggestion to any[]
    try {
      const response = await api.get('/api/v1/stocks/popular');
      return response.data;
    } catch (error) {
      console.error('Error fetching popular stocks:', error);
      throw error;
    }
  },

  // 시가총액 상위 주식 조회
  async getTopMarketCapStocks(): Promise<any> {
    try {
      const apiUrl = '/api/v1/stocks/top-market-cap';
      console.log('🔄 Fetching top market cap stocks from:', apiUrl);
      const response = await api.get(apiUrl);
      console.log('✅ Top market cap stocks response:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Error fetching top market cap stocks:', error);
      throw error;
    }
  },

  // 회사 설명 조회
  async getCompanyDescription(symbol: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/stocks/${symbol}/description`);
      return response.data;
    } catch (error) {
      console.error('Error fetching company description:', error);
      throw error;
    }
  },

  // 지수별 주식 조회
  async getIndexStocks(indexName: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/stocks/index/${indexName}/stocks`);
      return response.data;
    } catch (error) {
      console.error('Error fetching index stocks:', error);
      throw error;
    }
  }
}; 