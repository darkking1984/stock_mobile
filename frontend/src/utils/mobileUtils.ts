// 모바일 환경 감지 및 디버깅 유틸리티

export const isMobile = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

export const isIOS = (): boolean => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent);
};

export const isAndroid = (): boolean => {
  return /Android/.test(navigator.userAgent);
};

// 모바일 환경에서의 네트워크 상태 확인
export const checkNetworkStatus = async (): Promise<boolean> => {
  try {
    const response = await fetch('/api/v1/health', { 
      method: 'HEAD',
      cache: 'no-cache'
    });
    return response.ok;
  } catch (error) {
    console.error('Network check failed:', error);
    return false;
  }
};

// 모바일 환경에서의 로컬스토리지 지원 확인
export const isLocalStorageSupported = (): boolean => {
  try {
    const test = 'test';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch (e) {
    return false;
  }
};

// 모바일 환경에서의 쿠키 지원 확인
export const isCookieSupported = (): boolean => {
  try {
    document.cookie = 'test=1';
    const hasCookie = document.cookie.indexOf('test=') !== -1;
    document.cookie = 'test=1; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    return hasCookie;
  } catch (e) {
    return false;
  }
};

// 모바일 환경에서의 디버깅 정보 출력
export const logMobileDebugInfo = (): void => {
  console.group('📱 Mobile Debug Info');
  console.log('User Agent:', navigator.userAgent);
  console.log('Is Mobile:', isMobile());
  console.log('Is iOS:', isIOS());
  console.log('Is Android:', isAndroid());
  console.log('Local Storage Supported:', isLocalStorageSupported());
  console.log('Cookie Supported:', isCookieSupported());
  console.log('Current URL:', window.location.href);
  console.log('Hostname:', window.location.hostname);
  console.log('Protocol:', window.location.protocol);
  console.groupEnd();
};

// 안전한 DOM 조작을 위한 유틸리티
export const safeDOMOperation = (operation: () => void): void => {
  try {
    // DOM이 준비되었는지 확인
    if (typeof window !== 'undefined' && document.readyState === 'complete') {
      operation();
    } else {
      // DOM이 준비되지 않았으면 이벤트 리스너 추가
      window.addEventListener('load', operation, { once: true });
    }
  } catch (error) {
    console.warn('Safe DOM operation failed:', error);
  }
};

// 모바일 환경에서의 API 요청 실패 시 재시도 로직
export const retryApiRequest = async <T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> => {
  let lastError: Error;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error as Error;
      console.warn(`API request failed (attempt ${i + 1}/${maxRetries}):`, error);
      
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
      }
    }
  }
  
  throw lastError!;
}; 