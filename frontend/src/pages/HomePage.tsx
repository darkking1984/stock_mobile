import React, { useState } from 'react';
import StockSearch from '../components/stock/StockSearch';
import StockChart from '../components/charts/StockChart';
import PriceCard from '../components/stock/PriceCard';
import InfoCard from '../components/stock/InfoCard';
import CompanyDescription from '../components/stock/CompanyDescription';
import TopStocksGrid from '../components/stock/TopStocksGrid';
import { useStock } from '../hooks/useStock';

const HomePage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');

  const handleStockSelect = (symbol: string) => {
    setSelectedSymbol(symbol);
    
    // 상세정보 섹션으로 부드럽게 스크롤
    setTimeout(() => {
      const detailSection = document.getElementById('stock-detail-section');
      if (detailSection) {
        detailSection.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        });
      }
    }, 100); // 약간의 지연을 두어 상태 업데이트 후 스크롤 실행
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
            미국 주식 정보 대시보드
          </h1>

          <div className="mb-8">
            <StockSearch
              onSearch={() => {}}
              onSelect={handleStockSelect}
              placeholder="종목명 또는 티커 검색..."
            />
          </div>

          {/* 선택된 주식의 상세 정보 (위쪽에 표시) */}
          {selectedSymbol && (
            <div id="stock-detail-section" className="mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-semibold text-gray-800">
                  {selectedSymbol} 상세 정보
                </h2>
                <button
                  onClick={() => {
                    const marketCapSection = document.getElementById('market-cap-section');
                    if (marketCapSection) {
                      marketCapSection.scrollIntoView({ 
                        behavior: 'smooth', 
                        block: 'start' 
                      });
                    }
                  }}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition-colors duration-200 flex items-center space-x-2"
                  title="시가총액 상위 주식 목록으로 이동"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0l-4-4m4 4l-4 4m4-4v6a2 2 0 01-2 2H7a2 2 0 01-2-2V9a2 2 0 012-2h10a2 2 0 012 2v2z" />
                  </svg>
                  <span>시가총액 목록</span>
                </button>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                <div className="lg:col-span-1">
                  <StockDetailSection symbol={selectedSymbol} />
                </div>
                <div className="lg:col-span-2">
                  <StockChart symbol={selectedSymbol} />
                </div>
              </div>
            </div>
          )}

          {/* 시가총액 상위 주식 그리드 (항상 하단에 표시) */}
          <div id="market-cap-section">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-800">
                시가총액 상위 10개 주식
              </h2>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>항목을 클릭하면 상세정보로 이동합니다</span>
                </div>
                {selectedSymbol && (
                  <button
                    onClick={() => {
                      const detailSection = document.getElementById('stock-detail-section');
                      if (detailSection) {
                        detailSection.scrollIntoView({ 
                          behavior: 'smooth', 
                          block: 'start' 
                        });
                      }
                    }}
                    className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-lg text-sm font-medium transition-colors duration-200 flex items-center space-x-2"
                    title={`${selectedSymbol} 상세정보로 돌아가기`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span>{selectedSymbol} 상세정보</span>
                  </button>
                )}
              </div>
            </div>
            <TopStocksGrid 
              onStockSelect={handleStockSelect}
              className="mb-8"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// 선택된 종목의 상세 정보를 보여주는 컴포넌트
const StockDetailSection: React.FC<{ symbol: string }> = ({ symbol }) => {
  const { data: stockData } = useStock(symbol);

  if (!stockData) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow-sm border p-4">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PriceCard stock={stockData} />
      <InfoCard stock={stockData} />
      <CompanyDescription symbol={symbol} />
    </div>
  );
};

export default HomePage; 