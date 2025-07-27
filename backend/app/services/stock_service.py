import yfinance as yf
from typing import Optional, Dict, Any, List
import pandas as pd
import requests
import asyncio
from datetime import datetime, timedelta
from ..models.stock import StockInfo, ChartData, ChartDataPoint, StockSuggestion, FinancialData, DividendData
from requests.exceptions import HTTPError

class StockService:
    def __init__(self):
        # 강화된 캐시 시스템
        self.cache = {}
        self.cache_duration = 300  # 5분 캐시
        self.batch_cache_duration = 180  # 3분 (배치 데이터용)
        
        # 캐시 키 상수
        self.CACHE_KEYS = {
            'TOP_MARKET_CAP': 'top_market_cap_stocks',
            'INDEX_STOCKS': 'index_stocks_{index_name}',
            'STOCK_INFO': 'stock_info_{symbol}',
            'BATCH_STOCKS': 'batch_stocks_{tickers_hash}'
        }
        
        # 배치 처리 설정
        self.max_concurrent_requests = 5
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # 한글 회사명 매핑 데이터
        self.korean_company_mapping = {
            # 기술 기업
            "애플": "Apple",
            "구글": "Google", 
            "알파벳": "Alphabet",
            "마이크로소프트": "Microsoft",
            "아마존": "Amazon",
            "테슬라": "Tesla",
            "메타": "Meta",
            "페이스북": "Facebook",
            "넷플릭스": "Netflix",
            "엔비디아": "NVIDIA",
            "인텔": "Intel",
            "어도비": "Adobe",
            "페이팔": "PayPal",
            "세일즈포스": "Salesforce",
            
            # 금융 기업
            "제이피모건": "JPMorgan",
            "뱅크오브아메리카": "Bank of America",
            "웰스파고": "Wells Fargo",
            "골드만삭스": "Goldman Sachs",
            "모건스탠리": "Morgan Stanley",
            
            # 제조/소비재 기업
            "존슨앤존슨": "Johnson & Johnson",
            "프록터앤갬블": "Procter & Gamble",
            "코카콜라": "Coca-Cola",
            "펩시": "Pepsi",
            "월마트": "Walmart",
            "홈디포": "Home Depot",
            "월트디즈니": "Walt Disney",
            "버라이즌": "Verizon",
            "AT&T": "AT&T",
            
            # 기타 유명 기업
            "버킹엄": "Berkshire Hathaway",
            "유나이티드헬스": "UnitedHealth",
            "비자": "Visa",
            "마스터카드": "Mastercard",
            "맥도날드": "McDonald's",
            "스타벅스": "Starbucks",
            "나이키": "Nike",
            "애디다스": "Adidas",
            
            # 팔란티어 관련 (사용자가 검색한 단어)
            "팔란티어": "Palantir",
            "팔란티어테크": "Palantir Technologies",
        }
    
    def _get_cache_key(self, key_type: str, **kwargs) -> str:
        """캐시 키 생성"""
        if key_type == 'INDEX_STOCKS':
            return self.CACHE_KEYS['INDEX_STOCKS'].format(index_name=kwargs.get('index_name'))
        elif key_type == 'STOCK_INFO':
            return self.CACHE_KEYS['STOCK_INFO'].format(symbol=kwargs.get('symbol'))
        elif key_type == 'BATCH_STOCKS':
            tickers_hash = hash(tuple(sorted(kwargs.get('tickers', []))))
            return self.CACHE_KEYS['BATCH_STOCKS'].format(tickers_hash=tickers_hash)
        else:
            return self.CACHE_KEYS.get(key_type, key_type)
    
    def _is_cache_valid(self, cache_data: Dict, duration: int = None) -> bool:
        """캐시 유효성 검사"""
        if not cache_data or 'timestamp' not in cache_data:
            return False
        
        cache_duration = duration or self.cache_duration
        return (datetime.now() - cache_data['timestamp']).total_seconds() < cache_duration
    
    def _set_cache(self, key: str, data: Any, duration: int = None) -> None:
        """캐시에 데이터 저장"""
        cache_duration = duration or self.cache_duration
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now(),
            'duration': cache_duration
        }
    
    def _get_cache(self, key: str, duration: int = None) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        cache_data = self.cache.get(key)
        if cache_data and self._is_cache_valid(cache_data, duration):
            return cache_data['data']
        return None
    
    def _translate_korean_to_english(self, query: str) -> str:
        """한글 검색어를 영어로 변환"""
        query_lower = query.lower()
        
        # 정확한 매칭
        if query_lower in self.korean_company_mapping:
            return self.korean_company_mapping[query_lower]
        
        # 부분 매칭
        for korean, english in self.korean_company_mapping.items():
            if korean in query_lower or query_lower in korean:
                return english
        
        # 매칭되지 않으면 원본 반환
        return query
    
    def _translate_to_korean(self, text: str) -> str:
        """영어 텍스트를 한글로 번역"""
        if not text or text.strip() == "":
            return ""
        
        try:
            # 간단한 번역 API 사용 (무료)
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "en",
                "tl": "ko",
                "dt": "t",
                "q": text
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                result = response.json()
                if result and len(result) > 0 and len(result[0]) > 0:
                    translated_text = "".join([item[0] for item in result[0] if item[0]])
                    return translated_text
            
            # 번역 실패시 원본 반환
            return text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get detailed stock information for a single symbol (Mock Data)"""
        print(f"🔄 Fetching stock info for {symbol}")
        
        # 캐시 확인
        cache_key = f"stock_info_{symbol}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            print(f"✅ Using cached data for {symbol}")
            return cached_data
        
        # Mock 데이터 정의
        mock_stock_data = {
            "AAPL": {
                "name": "Apple Inc.",
                "currentPrice": 213.88,
                "previousClose": 213.76,
                "change": 0.12,
                "changePercent": 0.06,
                "high": 215.50,
                "low": 212.30,
                "volume": 45000000,
                "marketCap": 3200000000000,  # 3.2T
                "peRatio": 28.5,
                "dividendYield": 0.5,
                "beta": 1.2,
                "fiftyTwoWeekHigh": 230.50,
                "fiftyTwoWeekLow": 150.20,
                "avgVolume": 52000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "currentPrice": 513.71,
                "previousClose": 510.88,
                "change": 2.83,
                "changePercent": 0.55,
                "high": 515.20,
                "low": 509.50,
                "volume": 22000000,
                "marketCap": 3800000000000,  # 3.8T
                "peRatio": 35.2,
                "dividendYield": 0.8,
                "beta": 1.1,
                "fiftyTwoWeekHigh": 520.00,
                "fiftyTwoWeekLow": 320.50,
                "avgVolume": 25000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Software"
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "currentPrice": 193.18,
                "previousClose": 192.17,
                "change": 1.01,
                "changePercent": 0.53,
                "high": 194.50,
                "low": 191.80,
                "volume": 28000000,
                "marketCap": 2300000000000,  # 2.3T
                "peRatio": 25.8,
                "dividendYield": 0.0,
                "beta": 1.0,
                "fiftyTwoWeekHigh": 200.00,
                "fiftyTwoWeekLow": 120.50,
                "avgVolume": 30000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Internet Content"
            },
            "AMZN": {
                "name": "Amazon.com Inc.",
                "currentPrice": 231.44,
                "previousClose": 232.23,
                "change": -0.79,
                "changePercent": -0.34,
                "high": 233.50,
                "low": 230.20,
                "volume": 35000000,
                "marketCap": 2500000000000,  # 2.5T
                "peRatio": 45.2,
                "dividendYield": 0.0,
                "beta": 1.3,
                "fiftyTwoWeekHigh": 240.00,
                "fiftyTwoWeekLow": 150.50,
                "avgVolume": 40000000,
                "exchange": "NASDAQ",
                "sector": "Consumer Cyclical",
                "industry": "Internet Retail"
            },
            "NVDA": {
                "name": "NVIDIA Corporation",
                "currentPrice": 173.50,
                "previousClose": 173.74,
                "change": -0.24,
                "changePercent": -0.14,
                "high": 175.20,
                "low": 172.80,
                "volume": 55000000,
                "marketCap": 4200000000000,  # 4.2T
                "peRatio": 75.5,
                "dividendYield": 0.1,
                "beta": 1.8,
                "fiftyTwoWeekHigh": 180.00,
                "fiftyTwoWeekLow": 80.50,
                "avgVolume": 60000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Semiconductors"
            },
            "META": {
                "name": "Meta Platforms Inc.",
                "currentPrice": 712.68,
                "previousClose": 714.80,
                "change": -2.12,
                "changePercent": -0.30,
                "high": 716.50,
                "low": 710.20,
                "volume": 18000000,
                "marketCap": 1800000000000,  # 1.8T
                "peRatio": 32.5,
                "dividendYield": 0.0,
                "beta": 1.4,
                "fiftyTwoWeekHigh": 720.00,
                "fiftyTwoWeekLow": 450.50,
                "avgVolume": 20000000,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Internet Content"
            },
            "BRK-B": {
                "name": "Berkshire Hathaway Inc.",
                "currentPrice": 415.50,
                "previousClose": 414.20,
                "change": 1.30,
                "changePercent": 0.31,
                "high": 417.00,
                "low": 413.50,
                "volume": 8000000,
                "marketCap": 900000000000,  # 900B
                "peRatio": 22.5,
                "dividendYield": 0.0,
                "beta": 0.8,
                "fiftyTwoWeekHigh": 420.00,
                "fiftyTwoWeekLow": 350.50,
                "avgVolume": 9000000,
                "exchange": "NYSE",
                "sector": "Financial Services",
                "industry": "Insurance"
            },
            "LLY": {
                "name": "Eli Lilly and Company",
                "currentPrice": 850.25,
                "previousClose": 848.50,
                "change": 1.75,
                "changePercent": 0.21,
                "high": 852.00,
                "low": 847.20,
                "volume": 5000000,
                "marketCap": 800000000000,  # 800B
                "peRatio": 65.2,
                "dividendYield": 0.7,
                "beta": 0.6,
                "fiftyTwoWeekHigh": 860.00,
                "fiftyTwoWeekLow": 600.50,
                "avgVolume": 5500000,
                "exchange": "NYSE",
                "sector": "Healthcare",
                "industry": "Drug Manufacturers"
            },
            "TSM": {
                "name": "Taiwan Semiconductor Manufacturing",
                "currentPrice": 185.30,
                "previousClose": 184.50,
                "change": 0.80,
                "changePercent": 0.43,
                "high": 186.50,
                "low": 183.80,
                "volume": 12000000,
                "marketCap": 600000000000,  # 600B
                "peRatio": 28.5,
                "dividendYield": 1.2,
                "beta": 1.1,
                "fiftyTwoWeekHigh": 190.00,
                "fiftyTwoWeekLow": 120.50,
                "avgVolume": 13000000,
                "exchange": "NYSE",
                "sector": "Technology",
                "industry": "Semiconductors"
            },
            "V": {
                "name": "Visa Inc.",
                "currentPrice": 295.50,
                "previousClose": 294.80,
                "change": 0.70,
                "changePercent": 0.24,
                "high": 296.50,
                "low": 293.20,
                "volume": 15000000,
                "marketCap": 600000000000,  # 600B
                "peRatio": 30.2,
                "dividendYield": 0.8,
                "beta": 0.9,
                "fiftyTwoWeekHigh": 300.00,
                "fiftyTwoWeekLow": 200.50,
                "avgVolume": 16000000,
                "exchange": "NYSE",
                "sector": "Financial Services",
                "industry": "Credit Services"
            }
        }
        
        # Mock 데이터에서 주식 정보 가져오기
        if symbol in mock_stock_data:
            mock_data = mock_stock_data[symbol]
            
            # StockInfo 객체 생성
            stock_info = StockInfo(
                symbol=symbol,
                name=mock_data["name"],
                currentPrice=mock_data["currentPrice"],
                previousClose=mock_data["previousClose"],
                change=mock_data["change"],
                changePercent=mock_data["changePercent"],
                high=mock_data["high"],
                low=mock_data["low"],
                volume=mock_data["volume"],
                marketCap=mock_data["marketCap"],
                peRatio=mock_data["peRatio"],
                dividendYield=mock_data["dividendYield"],
                beta=mock_data["beta"],
                fiftyTwoWeekHigh=mock_data["fiftyTwoWeekHigh"],
                fiftyTwoWeekLow=mock_data["fiftyTwoWeekLow"],
                avgVolume=mock_data["avgVolume"],
                currency="USD",
                exchange=mock_data["exchange"],
                sector=mock_data["sector"],
                industry=mock_data["industry"]
            )
            
            print(f"✅ Mock data for {symbol}:")
            print(f"   Name: {stock_info.name}")
            print(f"   Price: ${stock_info.currentPrice}")
            print(f"   Change: ${stock_info.change} ({stock_info.changePercent}%)")
            print(f"   Market Cap: ${stock_info.marketCap/1e9:.1f}B")
            
            # 캐시에 저장 (10분)
            self._set_cache(cache_key, stock_info, 600)
            
            return stock_info
        else:
            print(f"❌ Mock data not available for {symbol}")
            return None
    
    async def get_stock_chart(self, symbol: str, period: str = "1y", interval: str = "1d") -> dict:
        """주식 차트 데이터 조회 (Mock Data)"""
        try:
            print(f"🔄 Fetching chart data for {symbol} (Mock Data)")
            
            # Mock 차트 데이터 생성 (1년치 일별 데이터)
            import random
            from datetime import datetime, timedelta
            
            # 기본 가격 설정 (주식별로 다른 기본 가격)
            base_prices = {
                "AAPL": 200.0,
                "MSFT": 500.0,
                "GOOGL": 190.0,
                "AMZN": 230.0,
                "NVDA": 170.0,
                "META": 710.0,
                "BRK-B": 410.0,
                "LLY": 850.0,
                "TSM": 185.0,
                "V": 295.0
            }
            
            base_price = base_prices.get(symbol, 100.0)
            
            # 1년치 일별 데이터 생성 (365일)
            data = []
            current_date = datetime.now() - timedelta(days=365)
            
            for i in range(365):
                # 가격 변동 시뮬레이션 (랜덤 워크)
                price_change = random.uniform(-0.02, 0.02)  # -2% ~ +2%
                base_price *= (1 + price_change)
                
                # OHLC 데이터 생성
                daily_volatility = random.uniform(0.005, 0.015)  # 0.5% ~ 1.5%
                open_price = base_price
                high_price = base_price * (1 + random.uniform(0, daily_volatility))
                low_price = base_price * (1 - random.uniform(0, daily_volatility))
                close_price = base_price * (1 + random.uniform(-daily_volatility/2, daily_volatility/2))
                
                # 거래량 생성
                volume = random.randint(1000000, 100000000)
                
                chart_point = {
                    "timestamp": current_date.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": volume
                }
                data.append(chart_point)
                
                current_date += timedelta(days=1)
            
            print(f"✅ Mock chart data: Generated {len(data)} data points for {symbol}")
            
            result = {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error in get_stock_chart: {e}")
            raise ValueError(f"Failed to fetch chart data for {symbol}: {str(e)}")
    
    async def search_stocks(self, query: str, limit: int = 10) -> List[StockSuggestion]:
        """주식 검색 - Mock Data"""
        try:
            print(f"🔍 Searching for: '{query}' (Mock Data)")
            
            # Mock 검색 데이터
            mock_stocks = [
                StockSuggestion(symbol="AAPL", name="Apple Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="MSFT", name="Microsoft Corporation", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="GOOGL", name="Alphabet Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="AMZN", name="Amazon.com Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="NVDA", name="NVIDIA Corporation", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="META", name="Meta Platforms Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="BRK-B", name="Berkshire Hathaway Inc.", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="LLY", name="Eli Lilly and Company", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="TSM", name="Taiwan Semiconductor Manufacturing", exchange="NYSE", type="Common Stock", country="TW"),
                StockSuggestion(symbol="V", name="Visa Inc.", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="PLTR", name="Palantir Technologies Inc.", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="TSLA", name="Tesla Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="JPM", name="JPMorgan Chase & Co.", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="JNJ", name="Johnson & Johnson", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="PG", name="Procter & Gamble Co.", exchange="NYSE", type="Common Stock", country="US")
            ]
            
            # 검색어와 매칭 (대소문자 무시)
            query_lower = query.lower()
            matched_stocks = []
            
            for stock in mock_stocks:
                # 심볼, 이름, 한글 번역명으로 검색
                if (query_lower in stock.symbol.lower() or 
                    query_lower in stock.name.lower() or
                    query_lower in self._translate_to_korean(stock.name).lower()):
                    matched_stocks.append(stock)
            
            # 검색 결과가 없으면 인기 주식들 반환
            if not matched_stocks:
                print(f"⚠️ No exact matches found, returning popular stocks")
                matched_stocks = mock_stocks[:limit]
            
            print(f"✅ Mock search: Found {len(matched_stocks)} matches")
            return matched_stocks[:limit]
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            # 최종 fallback: 인기 주식에서만 검색
            return await self._search_popular_stocks(query, limit)
    
    async def _search_popular_stocks(self, query: str, limit: int = 10) -> List[StockSuggestion]:
        """인기 주식 목록에서 검색 (fallback)"""
        try:
            popular_stocks = [
                {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "META", "name": "Meta Platforms Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "NFLX", "name": "Netflix Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "JNJ", "name": "Johnson & Johnson", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "V", "name": "Visa Inc.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "PG", "name": "Procter & Gamble Co.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "HD", "name": "Home Depot Inc.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "DIS", "name": "Walt Disney Co.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "PYPL", "name": "PayPal Holdings Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "ADBE", "name": "Adobe Inc.", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "CRM", "name": "Salesforce Inc.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "INTC", "name": "Intel Corporation", "exchange": "NASDAQ", "type": "Common Stock", "country": "US"},
                {"symbol": "VZ", "name": "Verizon Communications Inc.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
                {"symbol": "PLTR", "name": "Palantir Technologies Inc.", "exchange": "NYSE", "type": "Common Stock", "country": "US"},
            ]
            
            # 한글 검색어를 영어로 변환
            english_query = self._translate_korean_to_english(query)
            
            # 쿼리와 매칭되는 주식 필터링 (원본 쿼리와 영어 변환 모두 검색)
            filtered_stocks = [
                stock for stock in popular_stocks
                if (query.upper() in stock["symbol"].upper() or 
                    query.lower() in stock["name"].lower() or
                    english_query.upper() in stock["symbol"].upper() or 
                    english_query.lower() in stock["name"].lower())
            ]
            
            return [StockSuggestion(**stock) for stock in filtered_stocks[:limit]]
        except Exception as e:
            raise ValueError(f"Failed to search popular stocks: {str(e)}")
    
    async def get_popular_stocks(self) -> List[StockInfo]:
        """인기 주식 목록 조회 (Mock Data)"""
        try:
            print(f"🔄 Fetching popular stocks (Mock Data)")
            
            # Mock 인기 주식 데이터
            mock_popular_stocks = [
                StockInfo(
                    symbol="AAPL",
                    name="Apple Inc.",
                    currentPrice=213.88,
                    previousClose=213.76,
                    change=0.12,
                    changePercent=0.06,
                    high=215.50,
                    low=212.30,
                    volume=45000000,
                    marketCap=3200000000000,
                    peRatio=28.5,
                    dividendYield=0.5,
                    beta=1.2,
                    fiftyTwoWeekHigh=230.50,
                    fiftyTwoWeekLow=150.20,
                    avgVolume=52000000,
                    currency="USD",
                    exchange="NASDAQ",
                    sector="Technology",
                    industry="Consumer Electronics"
                ),
                StockInfo(
                    symbol="MSFT",
                    name="Microsoft Corporation",
                    currentPrice=513.71,
                    previousClose=510.88,
                    change=2.83,
                    changePercent=0.55,
                    high=515.20,
                    low=509.50,
                    volume=22000000,
                    marketCap=3800000000000,
                    peRatio=35.2,
                    dividendYield=0.8,
                    beta=1.1,
                    fiftyTwoWeekHigh=520.00,
                    fiftyTwoWeekLow=320.50,
                    avgVolume=25000000,
                    currency="USD",
                    exchange="NASDAQ",
                    sector="Technology",
                    industry="Software"
                ),
                StockInfo(
                    symbol="GOOGL",
                    name="Alphabet Inc.",
                    currentPrice=193.18,
                    previousClose=192.17,
                    change=1.01,
                    changePercent=0.53,
                    high=194.50,
                    low=191.80,
                    volume=28000000,
                    marketCap=2300000000000,
                    peRatio=25.8,
                    dividendYield=0.0,
                    beta=1.0,
                    fiftyTwoWeekHigh=200.00,
                    fiftyTwoWeekLow=120.50,
                    avgVolume=30000000,
                    currency="USD",
                    exchange="NASDAQ",
                    sector="Technology",
                    industry="Internet Content"
                )
            ]
            
            print(f"✅ Mock popular stocks: Returned {len(mock_popular_stocks)} stocks")
            return mock_popular_stocks
            
        except Exception as e:
            print(f"❌ Error in get_popular_stocks: {e}")
            return []

    async def get_financial_data(self, symbol: str) -> FinancialData:
        """주식 재무정보 조회 (MVP: 최근 연간 데이터 1건만)"""
        try:
            ticker = yf.Ticker(symbol)
            fin = ticker.financials
            if fin is None or fin.empty:
                raise ValueError("No financial data")
            # 최근 연도 데이터 추출
            latest_col = fin.columns[0]
            revenue = float(fin.loc["Total Revenue", latest_col]) if "Total Revenue" in fin.index else None
            net_income = float(fin.loc["Net Income", latest_col]) if "Net Income" in fin.index else None
            operating_income = float(fin.loc["Operating Income", latest_col]) if "Operating Income" in fin.index else None
            return FinancialData(
                symbol=symbol,
                period=str(latest_col),
                revenue=revenue,
                netIncome=net_income,
                operatingIncome=operating_income
            )
        except Exception as e:
            raise ValueError(f"Failed to fetch financial data for {symbol}: {str(e)}")

    async def get_dividend_history(self, symbol: str, years: int = 5) -> list:
        """주식 배당 이력 조회 (최근 N년)"""
        try:
            ticker = yf.Ticker(symbol)
            div = ticker.dividends
            if div is None or div.empty:
                return []
            # 인덱스의 타임존 제거
            div.index = div.index.tz_localize(None)
            # 최근 N년 데이터 필터링
            div = div[div.index > pd.Timestamp.now() - pd.DateOffset(years=years)]
            result = [
                DividendData(
                    symbol=symbol,
                    date=str(idx.date()),
                    amount=float(val),
                    type="cash"
                ) for idx, val in div.items()
            ]
            return result
        except Exception as e:
            raise ValueError(f"Failed to fetch dividend history for {symbol}: {str(e)}")

    async def compare_stocks(self, symbols: list) -> list:
        """여러 종목 정보 비교"""
        try:
            result = []
            for symbol in symbols:
                try:
                    info = await self.get_stock_info(symbol)
                    result.append(info)
                except Exception:
                    continue
            return result
        except Exception as e:
            raise ValueError(f"Failed to compare stocks: {str(e)}") 

    async def get_company_description(self, symbol: str) -> dict:
        """회사 상세설명 조회 (Mock Data)"""
        try:
            print(f"🔄 Fetching company description for {symbol} (Mock Data)")
            
            # Mock 회사 설명 데이터
            mock_descriptions = {
                "AAPL": {
                    "name": "Apple Inc.",
                    "shortName": "Apple",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "country": "United States",
                    "website": "https://www.apple.com",
                    "description": "애플은 혁신적인 기술 제품과 서비스를 제공하는 글로벌 기업입니다. iPhone, iPad, Mac, Apple Watch, AirPods 등의 하드웨어 제품과 iOS, macOS, watchOS 등의 소프트웨어 플랫폼을 개발하고 있습니다. 또한 Apple Music, iCloud, Apple TV+ 등의 디지털 서비스도 제공합니다.",
                    "originalDescription": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables and accessories, and sells a variety of related services.",
                    "employees": 164000,
                    "founded": "1976",
                    "ceo": "Tim Cook",
                    "headquarters": "Cupertino, California, United States",
                    "marketCap": 3200000000000,
                    "enterpriseValue": 3100000000000,
                    "revenue": 394328000000,
                    "profitMargin": 0.25,
                    "operatingMargin": 0.30,
                    "returnOnEquity": 1.47,
                    "returnOnAssets": 0.18,
                    "debtToEquity": 0.15
                },
                "MSFT": {
                    "name": "Microsoft Corporation",
                    "shortName": "Microsoft",
                    "sector": "Technology",
                    "industry": "Software",
                    "country": "United States",
                    "website": "https://www.microsoft.com",
                    "description": "마이크로소프트는 개인용 컴퓨터, 서버, 전화기, 지능형 장치용 소프트웨어, 서비스, 디바이스 및 솔루션을 개발, 제조, 라이선스, 지원 및 판매하는 글로벌 기술 기업입니다. Windows, Office, Azure, Xbox 등의 제품으로 유명합니다.",
                    "originalDescription": "Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.",
                    "employees": 221000,
                    "founded": "1975",
                    "ceo": "Satya Nadella",
                    "headquarters": "Redmond, Washington, United States",
                    "marketCap": 3800000000000,
                    "enterpriseValue": 3700000000000,
                    "revenue": 211915000000,
                    "profitMargin": 0.33,
                    "operatingMargin": 0.41,
                    "returnOnEquity": 0.39,
                    "returnOnAssets": 0.18,
                    "debtToEquity": 0.35
                },
                "GOOGL": {
                    "name": "Alphabet Inc.",
                    "shortName": "Alphabet",
                    "sector": "Technology",
                    "industry": "Internet Content",
                    "country": "United States",
                    "website": "https://www.alphabet.com",
                    "description": "알파벳은 Google 검색 엔진, YouTube, Android 운영체제, Chrome 브라우저 등의 인터넷 서비스를 제공하는 기술 기업입니다. 또한 Waymo 자율주행차, Google Cloud, Google Maps 등의 혁신적인 기술도 개발하고 있습니다.",
                    "originalDescription": "Alphabet Inc. provides online advertising services in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.",
                    "employees": 156500,
                    "founded": "2015",
                    "ceo": "Sundar Pichai",
                    "headquarters": "Mountain View, California, United States",
                    "marketCap": 2300000000000,
                    "enterpriseValue": 2200000000000,
                    "revenue": 307394000000,
                    "profitMargin": 0.21,
                    "operatingMargin": 0.26,
                    "returnOnEquity": 0.23,
                    "returnOnAssets": 0.18,
                    "debtToEquity": 0.05
                }
            }
            
            # 기본 Mock 데이터 (알 수 없는 주식용)
            default_description = {
                "name": f"{symbol} Corporation",
                "shortName": symbol,
                "sector": "Technology",
                "industry": "Software",
                "country": "United States",
                "website": f"https://www.{symbol.lower()}.com",
                "description": f"{symbol}는 혁신적인 기술 솔루션을 제공하는 글로벌 기업입니다.",
                "originalDescription": f"{symbol} is a global technology company providing innovative solutions.",
                "employees": 10000,
                "founded": "2000",
                "ceo": "CEO",
                "headquarters": "United States",
                "marketCap": 100000000000,
                "enterpriseValue": 95000000000,
                "revenue": 10000000000,
                "profitMargin": 0.15,
                "operatingMargin": 0.20,
                "returnOnEquity": 0.25,
                "returnOnAssets": 0.10,
                "debtToEquity": 0.30
            }
            
            # Mock 데이터에서 회사 정보 가져오기
            company_info = mock_descriptions.get(symbol, default_description)
            company_info["symbol"] = symbol
            
            print(f"✅ Mock company description: Returned data for {symbol}")
            return company_info
            
        except Exception as e:
            print(f"❌ Error in get_company_description: {e}")
            return {"symbol": symbol, "error": "Failed to fetch company description"} 

    async def get_top_market_cap_stocks(self) -> List[Dict[str, Any]]:
        """시가총액 상위 10개 주식 조회 (Mock Data)"""
        try:
            # 캐시된 데이터 사용
            cached_data = self._get_cache(self._get_cache_key('TOP_MARKET_CAP'))
            if cached_data:
                print(f"✅ Returning cached top market cap stocks")
                return cached_data

            print(f"🔄 Fetching top market cap stocks (Mock Data)")

            # Mock 데이터로 시가총액 상위 10개 주식
            top_stocks = [
                {
                    "symbol": "NVDA",
                    "name": "NVIDIA Corporation",
                    "price": 173.50,
                    "change": -0.24,
                    "changePercent": -0.14,
                    "marketCap": 4200000000000,  # 4.2T
                    "volume": 55000000
                },
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corporation",
                    "price": 513.71,
                    "change": 2.83,
                    "changePercent": 0.55,
                    "marketCap": 3800000000000,  # 3.8T
                    "volume": 22000000
                },
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "price": 213.88,
                    "change": 0.12,
                    "changePercent": 0.06,
                    "marketCap": 3200000000000,  # 3.2T
                    "volume": 45000000
                },
                {
                    "symbol": "GOOGL",
                    "name": "Alphabet Inc.",
                    "price": 193.18,
                    "change": 1.01,
                    "changePercent": 0.53,
                    "marketCap": 2300000000000,  # 2.3T
                    "volume": 28000000
                },
                {
                    "symbol": "AMZN",
                    "name": "Amazon.com Inc.",
                    "price": 231.44,
                    "change": -0.79,
                    "changePercent": -0.34,
                    "marketCap": 2500000000000,  # 2.5T
                    "volume": 35000000
                },
                {
                    "symbol": "META",
                    "name": "Meta Platforms Inc.",
                    "price": 712.68,
                    "change": -2.12,
                    "changePercent": -0.30,
                    "marketCap": 1800000000000,  # 1.8T
                    "volume": 18000000
                },
                {
                    "symbol": "BRK-B",
                    "name": "Berkshire Hathaway Inc.",
                    "price": 415.50,
                    "change": 1.30,
                    "changePercent": 0.31,
                    "marketCap": 900000000000,  # 900B
                    "volume": 8000000
                },
                {
                    "symbol": "LLY",
                    "name": "Eli Lilly and Company",
                    "price": 850.25,
                    "change": 1.75,
                    "changePercent": 0.21,
                    "marketCap": 800000000000,  # 800B
                    "volume": 5000000
                },
                {
                    "symbol": "TSM",
                    "name": "Taiwan Semiconductor Manufacturing",
                    "price": 185.30,
                    "change": 0.80,
                    "changePercent": 0.43,
                    "marketCap": 600000000000,  # 600B
                    "volume": 12000000
                },
                {
                    "symbol": "V",
                    "name": "Visa Inc.",
                    "price": 295.50,
                    "change": 0.70,
                    "changePercent": 0.24,
                    "marketCap": 600000000000,  # 600B
                    "volume": 15000000
                }
            ]

            print(f"✅ Mock data: Successfully fetched {len(top_stocks)} stocks")
            for stock in top_stocks:
                print(f"   {stock['symbol']}: ${stock['price']:.2f} (시총: ${stock['marketCap']/1e9:.1f}B)")

            # 캐시에 저장 (10분)
            self._set_cache(self._get_cache_key('TOP_MARKET_CAP'), top_stocks, 600)

            return top_stocks

        except Exception as e:
            print(f"❌ Error in get_top_market_cap_stocks: {e}")
            return []

    async def get_index_stocks(self, index_name: str) -> List[Dict[str, Any]]:
        """지수별 상위 주식 조회 (실시간)"""
        try:
            # 캐시된 데이터 사용
            cached_data = self._get_cache(self._get_cache_key('INDEX_STOCKS', index_name=index_name))
            if cached_data:
                print(f"Returning cached index stocks for {index_name}")
                return cached_data

            # 각 지수별 주요 주식 리스트 (실제 지수 구성 기반)
            index_constituents = {
                "dow": [
                    "AAPL", "MSFT", "JPM", "JNJ", "V", "PG", "HD", "UNH", "MA", "DIS",
                    "WMT", "KO", "PFE", "T", "VZ", "MRK", "ABT", "CVX", "XOM", "CSCO",
                    "NKE", "MCD", "BA", "CAT", "IBM", "GS", "AXP", "MMM", "DOW", "WBA"
                ],
                "nasdaq": [
                    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", 
                    "ADBE", "PYPL", "INTC", "AMD", "CRM", "ORCL", "CSCO", "QCOM",
                    "AVGO", "TXN", "MU", "ADI", "KLAC", "LRCX", "ASML", "AMAT",
                    "CHTR", "CMCSA", "COST", "PEP", "TMUS", "NFLX"
                ],
                "sp500": [
                    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY", 
                    "TSM", "V", "UNH", "JNJ", "JPM", "PG", "HD", "MA", "DIS", "PFE",
                    "ABBV", "KO", "PEP", "AVGO", "COST", "TMO", "DHR", "ACN", "WMT",
                    "MRK", "VZ", "TXN"
                ],
                "russell2000": [
                    "IWM", "SMH", "XBI", "ARKK", "TQQQ", "SOXL", "LABU", "DPST", 
                    "ERX", "TMF", "UCO", "SCO", "UGA", "UNG", "USO", "BNO", "XOP",
                    "XLE", "XLF", "XLK", "XLV", "XLI", "XLP", "XLY", "XLU", "XLB",
                    "XLC", "XLRE", "XME", "XRT"
                ]
            }
            
            # 유효한 지수명인지 확인
            if index_name not in index_constituents:
                raise ValueError(f"Invalid index name: {index_name}. Must be one of: {list(index_constituents.keys())}")
            
            # 선택된 지수의 구성 주식들 (상위 10개 처리)
            constituents = index_constituents[index_name][:10]  # 상위 10개
            
            # 배치로 주식 정보 가져오기
            stock_infos = await self.get_stock_info_batch(constituents)
            
            # 결과 변환
            stocks = []
            for stock_info in stock_infos:
                if stock_info and stock_info.marketCap > 0:
                    stocks.append({
                        "symbol": stock_info.symbol,
                        "name": stock_info.name,
                        "price": stock_info.currentPrice,
                        "change": stock_info.change,
                        "changePercent": stock_info.changePercent,
                        "marketCap": stock_info.marketCap,
                        "volume": stock_info.volume
                    })
            
            # 실시간 시가총액 순으로 정렬
            stocks.sort(key=lambda x: x.get("marketCap", 0), reverse=True)
            
            # 캐시에 저장
            self._set_cache(self._get_cache_key('INDEX_STOCKS', index_name=index_name), stocks)
            
            return stocks[:10]  # 상위 10개 반환
            
        except Exception as e:
            raise Exception(f"Failed to get index stocks for {index_name}: {str(e)}")

    async def get_stock_info_batch(self, tickers: List[str]) -> List[Optional[StockInfo]]:
        """배치로 주식 정보 가져오기 (API 제한 방지)"""
        async def fetch_single_stock_with_retry(ticker: str, max_retries: int = 5) -> Optional[StockInfo]:
            for attempt in range(max_retries):
                try:
                    print(f"🔄 Fetching stock info for {ticker} (attempt {attempt + 1}/{max_retries})")
                    
                    # API 제한 방지를 위한 지연 (점진적 증가)
                    # 배포 환경 감지
                    import os
                    is_production = os.getenv('RENDER', False) or os.getenv('VERCEL', False)
                    
                    if is_production:
                        delay = 10.0 + (attempt * 5.0)  # 배포: 10s, 15s, 20s
                    else:
                        delay = 5.0 + (attempt * 2.0)   # 로컬: 5s, 7s, 9s
                    
                    print(f"⏳ Waiting {delay}s before request (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    
                    result = await self.get_stock_info(ticker)
                    if result:
                        print(f"✅ Successfully fetched {ticker}")
                        return result
                    else:
                        print(f"⚠️ No data for {ticker}")
                        return None
                        
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Error fetching {ticker} (attempt {attempt + 1}): {error_msg}")
                    
                    # 429 오류인 경우 더 긴 지연
                    if "429" in error_msg or "Too Many Requests" in error_msg:
                        print(f"🛑 Rate limit hit for {ticker}, waiting longer...")
                        # 배포 환경에서는 더 긴 지연
                        import os
                        is_production = os.getenv('RENDER', False) or os.getenv('VERCEL', False)
                        
                        if is_production:
                            wait_time = 30.0 + (attempt * 15.0)  # 배포: 30s, 45s, 60s
                        else:
                            wait_time = 10.0 + (attempt * 5.0)   # 로컬: 10s, 15s, 20s
                        
                        print(f"⏳ Waiting {wait_time}s due to rate limit...")
                        await asyncio.sleep(wait_time)
                    
                    if attempt == max_retries - 1:
                        print(f"❌ Failed to fetch {ticker} after {max_retries} attempts")
                        return None
            
            return None

        async def fetch_with_semaphore(ticker: str) -> Optional[StockInfo]:
            async with self.request_semaphore:
                return await fetch_single_stock_with_retry(ticker)

        # 순차 처리로 변경 (API 제한 방지)
        print(f"🚀 Starting sequential fetch for {len(tickers)} tickers")
        stock_infos = []
        success_count = 0
        
        # 배포 환경 감지
        import os
        is_production = os.getenv('RENDER', False) or os.getenv('VERCEL', False)
        
        for i, ticker in enumerate(tickers):
            print(f"📊 Processing {i+1}/{len(tickers)}: {ticker}")
            
            # 배포 환경에서는 더 긴 지연
            if is_production:
                print(f"🌐 Production environment detected, using extended delays")
                await asyncio.sleep(8.0)  # 배포 환경에서 8초 지연
            
            result = await fetch_with_semaphore(ticker)
            stock_infos.append(result)
            if result:
                success_count += 1
                print(f"✅ Progress: {success_count}/{len(tickers)} successful")
            
            # 배포 환경에서 추가 지연
            if is_production and i < len(tickers) - 1:
                print(f"⏳ Production delay between requests...")
                await asyncio.sleep(5.0)
        
        print(f"✅ Sequential fetch completed: {success_count}/{len(tickers)} successful")
        return stock_infos

    # get_index_constituents 메서드는 get_index_stocks로 통합되었으므로 제거 