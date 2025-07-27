import React, { useState, useCallback } from 'react';
import { stockService } from '../../services/stockService';
import { StockSuggestion } from '../../types/stock';
import LoadingSpinner from '../common/LoadingSpinner';

interface StockSearchProps {
  onSearch: (query: string) => void;
  onSelect: (symbol: string) => void;
  placeholder?: string;
  className?: string;
}

const StockSearch: React.FC<StockSearchProps> = ({
  onSearch,
  onSelect,
  placeholder = "종목명 또는 티커 검색...",
  className
}) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<StockSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // 검색 로직
  const handleSearch = useCallback(
    async (searchQuery: string) => {
      console.log(`🔍 StockSearch: handleSearch called with '${searchQuery}'`);
      
      if (searchQuery.length < 2) {
        console.log(`⚠️ StockSearch: Query too short (${searchQuery.length} chars)`);
        setSuggestions([]);
        return;
      }
      
      setIsLoading(true);
      try {
        console.log(`🔄 StockSearch: Calling stockService.searchStocks('${searchQuery}')`);
        const results = await stockService.searchStocks(searchQuery);
        console.log(`✅ StockSearch: Received ${results?.length || 0} results:`, results);
        setSuggestions(results || []);
      } catch (error) {
        console.error("❌ StockSearch: Search error:", error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    handleSearch(value);
  };

  const handleSuggestionClick = (suggestion: StockSuggestion) => {
    onSelect(suggestion.symbol);
    setQuery("");
    setSuggestions([]);
  };
  
  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder={placeholder}
          className="w-full px-4 py-3 pl-12 text-lg border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <svg 
          className="absolute left-3 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        {isLoading && (
          <LoadingSpinner className="absolute right-3 top-1/2 transform -translate-y-1/2" />
        )}
      </div>
      
      {/* 검색 제안 */}
      {suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.symbol}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold text-gray-900">
                    {suggestion.symbol}
                  </div>
                  <div className="text-sm text-gray-600">
                    {suggestion.name}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {suggestion.exchange}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default StockSearch; 