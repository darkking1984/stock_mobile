import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { logMobileDebugInfo, retryApiRequest } from '../utils/mobileUtils';

interface User {
  id: number;
  username: string;
  email?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string, secureLogin?: boolean) => Promise<boolean>;
  register: (username: string, password: string, email?: string) => Promise<boolean>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(false);
  const [isMounted, setIsMounted] = useState(true);

  // 컴포넌트 마운트/언마운트 관리
  useEffect(() => {
    setIsMounted(true);
    return () => {
      setIsMounted(false);
    };
  }, []);

  // 토큰이 있으면 사용자 정보 가져오기
  useEffect(() => {
    if (token && isMounted) {
      // 모바일 디버깅 정보 출력
      logMobileDebugInfo();
      fetchUserInfo();
    }
  }, [token, isMounted]);

  // 디버깅 로그 추가
  useEffect(() => {
    console.log('=== AuthContext API Configuration ===');
    console.log('NODE_ENV:', process.env.NODE_ENV);
    console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    console.log('AuthContext getApiUrl():', getApiUrl());
    console.log('Current URL:', window.location.href);
    console.log('===================================');
  }, []);

  // API 기본 URL 설정 - 모바일 호환
  const getApiUrl = () => {
    // 프로덕션 환경에서는 항상 Render 백엔드 URL 사용
    if (process.env.NODE_ENV === 'production') {
      return 'https://stock-backend-6e1s.onrender.com';
    }
    
    // 환경 변수가 설정되어 있으면 사용
    if (process.env.REACT_APP_API_URL) {
      return process.env.REACT_APP_API_URL;
    }
    
    // 개발 환경에서는 현재 호스트의 IP를 사용
    const hostname = window.location.hostname;
    const port = '8000'; // 백엔드 포트
    return `http://${hostname}:${port}`;
  };

  const fetchUserInfo = async () => {
    const fetchUserData = async () => {
      // 컴포넌트가 언마운트되었으면 중단
      if (!isMounted) {
        console.log('Component unmounted, aborting fetchUserInfo');
        return;
      }

      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/v1/auth/me`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      });
      
      if (response.ok) {
        const userData = await response.json();
        // 컴포넌트가 여전히 마운트되어 있는지 확인
        if (isMounted) {
          setUser(userData);
        }
      } else {
        console.error('Failed to fetch user info:', response.status, response.statusText);
        // 토큰이 유효하지 않으면 로그아웃 (마운트된 상태에서만)
        if (isMounted) {
          logout();
        }
      }
    };

    try {
      // 모바일 환경에서 재시도 로직 적용
      await retryApiRequest(fetchUserData, 3, 1000);
    } catch (error) {
      console.error('Failed to fetch user info after retries:', error);
      // 컴포넌트가 마운트된 상태에서만 로그아웃
      if (isMounted) {
        logout();
      }
    }
  };

  const login = async (username: string, password: string, secureLogin: boolean = false): Promise<boolean> => {
    setIsLoading(true);
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ username, password, secureLogin }),
      });

      if (response.ok) {
        const data = await response.json();
        setToken(data.access_token);
        setUser(data.user);
        localStorage.setItem('token', data.access_token);
        return true;
      } else {
        const errorData = await response.json();
        alert(errorData.detail || '로그인에 실패했습니다.');
        return false;
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('로그인 중 오류가 발생했습니다.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (username: string, password: string, email?: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ username, password, email }),
      });

      if (response.ok) {
        const userData = await response.json();
        alert('회원가입이 완료되었습니다. 로그인해주세요.');
        return true;
      } else {
        const errorData = await response.json();
        alert(errorData.detail || '회원가입에 실패했습니다.');
        return false;
      }
    } catch (error) {
      console.error('Register error:', error);
      alert('회원가입 중 오류가 발생했습니다.');
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    isLoading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 