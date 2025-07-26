import axios, { AxiosResponse, AxiosError } from 'axios';

// 모바일과 데스크톱 모두에서 접근 가능하도록 설정
const getApiBaseUrl = () => {
  // 환경 변수가 설정되어 있으면 사용
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // 개발 환경에서는 현재 호스트의 IP를 사용 (모바일 호환)
  if (process.env.NODE_ENV === 'development') {
    const hostname = window.location.hostname;
    const port = '8000'; // 백엔드 포트
    return `http://${hostname}:${port}`;
  }
  
  // 프로덕션 환경에서는 상대 경로 사용
  return '';
};

const API_BASE_URL = getApiBaseUrl();

console.log('API Base URL:', API_BASE_URL);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30초로 증가
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터
api.interceptors.request.use(
  (config) => {
    console.log(`Making request to: ${config.method?.toUpperCase()} ${config.url}`);
    // 로딩 상태 관리
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 응답 인터셉터
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`Response received from: ${response.config.url}`, response.status);
    return response;
  },
  async (error: AxiosError) => {
    console.error('Response error:', error);
    
    // 타임아웃 에러인 경우 재시도 로직
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      console.log('Request timeout, retrying...');
      
      // 원본 요청 설정 복원
      const originalRequest = error.config;
      if (originalRequest) {
        try {
          // 3초 후 재시도
          await new Promise(resolve => setTimeout(resolve, 3000));
          return api.request(originalRequest);
        } catch (retryError) {
          console.error('Retry failed:', retryError);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export default api; 