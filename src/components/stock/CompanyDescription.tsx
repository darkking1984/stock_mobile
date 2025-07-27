import React, { useState, useEffect } from 'react';
import { stockService } from '../../services/stockService';
import LoadingSpinner from '../common/LoadingSpinner';
import Modal from '../common/Modal';

interface CompanyDescriptionProps {
  symbol: string;
  className?: string;
}

interface CompanyInfo {
  symbol: string;
  name: string;
  shortName: string;
  sector: string;
  industry: string;
  country: string;
  website: string;
  description: string;
  originalDescription: string;
  employees: number;
  founded: string;
  ceo: string;
  headquarters: string;
  marketCap: number;
  enterpriseValue: number;
  revenue: number;
  profitMargin: number;
  operatingMargin: number;
  returnOnEquity: number;
  returnOnAssets: number;
  debtToEquity: number;
  currentRatio: number;
  quickRatio: number;
  cashPerShare: number;
  bookValue: number;
  priceToBook: number;
  priceToSales: number;
  enterpriseToRevenue: number;
  enterpriseToEbitda: number;
}

const CompanyDescription: React.FC<CompanyDescriptionProps> = ({ symbol, className }) => {
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showOriginal, setShowOriginal] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const fetchCompanyDescription = async () => {
      if (!symbol) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await stockService.getCompanyDescription(symbol);
        if (response.success) {
          setCompanyInfo(response.data);
        } else {
          setError('Failed to fetch company description');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch company description');
      } finally {
        setLoading(false);
      }
    };

    fetchCompanyDescription();
  }, [symbol]);

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-xl shadow-lg border border-gray-100 p-6 ${className}`}>
        <div className="flex items-center justify-center h-20">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-xl shadow-lg border border-gray-100 p-6 ${className}`}>
        <div className="text-red-600 text-center">
          Error: {error}
        </div>
      </div>
    );
  }

  if (!companyInfo) {
    return (
      <div className={`bg-white rounded-xl shadow-lg border border-gray-100 p-6 ${className}`}>
        <div className="text-gray-500 text-center">
          회사 정보를 불러올 수 없습니다.
        </div>
      </div>
    );
  }

  const formatNumber = (num: number) => {
    if (!num || isNaN(num) || num <= 0) return '-';
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
  };

  const formatPercentage = (num: number) => {
    if (!num || isNaN(num)) return '-';
    return (num * 100).toFixed(2) + '%';
  };

  // 간단한 카드 형태로 표시
  return (
    <>
      <div className={`bg-white rounded-xl shadow-lg border border-gray-100 p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            회사 정보
          </h3>
          <button
            onClick={handleOpenModal}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 flex items-center space-x-2 text-sm font-medium"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span>상세보기</span>
          </button>
        </div>
        
        {/* 간단한 회사 정보 미리보기 */}
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <div>
              <div className="text-gray-500 text-sm">회사명</div>
              <div className="text-gray-900 font-medium">{companyInfo.name}</div>
            </div>
          </div>
          
          {companyInfo.sector && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <div>
                <div className="text-gray-500 text-sm">섹터</div>
                <div className="text-gray-900 font-medium">{companyInfo.sector}</div>
              </div>
            </div>
          )}
          
          {companyInfo.employees > 0 && (
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              <div>
                <div className="text-gray-500 text-sm">직원 수</div>
                <div className="text-gray-900 font-medium">{companyInfo.employees.toLocaleString()}명</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 상세 정보 모달 */}
      <Modal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        title={`${companyInfo.name} 상세 정보`}
        size="2xl"
      >
        <CompanyDetailContent 
          companyInfo={companyInfo} 
          showOriginal={showOriginal}
          setShowOriginal={setShowOriginal}
        />
      </Modal>
    </>
  );
};

// 상세 정보 내용 컴포넌트
const CompanyDetailContent: React.FC<{
  companyInfo: CompanyInfo;
  showOriginal: boolean;
  setShowOriginal: (show: boolean) => void;
}> = ({ companyInfo, showOriginal, setShowOriginal }) => {
  const formatNumber = (num: number) => {
    if (!num || isNaN(num) || num <= 0) return '-';
    if (num >= 1e12) return (num / 1e12).toFixed(2) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(2) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(2) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(2) + 'K';
    return num.toFixed(2);
  };

  const formatPercentage = (num: number) => {
    if (!num || isNaN(num)) return '-';
    return (num * 100).toFixed(2) + '%';
  };

  return (
    <div className="space-y-8">
      {/* 헤더 섹션 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 px-6 py-4 rounded-xl border border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-1">{companyInfo.name}</h2>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              {companyInfo.sector && (
                <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                  {companyInfo.sector}
                </span>
              )}
              {companyInfo.industry && (
                <span className="bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full text-xs font-medium">
                  {companyInfo.industry}
                </span>
              )}
              {companyInfo.country && (
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                  {companyInfo.country}
                </span>
              )}
            </div>
          </div>
          {companyInfo.website && (
            <a 
              href={companyInfo.website} 
              target="_blank" 
              rel="noopener noreferrer"
              className="bg-white hover:bg-gray-50 text-blue-600 hover:text-blue-700 px-4 py-2 rounded-lg border border-gray-200 transition-all duration-200 flex items-center space-x-2 text-sm font-medium"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              <span>웹사이트</span>
            </a>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 회사 설명 - 왼쪽 */}
        {companyInfo.description && (
          <div className="lg:col-span-1">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  회사 소개
                </h3>
                {companyInfo.originalDescription && (
                  <button
                    onClick={() => setShowOriginal(!showOriginal)}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium flex items-center space-x-1 transition-colors duration-200"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                    </svg>
                    <span>{showOriginal ? '한글 보기' : '영어 원문 보기'}</span>
                  </button>
                )}
              </div>
              <div className="bg-gradient-to-r from-gray-50 to-blue-50 rounded-xl p-6 border border-gray-100">
                <p className="text-gray-700 leading-relaxed text-sm">
                  {showOriginal ? companyInfo.originalDescription : companyInfo.description}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* 기본정보/재무정보/재무비율 - 오른쪽 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 기본 정보 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
              기본 정보
            </h3>
            <div className="grid grid-cols-1 gap-3">
              {companyInfo.employees > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-500 text-sm font-medium">직원 수</div>
                      <div className="text-gray-900 font-semibold text-lg">{companyInfo.employees.toLocaleString()}명</div>
                    </div>
                  </div>
                </div>
              )}
              {companyInfo.founded && companyInfo.founded.trim() !== '' && (
                <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-500 text-sm font-medium">설립년도</div>
                      <div className="text-gray-900 font-semibold text-lg">{companyInfo.founded}</div>
                    </div>
                  </div>
                </div>
              )}
              {companyInfo.ceo && companyInfo.ceo.trim() !== '' && (
                <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-500 text-sm font-medium">CEO</div>
                      <div className="text-gray-900 font-semibold text-lg truncate">{companyInfo.ceo}</div>
                    </div>
                  </div>
                </div>
              )}
              {companyInfo.headquarters && companyInfo.headquarters.trim() !== '' && (
                <div className="bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-500 text-sm font-medium">본사</div>
                      <div className="text-gray-900 font-semibold text-sm truncate">{companyInfo.headquarters}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 재무 정보 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
              재무 정보
            </h3>
            <div className="grid grid-cols-1 gap-3">
              {companyInfo.marketCap > 0 && (
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-700 text-sm font-medium">시가총액</div>
                      <div className="font-bold text-green-700 text-lg">${formatNumber(companyInfo.marketCap)}</div>
                    </div>
                  </div>
                </div>
              )}
              {companyInfo.revenue > 0 && (
                <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl border border-blue-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-700 text-sm font-medium">매출</div>
                      <div className="font-bold text-blue-700 text-lg">${formatNumber(companyInfo.revenue)}</div>
                    </div>
                  </div>
                </div>
              )}
              {companyInfo.profitMargin > 0 && (
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-purple-200 p-4 hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-gray-700 text-sm font-medium">순이익률</div>
                      <div className="font-bold text-purple-700 text-lg">{formatPercentage(companyInfo.profitMargin)}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 재무 비율 */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              재무 비율
            </h3>
            <div className="grid grid-cols-2 gap-3">
              {companyInfo.returnOnEquity > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">ROE</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-blue-600 transition-colors duration-200">
                    {formatPercentage(companyInfo.returnOnEquity)}
                  </div>
                </div>
              )}
              {companyInfo.returnOnAssets > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">ROA</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-green-600 transition-colors duration-200">
                    {formatPercentage(companyInfo.returnOnAssets)}
                  </div>
                </div>
              )}
              {companyInfo.debtToEquity > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">부채비율</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-red-600 transition-colors duration-200">
                    {companyInfo.debtToEquity.toFixed(2)}
                  </div>
                </div>
              )}
              {companyInfo.currentRatio > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">유동비율</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-purple-600 transition-colors duration-200">
                    {companyInfo.currentRatio.toFixed(2)}
                  </div>
                </div>
              )}
              {companyInfo.priceToBook > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">P/B</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-yellow-600 transition-colors duration-200">
                    {companyInfo.priceToBook.toFixed(2)}
                  </div>
                </div>
              )}
              {companyInfo.priceToSales > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">P/S</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-indigo-600 transition-colors duration-200">
                    {companyInfo.priceToSales.toFixed(2)}
                  </div>
                </div>
              )}
              {companyInfo.cashPerShare > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">현금/주</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-emerald-600 transition-colors duration-200">
                    ${companyInfo.cashPerShare.toFixed(2)}
                  </div>
                </div>
              )}
              {companyInfo.bookValue > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-3 hover:shadow-md transition-all duration-200 text-center group">
                  <div className="text-gray-500 text-xs mb-2 font-medium">BPS</div>
                  <div className="font-bold text-lg text-gray-900 group-hover:text-pink-600 transition-colors duration-200">
                    ${companyInfo.bookValue.toFixed(2)}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyDescription; 