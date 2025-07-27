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
    
    def _get_mock_stock_data(self) -> dict:
        """Mock 주식 데이터 반환"""
        return {
            "AAPL": {
                "name": "Apple Inc.",
                "currentPrice": 213.88,
                "previousClose": 213.76,
                "change": 0.12,
                "changePercent": 0.056,
                "high": 215.24,
                "low": 213.4,
                "volume": 38585030,
                "marketCap": 3194468958208,  # 3.19T
                "peRatio": 33.31,
                "dividendYield": 0.49,
                "beta": 1.199,
                "fiftyTwoWeekHigh": 260.1,
                "fiftyTwoWeekLow": 169.21,
                "avgVolume": 38585030,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Consumer Electronics"
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "currentPrice": 513.71,
                "previousClose": 510.88,
                "change": 2.83,
                "changePercent": 0.554,
                "high": 518.29,
                "low": 510.36,
                "volume": 18998701,
                "marketCap": 3818170351616,  # 3.82T
                "peRatio": 39.67,
                "dividendYield": 0.65,
                "beta": 1.033,
                "fiftyTwoWeekHigh": 518.29,
                "fiftyTwoWeekLow": 344.79,
                "avgVolume": 19908059,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Software - Infrastructure"
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "currentPrice": 193.18,
                "previousClose": 192.17,
                "change": 1.01,
                "changePercent": 0.526,
                "high": 194.33,
                "low": 191.26,
                "volume": 39519098,
                "marketCap": 2341206228992,  # 2.34T
                "peRatio": 20.57,
                "dividendYield": 0.43,
                "beta": 1.005,
                "fiftyTwoWeekHigh": 207.05,
                "fiftyTwoWeekLow": 140.53,
                "avgVolume": 41583572,
                "exchange": "NASDAQ",
                "sector": "Communication Services",
                "industry": "Internet Content & Information"
            },
            "AMZN": {
                "name": "Amazon.com Inc.",
                "currentPrice": 231.44,
                "previousClose": 232.23,
                "change": -0.79,
                "changePercent": -0.34,
                "high": 232.48,
                "low": 231.18,
                "volume": 28339929,
                "marketCap": 2457059721216,  # 2.46T
                "peRatio": 37.76,
                "dividendYield": 0.0,
                "beta": 1.337,
                "fiftyTwoWeekHigh": 242.52,
                "fiftyTwoWeekLow": 151.61,
                "avgVolume": 41880872,
                "exchange": "NASDAQ",
                "sector": "Consumer Cyclical",
                "industry": "Internet Retail"
            },
            "NVDA": {
                "name": "NVIDIA Corporation",
                "currentPrice": 173.5,
                "previousClose": 173.74,
                "change": -0.24,
                "changePercent": -0.138,
                "high": 174.72,
                "low": 172.97,
                "volume": 120814633,
                "marketCap": 4231248740352,  # 4.23T
                "peRatio": 55.79,
                "dividendYield": 0.02,
                "beta": 2.131,
                "fiftyTwoWeekHigh": 174.72,
                "fiftyTwoWeekLow": 86.62,
                "avgVolume": 195125162,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Semiconductors"
            },
            "META": {
                "name": "Meta Platforms Inc.",
                "currentPrice": 712.68,
                "previousClose": 714.8,
                "change": -2.12,
                "changePercent": -0.297,
                "high": 720.65,
                "low": 711.9,
                "volume": 8239722,
                "marketCap": 1791912706048,  # 1.79T
                "peRatio": 27.85,
                "dividendYield": 0.29,
                "beta": 1.284,
                "fiftyTwoWeekHigh": 747.9,
                "fiftyTwoWeekLow": 450.8,
                "avgVolume": 12720433,
                "exchange": "NASDAQ",
                "sector": "Communication Services",
                "industry": "Internet Content & Information"
            },
            "BRK-B": {
                "name": "Berkshire Hathaway Inc.",
                "currentPrice": 484.07,
                "previousClose": 480.6,
                "change": 3.47,
                "changePercent": 0.722,
                "high": 484.88,
                "low": 480.6,
                "volume": 4194066,
                "marketCap": 1044361641984,  # 1.04T
                "peRatio": 9.5,
                "dividendYield": 0.0,
                "beta": 0.87,
                "fiftyTwoWeekHigh": 484.88,
                "fiftyTwoWeekLow": 325.0,
                "avgVolume": 4194066,
                "exchange": "NYSE",
                "sector": "Financial Services",
                "industry": "Insurance - Diversified"
            },
            "LLY": {
                "name": "Eli Lilly and Company",
                "currentPrice": 812.69,
                "previousClose": 805.43,
                "change": 7.26,
                "changePercent": 0.901,
                "high": 812.69,
                "low": 805.43,
                "volume": 2974840,
                "marketCap": 729581092864,  # 730B
                "peRatio": 132.0,
                "dividendYield": 0.68,
                "beta": 0.32,
                "fiftyTwoWeekHigh": 812.69,
                "fiftyTwoWeekLow": 434.0,
                "avgVolume": 2974840,
                "exchange": "NYSE",
                "sector": "Healthcare",
                "industry": "Drug Manufacturers - General"
            },
            "TSM": {
                "name": "Taiwan Semiconductor Manufacturing",
                "currentPrice": 245.6,
                "previousClose": 241.6,
                "change": 4.0,
                "changePercent": 1.656,
                "high": 245.6,
                "low": 241.6,
                "volume": 11531815,
                "marketCap": 1273809338368,  # 1.27T
                "peRatio": 25.0,
                "dividendYield": 1.8,
                "beta": 1.2,
                "fiftyTwoWeekHigh": 245.6,
                "fiftyTwoWeekLow": 120.0,
                "avgVolume": 11531815,
                "exchange": "NYSE",
                "sector": "Technology",
                "industry": "Semiconductors"
            },
            "V": {
                "name": "Visa Inc.",
                "currentPrice": 357.04,
                "previousClose": 355.0,
                "change": 2.04,
                "changePercent": 0.575,
                "high": 357.04,
                "low": 355.0,
                "volume": 8500000,
                "marketCap": 345000000000,  # 345B
                "peRatio": 32.0,
                "dividendYield": 0.8,
                "beta": 0.95,
                "fiftyTwoWeekHigh": 357.04,
                "fiftyTwoWeekLow": 280.0,
                "avgVolume": 8500000,
                "exchange": "NYSE",
                "sector": "Financial Services",
                "industry": "Credit Services"
            },
            "TSLA": {
                "name": "Tesla Inc.",
                "currentPrice": 316.06,
                "previousClose": 305.3,
                "change": 10.76,
                "changePercent": 3.524,
                "high": 323.63,
                "low": 308.01,
                "volume": 147147702,
                "marketCap": 1019435745280,  # 1.02T
                "peRatio": 188.13,
                "dividendYield": 0.0,
                "beta": 2.398,
                "fiftyTwoWeekHigh": 488.54,
                "fiftyTwoWeekLow": 182.0,
                "avgVolume": 109701372,
                "exchange": "NASDAQ",
                "sector": "Consumer Cyclical",
                "industry": "Auto Manufacturers"
            },
            "PLTR": {
                "name": "Palantir Technologies Inc.",
                "currentPrice": 158.8,
                "previousClose": 154.86,
                "change": 3.94,
                "changePercent": 2.544,
                "high": 160.39,
                "low": 155.67,
                "volume": 57495017,
                "marketCap": 374753689600,  # 375B
                "peRatio": 721.82,
                "dividendYield": 0.0,
                "beta": 2.593,
                "fiftyTwoWeekHigh": 160.39,
                "fiftyTwoWeekLow": 21.23,
                "avgVolume": 83173206,
                "exchange": "NASDAQ",
                "sector": "Technology",
                "industry": "Software - Infrastructure"
            }
        }

    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get detailed stock information for a single symbol (Mock Data)"""
        print(f"🔄 Fetching stock info for {symbol}")
        
        # 캐시 확인
        cache_key = f"stock_info_{symbol}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            print(f"✅ Using cached data for {symbol}")
            return cached_data
        
        # Mock 데이터 가져오기
        mock_stock_data = self._get_mock_stock_data()
        
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
            
            # Mock 차트 데이터 생성 (1년치 일별 데이터 - 2025-07-25 기준)
            import random
            from datetime import datetime, timedelta
            
            # 기본 가격 설정 (주식별로 다른 기본 가격 - 2025-07-27 기준)
            base_prices = {
                "AAPL": 213.88,
                "MSFT": 513.71,
                "GOOGL": 193.18,
                "AMZN": 231.44,
                "NVDA": 173.5,
                "META": 712.68,
                "BRK-B": 484.07,
                "LLY": 812.69,
                "TSM": 245.6,
                "V": 357.04,
                "TSLA": 316.06,
                "PLTR": 158.8
            }
            
            base_price = base_prices.get(symbol, 100.0)
            
            # 1년치 일별 데이터 생성 (365일) - 2025-07-27 기준
            data = []
            current_date = datetime(2025, 7, 27) - timedelta(days=365)
            
            # 목표 최종 가격 (실제 주식 가격과 일치)
            target_final_price = base_prices.get(symbol, 100.0)
            
            for i in range(365):
                # 마지막 데이터 포인트에서는 목표 가격으로 설정
                if i == 364:  # 마지막 날
                    close_price = target_final_price
                    open_price = close_price * (1 + random.uniform(-0.01, 0.01))
                    high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
                    low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
                else:
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
            
            # 1일 차트의 경우 더 정확한 가격 데이터 생성
            if period == "1d" or interval == "1m":
                # 1일 차트 데이터 생성 (24시간, 1분 간격)
                daily_data = []
                current_time = datetime(2025, 7, 27, 9, 30)  # 시장 개장 시간
                
                # 실제 주식 정보에서 가격 데이터 가져오기
                stock_info = self._get_mock_stock_data().get(symbol, {})
                current_price = stock_info.get("currentPrice", target_final_price)
                previous_close = stock_info.get("previousClose", current_price * 0.99)
                high = stock_info.get("high", current_price * 1.02)
                low = stock_info.get("low", current_price * 0.98)
                volume = stock_info.get("volume", 10000000)
                
                for minute in range(390):  # 6.5시간 (9:30 AM - 4:00 PM)
                    # 시간별 가격 변동 시뮬레이션
                    if minute == 0:
                        price = previous_close
                    elif minute == 389:  # 마지막 분
                        price = current_price
                    else:
                        # 가격이 low와 high 사이에서 변동
                        progress = minute / 389
                        base_price = previous_close + (current_price - previous_close) * progress
                        volatility = random.uniform(-0.005, 0.005)  # 0.5% 변동
                        price = base_price * (1 + volatility)
                        price = max(low, min(high, price))  # high/low 범위 내로 제한
                    
                    daily_data.append({
                        "timestamp": current_time.isoformat(),
                        "open": round(price, 2),
                        "high": round(price, 2),
                        "low": round(price, 2),
                        "close": round(price, 2),
                        "volume": volume // 390  # 분당 거래량
                    })
                    
                    current_time += timedelta(minutes=1)
                
                data = daily_data
            
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
                StockSuggestion(symbol="PG", name="Procter & Gamble Co.", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="NFLX", name="Netflix Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="ADBE", name="Adobe Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="PYPL", name="PayPal Holdings Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="INTC", name="Intel Corporation", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="AMD", name="Advanced Micro Devices Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="CRM", name="Salesforce Inc.", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="ORCL", name="Oracle Corporation", exchange="NYSE", type="Common Stock", country="US"),
                StockSuggestion(symbol="CSCO", name="Cisco Systems Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="QCOM", name="Qualcomm Incorporated", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="AVGO", name="Broadcom Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="TXN", name="Texas Instruments Incorporated", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="MU", name="Micron Technology Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="ADI", name="Analog Devices Inc.", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="KLAC", name="KLA Corporation", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="LRCX", name="Lam Research Corporation", exchange="NASDAQ", type="Common Stock", country="US"),
                StockSuggestion(symbol="ASML", name="ASML Holding N.V.", exchange="NASDAQ", type="Common Stock", country="NL"),
                StockSuggestion(symbol="AMAT", name="Applied Materials Inc.", exchange="NASDAQ", type="Common Stock", country="US")
            ]
            
            # 한글-영문 매핑 딕셔너리
            korean_mapping = {
                "팔란티어": "palantir",
                "테슬라": "tesla",
                "애플": "apple",
                "마이크로소프트": "microsoft",
                "구글": "google",
                "알파벳": "alphabet",
                "아마존": "amazon",
                "엔비디아": "nvidia",
                "메타": "meta",
                "넷플릭스": "netflix",
                "버크셔": "berkshire",
                "엘리릴리": "eli lilly",
                "타이완반도체": "taiwan semiconductor",
                "비자": "visa",
                "모건": "jpmorgan",
                "존슨앤존슨": "johnson",
                "프록터앤갬블": "procter",
                "페이팔": "paypal",
                "어도비": "adobe",
                "인텔": "intel",
                "amd": "amd",
                "퀄컴": "qualcomm",
                "브로드컴": "broadcom",
                "텍사스인스트루먼트": "texas instruments",
                "마이크론": "micron",
                "아날로그디바이스": "analog devices",
                "케이엘에이": "kla",
                "라믹스": "lam research",
                "asml": "asml",
                "어플라이드머티어리얼": "applied materials"
            }
            
            # 검색어와 매칭 (대소문자 무시)
            query_lower = query.lower()
            matched_stocks = []
            
            # 한글 검색어를 영어로 변환
            english_query = korean_mapping.get(query_lower, query_lower)
            
            for stock in mock_stocks:
                # 심볼, 이름, 한글 번역명으로 검색
                stock_name_lower = stock.name.lower()
                stock_symbol_lower = stock.symbol.lower()
                
                # 직접 매칭
                if (query_lower in stock_symbol_lower or 
                    query_lower in stock_name_lower or
                    english_query in stock_name_lower):
                    matched_stocks.append(stock)
                    continue
                
                # 한글 매핑을 통한 검색
                for korean, english in korean_mapping.items():
                    if (query_lower in korean and english in stock_name_lower) or \
                       (english in query_lower and english in stock_name_lower):
                        matched_stocks.append(stock)
                        break
            
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
            
            # Mock 인기 주식 데이터 (2025-07-27 기준 - 실제 Yahoo Finance 데이터)
            mock_popular_stocks = [
                StockInfo(
                    symbol="AAPL",
                    name="Apple Inc.",
                    currentPrice=213.88,
                    previousClose=213.76,
                    change=0.12,
                    changePercent=0.056,
                    high=215.24,
                    low=213.4,
                    volume=38585030,
                    marketCap=3194468958208,
                    peRatio=33.31,
                    dividendYield=0.49,
                    beta=1.199,
                    fiftyTwoWeekHigh=260.1,
                    fiftyTwoWeekLow=169.21,
                    avgVolume=38585030,
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
                    changePercent=0.554,
                    high=518.29,
                    low=510.36,
                    volume=18998701,
                    marketCap=3818170351616,
                    peRatio=39.67,
                    dividendYield=0.65,
                    beta=1.033,
                    fiftyTwoWeekHigh=518.29,
                    fiftyTwoWeekLow=344.79,
                    avgVolume=19908059,
                    currency="USD",
                    exchange="NASDAQ",
                    sector="Technology",
                    industry="Software - Infrastructure"
                ),
                StockInfo(
                    symbol="GOOGL",
                    name="Alphabet Inc.",
                    currentPrice=193.18,
                    previousClose=192.17,
                    change=1.01,
                    changePercent=0.526,
                    high=194.33,
                    low=191.26,
                    volume=39519098,
                    marketCap=2341206228992,
                    peRatio=20.57,
                    dividendYield=0.43,
                    beta=1.005,
                    fiftyTwoWeekHigh=207.05,
                    fiftyTwoWeekLow=140.53,
                    avgVolume=41583572,
                    currency="USD",
                    exchange="NASDAQ",
                    sector="Communication Services",
                    industry="Internet Content & Information"
                )
            ]
            
            print(f"✅ Mock popular stocks: Returned {len(mock_popular_stocks)} stocks")
            return mock_popular_stocks
            
        except Exception as e:
            print(f"❌ Error in get_popular_stocks: {e}")
            return []

    async def get_financial_data(self, symbol: str) -> FinancialData:
        """주식 재무정보 조회 (Mock Data)"""
        try:
            print(f"🔄 Fetching financial data for {symbol} (Mock Data)")
            
            # Mock 재무 데이터
            mock_financial_data = {
                "AAPL": {
                    "revenue": 394328000000,  # 394.3B
                    "netIncome": 96995000000,  # 97.0B
                    "operatingIncome": 114301000000  # 114.3B
                },
                "MSFT": {
                    "revenue": 211915000000,  # 211.9B
                    "netIncome": 72409000000,  # 72.4B
                    "operatingIncome": 88452000000  # 88.5B
                },
                "GOOGL": {
                    "revenue": 307394000000,  # 307.4B
                    "netIncome": 73795000000,  # 73.8B
                    "operatingIncome": 84293000000  # 84.3B
                },
                "AMZN": {
                    "revenue": 574785000000,  # 574.8B
                    "netIncome": 30425000000,  # 30.4B
                    "operatingIncome": 51242000000  # 51.2B
                },
                "NVDA": {
                    "revenue": 60922000000,  # 60.9B
                    "netIncome": 29760000000,  # 29.8B
                    "operatingIncome": 32972000000  # 33.0B
                },
                "TSLA": {
                    "revenue": 96773000000,  # 96.8B
                    "netIncome": 14997000000,  # 15.0B
                    "operatingIncome": 8890000000  # 8.9B
                },
                "PLTR": {
                    "revenue": 2225000000,  # 2.2B
                    "netIncome": 209000000,  # 209M
                    "operatingIncome": 119000000  # 119M
                }
            }
            
            # Mock 데이터에서 재무 정보 가져오기
            if symbol in mock_financial_data:
                data = mock_financial_data[symbol]
                financial_data = FinancialData(
                    symbol=symbol,
                    period="2024",
                    revenue=data["revenue"],
                    netIncome=data["netIncome"],
                    operatingIncome=data["operatingIncome"]
                )
                print(f"✅ Mock financial data: Returned data for {symbol}")
                return financial_data
            else:
                # 기본 Mock 데이터 (알 수 없는 주식용)
                financial_data = FinancialData(
                    symbol=symbol,
                    period="2024",
                    revenue=10000000000,  # 10B
                    netIncome=1500000000,  # 1.5B
                    operatingIncome=2000000000  # 2B
                )
                print(f"✅ Mock financial data: Returned default data for {symbol}")
                return financial_data
                
        except Exception as e:
            print(f"❌ Error in get_financial_data: {e}")
            raise ValueError(f"Failed to fetch financial data for {symbol}: {str(e)}")

    async def get_dividend_history(self, symbol: str, years: int = 5) -> list:
        """주식 배당 이력 조회 (Mock Data)"""
        try:
            print(f"🔄 Fetching dividend history for {symbol} (Mock Data)")
            
            # Mock 배당 데이터
            mock_dividend_data = {
                "AAPL": [
                    {"date": "2025-05-15", "amount": 0.25},
                    {"date": "2025-02-13", "amount": 0.25},
                    {"date": "2024-11-14", "amount": 0.25},
                    {"date": "2024-08-15", "amount": 0.25},
                    {"date": "2024-05-16", "amount": 0.24},
                    {"date": "2024-02-14", "amount": 0.24},
                    {"date": "2023-11-15", "amount": 0.24},
                    {"date": "2023-08-16", "amount": 0.24},
                    {"date": "2023-05-17", "amount": 0.24},
                    {"date": "2023-02-15", "amount": 0.23}
                ],
                "MSFT": [
                    {"date": "2025-06-12", "amount": 0.78},
                    {"date": "2025-03-13", "amount": 0.78},
                    {"date": "2024-12-12", "amount": 0.78},
                    {"date": "2024-09-12", "amount": 0.75},
                    {"date": "2024-06-13", "amount": 0.75},
                    {"date": "2024-03-14", "amount": 0.75},
                    {"date": "2023-12-14", "amount": 0.75},
                    {"date": "2023-09-14", "amount": 0.68},
                    {"date": "2023-06-15", "amount": 0.68},
                    {"date": "2023-03-16", "amount": 0.68}
                ],
                "JPM": [
                    {"date": "2025-07-03", "amount": 1.08},
                    {"date": "2025-04-03", "amount": 1.08},
                    {"date": "2025-01-02", "amount": 1.08},
                    {"date": "2024-10-03", "amount": 1.05},
                    {"date": "2024-07-03", "amount": 1.05},
                    {"date": "2024-04-03", "amount": 1.05},
                    {"date": "2024-01-03", "amount": 1.05},
                    {"date": "2023-10-03", "amount": 1.05},
                    {"date": "2023-07-03", "amount": 1.00},
                    {"date": "2023-04-03", "amount": 1.00}
                ],
                "JNJ": [
                    {"date": "2025-06-25", "amount": 1.22},
                    {"date": "2025-03-25", "amount": 1.22},
                    {"date": "2024-12-25", "amount": 1.22},
                    {"date": "2024-09-25", "amount": 1.19},
                    {"date": "2024-06-25", "amount": 1.19},
                    {"date": "2024-03-25", "amount": 1.19},
                    {"date": "2023-12-25", "amount": 1.19},
                    {"date": "2023-09-25", "amount": 1.19},
                    {"date": "2023-06-26", "amount": 1.13},
                    {"date": "2023-03-27", "amount": 1.13}
                ],
                "V": [
                    {"date": "2025-06-06", "amount": 0.54},
                    {"date": "2025-03-06", "amount": 0.54},
                    {"date": "2024-12-06", "amount": 0.54},
                    {"date": "2024-09-06", "amount": 0.52},
                    {"date": "2024-06-06", "amount": 0.52},
                    {"date": "2024-03-06", "amount": 0.52},
                    {"date": "2023-12-06", "amount": 0.52},
                    {"date": "2023-09-06", "amount": 0.45},
                    {"date": "2023-06-06", "amount": 0.45},
                    {"date": "2023-03-06", "amount": 0.45}
                ],
                "TSLA": [
                    {"date": "2025-01-15", "amount": 0.00},
                    {"date": "2024-10-15", "amount": 0.00},
                    {"date": "2024-07-15", "amount": 0.00},
                    {"date": "2024-04-15", "amount": 0.00},
                    {"date": "2024-01-15", "amount": 0.00},
                    {"date": "2023-10-15", "amount": 0.00},
                    {"date": "2023-07-15", "amount": 0.00},
                    {"date": "2023-04-15", "amount": 0.00},
                    {"date": "2023-01-15", "amount": 0.00},
                    {"date": "2022-10-15", "amount": 0.00}
                ],
                "PLTR": [
                    {"date": "2025-01-15", "amount": 0.00},
                    {"date": "2024-10-15", "amount": 0.00},
                    {"date": "2024-07-15", "amount": 0.00},
                    {"date": "2024-04-15", "amount": 0.00},
                    {"date": "2024-01-15", "amount": 0.00},
                    {"date": "2023-10-15", "amount": 0.00},
                    {"date": "2023-07-15", "amount": 0.00},
                    {"date": "2023-04-15", "amount": 0.00},
                    {"date": "2023-01-15", "amount": 0.00},
                    {"date": "2022-10-15", "amount": 0.00}
                ]
            }
            
            # Mock 데이터에서 배당 이력 가져오기
            if symbol in mock_dividend_data:
                dividend_history = []
                for dividend in mock_dividend_data[symbol]:
                    dividend_history.append(DividendData(
                        symbol=symbol,
                        date=dividend["date"],
                        amount=dividend["amount"],
                        type="cash"
                    ))
                print(f"✅ Mock dividend history: Returned {len(dividend_history)} records for {symbol}")
                return dividend_history
            else:
                # 기본 Mock 데이터 (알 수 없는 주식용)
                dividend_history = [
                    DividendData(symbol=symbol, date="2024-03-15", amount=0.50, type="cash"),
                    DividendData(symbol=symbol, date="2023-12-15", amount=0.50, type="cash"),
                    DividendData(symbol=symbol, date="2023-09-15", amount=0.45, type="cash"),
                    DividendData(symbol=symbol, date="2023-06-15", amount=0.45, type="cash"),
                    DividendData(symbol=symbol, date="2023-03-15", amount=0.45, type="cash")
                ]
                print(f"✅ Mock dividend history: Returned default data for {symbol}")
                return dividend_history
                
        except Exception as e:
            print(f"❌ Error in get_dividend_history: {e}")
            raise ValueError(f"Failed to fetch dividend history for {symbol}: {str(e)}")

    async def compare_stocks(self, symbols: list) -> list:
        """여러 종목 정보 비교 (Mock Data)"""
        try:
            print(f"🔄 Comparing stocks: {symbols} (Mock Data)")
            
            result = []
            for symbol in symbols:
                try:
                    info = await self.get_stock_info(symbol)
                    if info:
                        result.append(info)
                        print(f"✅ Added {symbol} to comparison")
                    else:
                        print(f"⚠️ No data for {symbol}")
                except Exception as e:
                    print(f"❌ Error processing {symbol}: {e}")
                    continue
            
            print(f"✅ Mock stock comparison: Returned {len(result)} stocks")
            return result
            
        except Exception as e:
            print(f"❌ Error in compare_stocks: {e}")
            raise ValueError(f"Failed to compare stocks: {str(e)}") 

    async def get_company_description(self, symbol: str) -> dict:
        """회사 상세설명 조회 (Mock Data)"""
        try:
            print(f"🔄 Fetching company description for {symbol} (Mock Data)")
            
            # Mock 회사 설명 데이터 (2025-07-27 기준 - 실제 Yahoo Finance 데이터)
            mock_descriptions = {
                "AAPL": {
                    "name": "Apple Inc.",
                    "shortName": "Apple",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "country": "United States",
                    "website": "https://www.apple.com",
                    "description": "애플은 전 세계적으로 스마트폰, 개인용 컴퓨터, 태블릿, 웨어러블 기기 및 액세서리를 설계, 제조 및 판매하는 기업입니다. 회사는 iPhone 스마트폰 라인, Mac 개인용 컴퓨터 라인, iPad 다목적 태블릿 라인, AirPods, Apple TV, Apple Watch, Beats 제품 및 HomePod을 포함한 웨어러블, 홈 및 액세서리를 제공합니다. 또한 AppleCare 지원 및 클라우드 서비스를 제공하며, 고객이 애플리케이션 및 책, 음악, 비디오, 게임, 팟캐스트와 같은 디지털 콘텐츠를 발견하고 다운로드할 수 있도록 하는 App Store를 포함한 다양한 플랫폼을 운영합니다. 또한 Apple Arcade 게임 구독 서비스, Apple Fitness+ 개인 맞춤형 피트니스 서비스, 사용자에게 주문형 라디오 스테이션이 있는 큐레이션된 청취 경험을 제공하는 Apple Music, 구독 뉴스 및 잡지 서비스인 Apple News+, 독점 오리지널 콘텐츠를 제공하는 Apple TV+, 공동 브랜드 신용카드인 Apple Card, 현금 없는 결제 서비스인 Apple Pay와 같은 다양한 구독 기반 서비스를 제공합니다. 회사는 소비자, 중소기업, 교육, 기업 및 정부 시장에 서비스를 제공합니다. App Store를 통해 제품용 타사 애플리케이션을 배포합니다. 회사는 또한 소매 및 온라인 스토어, 직접 영업팀, 타사 셀룰러 네트워크 사업자, 도매업자, 소매업자 및 재판매업자를 통해 제품을 판매합니다. 애플은 1976년에 설립되었으며 캘리포니아 쿠퍼티노에 본사를 두고 있습니다.",
                    "originalDescription": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, a line of smartphones; Mac, a line of personal computers; iPad, a line of multi-purpose tablets; and wearables, home, and accessories comprising AirPods, Apple TV, Apple Watch, Beats products, and HomePod. It also provides AppleCare support and cloud services; and operates various platforms, including the App Store that allow customers to discover and download applications and digital content, such as books, music, video, games, and podcasts, as well as advertising services include third-party licensing arrangements and its own advertising platforms. In addition, the company offers various subscription-based services, such as Apple Arcade, a game subscription service; Apple Fitness+, a personalized fitness service; Apple Music, which offers users a curated listening experience with on-demand radio stations; Apple News+, a subscription news and magazine service; Apple TV+, which offers exclusive original content; Apple Card, a co-branded credit card; and Apple Pay, a cashless payment service, as well as licenses its intellectual property. The company serves consumers, and small and mid-sized businesses; and the education, enterprise, and government markets. It distributes third-party applications for its products through the App Store. The company also sells its products through its retail and online stores, and direct sales force; and third-party cellular network carriers, wholesalers, retailers, and resellers. Apple Inc. was founded in 1976 and is headquartered in Cupertino, California.",
                    "employees": 164000,
                    "founded": "1976",
                    "ceo": "Mr. Timothy D. Cook",
                    "headquarters": "Cupertino, CA, United States",
                    "marketCap": 3194468958208,
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
                    "industry": "Software - Infrastructure",
                    "country": "United States",
                    "website": "https://www.microsoft.com",
                    "description": "마이크로소프트는 전 세계적으로 소프트웨어, 서비스, 디바이스 및 솔루션을 개발하고 지원하는 기업입니다. 생산성 및 비즈니스 프로세스 세그먼트는 Office, Exchange, SharePoint, Microsoft Teams, Office365 보안 및 규정 준수, Microsoft Viva 및 Microsoft 365 Copilot을 제공합니다. 또한 Microsoft 365 소비자 구독, 온프레미스 라이선스 Office 및 기타 Office 서비스와 같은 Office 소비자 서비스를 제공합니다. 이 세그먼트는 또한 LinkedIn을 제공하며, ERP, CRM, Power Apps 및 Power Automate를 아우르는 지능형 클라우드 기반 애플리케이션 세트인 Dynamics 365와 온프레미스 ERP 및 CRM 애플리케이션을 포함한 Dynamics 비즈니스 솔루션을 제공합니다. 지능형 클라우드 세그먼트는 Azure 및 기타 클라우드 서비스와 같은 서버 제품 및 클라우드 서비스, SQL 및 Windows Server, Visual Studio, System Center 및 관련 클라이언트 액세스 라이선스, Nuance 및 GitHub를 제공합니다. 또한 엔터프라이즈 지원 서비스, 업계 솔루션 및 Nuance 전문 서비스를 포함한 엔터프라이즈 서비스를 제공합니다. 개인용 컴퓨팅 세그먼트는 Windows OEM 라이선싱 및 Windows 운영 체제의 기타 비볼륨 라이선싱을 포함한 Windows, Windows 운영 체제의 볼륨 라이선싱, Windows 클라우드 서비스 및 기타 Windows 상용 제품을 포함한 Windows 상용, 특허 라이선싱 및 Windows IoT를 제공합니다. 또한 Surface, HoloLens 및 PC 액세서리와 같은 디바이스를 제공합니다. 또한 이 세그먼트는 Xbox 하드웨어 및 콘텐츠, 자사 및 타사 콘텐츠를 포함한 게임, Xbox Game Pass 및 기타 구독, 클라우드 게임, 광고, 타사 디스크 로열티 및 기타 클라우드 서비스, Bing, Microsoft News 및 Edge, 타사 제휴사를 포함한 검색 및 뉴스 광고, 자연 기반 탄소 제거 크레딧을 제공합니다. 회사는 OEM, 유통업체 및 재판매업자를 통해 제품을 판매하며, 디지털 마켓플레이스, 온라인 및 소매점을 통해 직접 판매합니다. 회사는 1975년에 설립되었으며 워싱턴 레드먼드에 본사를 두고 있습니다.",
                    "originalDescription": "Microsoft Corporation develops and supports software, services, devices and solutions worldwide. The Productivity and Business Processes segment offers office, exchange, SharePoint, Microsoft Teams, office365 Security and Compliance, Microsoft viva, and Microsoft 365 copilot; and office consumer services, such as Microsoft 365 consumer subscriptions, Office licensed on-premises, and other office services. This segment also provides LinkedIn; and dynamics business solutions, including Dynamics 365, a set of intelligent, cloud-based applications across ERP, CRM, power apps, and power automate; and on-premises ERP and CRM applications. The Intelligent Cloud segment offers server products and cloud services, such as azure and other cloud services; SQL and windows server, visual studio, system center, and related client access licenses, as well as nuance and GitHub; and enterprise services including enterprise support services, industry solutions, and nuance professional services. The More Personal Computing segment offers Windows, including windows OEM licensing and other non-volume licensing of the Windows operating system; Windows commercial comprising volume licensing of the Windows operating system, windows cloud services, and other Windows commercial offerings; patent licensing; and windows Internet of Things; and devices, such as surface, HoloLens, and PC accessories. Additionally, this segment provides gaming, which includes Xbox hardware and content, and first- and third-party content; Xbox game pass and other subscriptions, cloud gaming, advertising, third-party disc royalties, and other cloud services; search and news advertising, which includes Bing, Microsoft News and Edge, and third-party affiliates; and nature-based carbon removal credits. The company sells its products through OEMs, distributors, and resellers; and directly through digital marketplaces, online, and retail stores. The company was founded in 1975 and is headquartered in Redmond, Washington.",
                    "employees": 228000,
                    "founded": "1975",
                    "ceo": "Mr. Satya Nadella",
                    "headquarters": "Redmond, WA, United States",
                    "marketCap": 3818170351616,
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
                    "sector": "Communication Services",
                    "industry": "Internet Content & Information",
                    "country": "United States",
                    "website": "https://abc.xyz",
                    "description": "알파벳은 미국, 유럽, 중동, 아프리카, 아시아 태평양, 캐나다 및 라틴 아메리카에서 다양한 제품 및 플랫폼을 제공합니다. Google Services, Google Cloud 및 Other Bets 세그먼트를 통해 운영됩니다. Google Services 세그먼트는 광고, Android, Chrome, 디바이스, Gmail, Google Drive, Google Maps, Google Photos, Google Play, Search 및 YouTube를 포함한 제품 및 서비스를 제공합니다. 또한 Google Play 및 YouTube에서 앱 및 인앱 구매 및 디지털 콘텐츠 판매에 참여하며, 디바이스 및 YouTube 소비자 구독 서비스 제공에도 참여합니다. Google Cloud 세그먼트는 AI 인프라, Vertex AI 플랫폼, 사이버 보안, 데이터 및 분석 및 기타 서비스를 제공합니다. Google Workspace는 Calendar, Gmail, Docs, Drive 및 Meet와 같은 기업용 클라우드 기반 커뮤니케이션 및 협업 도구를 포함하며, 엔터프라이즈 고객을 위한 기타 서비스도 제공합니다. Other Bets 세그먼트는 의료 관련 및 인터넷 서비스를 판매합니다. 회사는 1998년에 설립되었으며 캘리포니아 마운틴 뷰에 본사를 두고 있습니다.",
                    "originalDescription": "Alphabet Inc. offers various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America. It operates through Google Services, Google Cloud, and Other Bets segments. The Google Services segment provides products and services, including ads, Android, Chrome, devices, Gmail, Google Drive, Google Maps, Google Photos, Google Play, Search, and YouTube. It is also involved in the sale of apps and in-app purchases and digital content in the Google Play and YouTube; and devices, as well as in the provision of YouTube consumer subscription services. The Google Cloud segment offers AI infrastructure, Vertex AI platform, cybersecurity, data and analytics, and other services; Google Workspace that include cloud-based communication and collaboration tools for enterprises, such as Calendar, Gmail, Docs, Drive, and Meet; and other services for enterprise customers. The Other Bets segment sells healthcare-related and internet services. The company was incorporated in 1998 and is headquartered in Mountain View, California.",
                    "employees": 187103,
                    "founded": "1998",
                    "ceo": "Mr. Sundar Pichai",
                    "headquarters": "Mountain View, CA, United States",
                    "marketCap": 2341206228992,
                    "enterpriseValue": 2200000000000,
                    "revenue": 307394000000,
                    "profitMargin": 0.21,
                    "operatingMargin": 0.26,
                    "returnOnEquity": 0.23,
                    "returnOnAssets": 0.18,
                    "debtToEquity": 0.05
                },
                "AMZN": {
                    "name": "Amazon.com Inc.",
                    "shortName": "Amazon",
                    "sector": "Consumer Cyclical",
                    "industry": "Internet Retail",
                    "country": "United States",
                    "website": "https://www.amazon.com",
                    "description": "아마존은 북미 및 국제적으로 소비자 제품 및 구독의 소매 판매에 종사합니다. 회사는 북미, 국제 및 Amazon Web Services(AWS) 세 개의 세그먼트를 통해 운영됩니다. 물리적 매장과 온라인 매장을 통해 제3자 판매자로부터 재판매를 위해 구매한 상품 및 콘텐츠를 판매합니다. 회사는 또한 Kindle, Fire 태블릿, Fire TV, Echo, Ring 및 기타 디바이스를 포함한 전자 디바이스를 제조 및 판매하며, 미디어 콘텐츠를 개발하고 제작합니다. 또한 판매자가 자사 웹사이트와 자체 웹사이트에서 제품을 판매할 수 있게 하는 프로그램과 저자, 음악가, 영화 제작자, 스킬 및 앱 개발자 등이 콘텐츠를 게시하고 판매할 수 있게 하는 프로그램을 제공합니다. 또한 컴퓨팅, 스토리지, 데이터베이스, 분석, 머신러닝 및 기타 서비스와 함께 이행, 광고 및 디지털 콘텐츠 구독을 제공합니다. 또한 영화 및 TV 에피소드 스트리밍 및 기타 디지털 콘텐츠에 대한 액세스를 제공하는 멤버십 프로그램인 Amazon Prime을 제공합니다. 회사는 소비자, 판매자, 개발자, 기업 및 콘텐츠 제작자에게 서비스를 제공합니다. 아마존은 1994년에 설립되었으며 워싱턴 시애틀에 본사를 두고 있습니다.",
                    "originalDescription": "Amazon.com Inc. engages in the retail sale of consumer products and subscriptions in North America and internationally. The company operates through three segments: North America, International, and Amazon Web Services (AWS). It sells merchandise and content purchased for resale from third-party sellers through physical stores and online stores. The company also manufactures and sells electronic devices, including Kindle, Fire tablet, Fire TV, Echo, Ring, and other devices; and develops and produces media content. In addition, it offers programs that enable sellers to sell their products on its websites, as well as their own websites; and programs that allow authors, musicians, filmmakers, skill and app developers, and others to publish and sell content. Further, the company provides compute, storage, database, analytics, machine learning, and other services, as well as fulfillment, advertising, and digital content subscriptions. Additionally, it offers Amazon Prime, a membership program, which provides access to the streaming of movies and television episodes, and other digital content. The company serves consumers, sellers, developers, enterprises, and content creators. Amazon.com Inc. was founded in 1994 and is headquartered in Seattle, Washington.",
                    "employees": 1608000,
                    "founded": "1994",
                    "ceo": "Mr. Andrew R. Jassy",
                    "headquarters": "Seattle, WA, United States",
                    "marketCap": 2457059721216,
                    "enterpriseValue": 2500000000000,
                    "revenue": 574785000000,
                    "profitMargin": 0.05,
                    "operatingMargin": 0.07,
                    "returnOnEquity": 0.15,
                    "returnOnAssets": 0.06,
                    "debtToEquity": 0.60
                },
                "TSLA": {
                    "name": "Tesla Inc.",
                    "shortName": "Tesla",
                    "sector": "Consumer Cyclical",
                    "industry": "Auto Manufacturers",
                    "country": "United States",
                    "website": "https://www.tesla.com",
                    "description": "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems in the United States, China, and internationally. The company operates in two segments, Automotive; and Energy Generation and Storage. The Automotive segment offers electric vehicles, as well as sells automotive regulatory credits; and non-warranty after-sales vehicle, used vehicles, body shop and parts, supercharging, retail merchandise, and vehicle insurance services. This segment also provides sedans and sport utility vehicles through direct and used vehicle sales, a network of Tesla Superchargers, and in-app upgrades; purchase financing and leasing services; services for electric vehicles through its company-owned service locations and Tesla mobile service technicians; and vehicle limited warranties and extended service plans. The Energy Generation and Storage segment engages in the design, manufacture, installation, sale, and leasing of solar energy generation and energy storage products, and related services to residential, commercial, and industrial customers and utilities through its website, stores, and galleries, as well as through a network of channel partners. This segment also provides services and repairs to its energy product customers, including under warranty; and various financing options to its residential customers. The company was formerly known as Tesla Motors, Inc. and changed its name to Tesla, Inc. in February 2017. Tesla, Inc. was incorporated in 2003 and is headquartered in Austin, Texas.",
                    "originalDescription": "Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems in the United States, China, and internationally. The company operates in two segments, Automotive; and Energy Generation and Storage. The Automotive segment offers electric vehicles, as well as sells automotive regulatory credits; and non-warranty after-sales vehicle, used vehicles, body shop and parts, supercharging, retail merchandise, and vehicle insurance services. This segment also provides sedans and sport utility vehicles through direct and used vehicle sales, a network of Tesla Superchargers, and in-app upgrades; purchase financing and leasing services; services for electric vehicles through its company-owned service locations and Tesla mobile service technicians; and vehicle limited warranties and extended service plans. The Energy Generation and Storage segment engages in the design, manufacture, installation, sale, and leasing of solar energy generation and energy storage products, and related services to residential, commercial, and industrial customers and utilities through its website, stores, and galleries, as well as through a network of channel partners. This segment also provides services and repairs to its energy product customers, including under warranty; and various financing options to its residential customers. The company was formerly known as Tesla Motors, Inc. and changed its name to Tesla, Inc. in February 2017. Tesla, Inc. was incorporated in 2003 and is headquartered in Austin, Texas.",
                    "employees": 125665,
                    "founded": "2003",
                    "ceo": "Mr. Elon R. Musk",
                    "headquarters": "Austin, TX, United States",
                    "marketCap": 1019435745280,
                    "enterpriseValue": 750000000000,
                    "revenue": 96773000000,
                    "profitMargin": 0.15,
                    "operatingMargin": 0.09,
                    "returnOnEquity": 0.25,
                    "returnOnAssets": 0.12,
                    "debtToEquity": 0.08
                },
                "PLTR": {
                    "name": "Palantir Technologies Inc.",
                    "shortName": "Palantir",
                    "sector": "Technology",
                    "industry": "Software - Infrastructure",
                    "country": "United States",
                    "website": "https://www.palantir.com",
                    "description": "팔란티어 테크놀로지는 미국, 영국 및 국제적으로 대테러리즘 수사 및 작전을 지원하기 위해 정보 기관을 위한 소프트웨어 플랫폼을 구축하고 배포합니다. 회사는 신호 정보 소스부터 기밀 정보원의 보고서까지 데이터셋 깊숙이 숨겨진 패턴을 식별할 수 있게 하는 소프트웨어 플랫폼인 Palantir Gotham을 제공하며, 분석가와 운영 사용자 간의 인계를 촉진하여 운영자가 플랫폼 내에서 식별된 위협에 대한 실제 대응을 계획하고 실행할 수 있도록 도와줍니다. 회사는 또한 조직이 데이터에 대한 중앙 운영 시스템을 만들어 운영 방식을 변화시키는 플랫폼인 Palantir Foundry를 제공하며, 개별 사용자가 필요한 데이터를 한 곳에서 통합하고 분석할 수 있게 합니다. 또한 비즈니스 전반에 소프트웨어 및 업데이트를 제공하고 고객이 거의 모든 환경에서 소프트웨어를 배포할 수 있게 하는 Palantir Apollo와 구조화된 데이터와 비구조화된 데이터를 LLM이 이해할 수 있는 객체로 변환하고 조직의 행동과 프로세스를 인간과 LLM 기반 에이전트를 위한 도구로 바꿀 수 있는 오픈소스, 자체 호스팅 및 상용 대규모 언어 모델(LLM)에 대한 통합 액세스를 제공하는 Palantir Artificial Intelligence Platform을 제공합니다. 회사는 2003년에 설립되었으며 콜로라도 덴버에 본사를 두고 있습니다.",
                    "originalDescription": "Palantir Technologies Inc. builds and deploys software platforms for the intelligence community to assist in counterterrorism investigations and operations in the United States, the United Kingdom, and internationally. It provides Palantir Gotham, a software platform, which enables users to identify patterns hidden deep within datasets, ranging from signals intelligence sources to reports from confidential informants, as well as facilitates the hand-off between analysts and operational users, helping operators plan and execute real-world responses to threats that have been identified within the platform. The company also offers Palantir Foundry, a platform that transforms the ways organizations operate by creating a central operating system for their data; and allows individual users to integrate and analyze the data they need in one place. In addition, it provides Palantir Apollo, a software that delivers software and updates across the business, as well as enables customers to deploy their software virtually in any environment; and Palantir Artificial Intelligence Platform that provides unified access to open-source, self-hosted, and commercial large language models (LLMs) that can transform structured and unstructured data into LLM-understandable objects and can turn organizations' actions and processes into tools for humans and LLM-driven agents. The company was incorporated in 2003 and is headquartered in Denver, Colorado.",
                    "employees": 4001,
                    "founded": "2003",
                    "ceo": "Mr. Peter Andreas Thiel J.D.",
                    "headquarters": "Denver, CO, United States",
                    "marketCap": 374753689600,
                    "enterpriseValue": 60000000000,
                    "revenue": 2225000000,
                    "profitMargin": 0.09,
                    "operatingMargin": 0.05,
                    "returnOnEquity": 0.12,
                    "returnOnAssets": 0.08,
                    "debtToEquity": 0.02
                },
                "NVDA": {
                    "name": "NVIDIA Corporation",
                    "shortName": "NVIDIA",
                    "sector": "Technology",
                    "industry": "Semiconductors",
                    "country": "United States",
                    "website": "https://www.nvidia.com",
                    "description": "엔비디아는 전 세계적으로 그래픽 처리 장치(GPU) 및 관련 소프트웨어를 설계, 개발 및 제조합니다. 회사는 게임 및 엔터테인먼트, 전문 시각화, 데이터 센터 및 자동차 시장을 위한 제품을 제공합니다. 게임 및 엔터테인먼트 세그먼트는 게임용 GPU, 게임 콘솔용 GPU, 게임 개발자용 소프트웨어 및 서비스를 제공합니다. 전문 시각화 세그먼트는 워크스테이션용 GPU, 엔터테인먼트 및 방송 산업용 GPU, 엔터프라이즈 그래픽 소프트웨어 및 서비스를 제공합니다. 데이터 센터 세그먼트는 AI, 딥러닝, 고성능 컴퓨팅 및 자율주행을 위한 GPU, 네트워킹 및 스토리지 솔루션을 제공합니다. 자동차 세그먼트는 자율주행 및 인포테인먼트 시스템을 위한 GPU 및 소프트웨어를 제공합니다. 회사는 또한 ARM 기반 CPU, 네트워킹 및 스토리지 솔루션을 제공합니다. 엔비디아는 1993년에 설립되었으며 캘리포니아 산타클라라에 본사를 두고 있습니다.",
                    "originalDescription": "NVIDIA Corporation designs, develops, and manufactures graphics processing units (GPUs) and related software worldwide. The company offers products for gaming and entertainment, professional visualization, data center, and automotive markets. The gaming and entertainment segment provides GPUs for gaming, GPUs for gaming consoles, and software and services for game developers. The professional visualization segment offers GPUs for workstations, GPUs for entertainment and broadcast industries, and enterprise graphics software and services. The data center segment provides GPUs for AI, deep learning, high-performance computing, and autonomous driving, as well as networking and storage solutions. The automotive segment offers GPUs and software for autonomous driving and infotainment systems. The company also provides ARM-based CPUs, networking, and storage solutions. NVIDIA was founded in 1993 and is headquartered in Santa Clara, California.",
                    "employees": 29975,
                    "founded": "1993",
                    "ceo": "Mr. Jensen Huang",
                    "headquarters": "Santa Clara, CA, United States",
                    "marketCap": 4231248740352,
                    "enterpriseValue": 4200000000000,
                    "revenue": 60922000000,
                    "profitMargin": 0.55,
                    "operatingMargin": 0.60,
                    "returnOnEquity": 0.85,
                    "returnOnAssets": 0.45,
                    "debtToEquity": 0.25
                },
                "META": {
                    "name": "Meta Platforms Inc.",
                    "shortName": "Meta",
                    "sector": "Communication Services",
                    "industry": "Internet Content & Information",
                    "country": "United States",
                    "website": "https://www.meta.com",
                    "description": "메타 플랫폼은 전 세계적으로 소셜 미디어 플랫폼을 개발하고 운영합니다. 회사는 Facebook, Instagram, Messenger, WhatsApp 및 기타 앱과 서비스를 통해 사람들이 연결하고, 공유하고, 커뮤니케이션할 수 있게 하는 제품을 제공합니다. 또한 가상현실(VR) 및 증강현실(AR) 제품을 개발하고 있으며, 메타버스 구축을 위한 기술을 개발하고 있습니다. 회사는 주로 디지털 광고를 통해 수익을 창출하며, 광고주가 타겟팅된 광고를 게재할 수 있도록 하는 도구와 서비스를 제공합니다. 또한 개발자가 앱과 서비스를 구축할 수 있도록 하는 플랫폼과 도구를 제공합니다. 메타는 2004년에 설립되었으며 캘리포니아 멘로파크에 본사를 두고 있습니다.",
                    "originalDescription": "Meta Platforms Inc. develops and operates social media platforms worldwide. The company provides products that enable people to connect, share, and communicate through Facebook, Instagram, Messenger, WhatsApp, and other apps and services. It also develops virtual reality (VR) and augmented reality (AR) products and is building technology for the metaverse. The company primarily generates revenue through digital advertising, providing tools and services that enable advertisers to deliver targeted ads. It also provides platforms and tools that enable developers to build apps and services. Meta was founded in 2004 and is headquartered in Menlo Park, California.",
                    "employees": 86482,
                    "founded": "2004",
                    "ceo": "Mr. Mark Zuckerberg",
                    "headquarters": "Menlo Park, CA, United States",
                    "marketCap": 1791912706048,
                    "enterpriseValue": 1700000000000,
                    "revenue": 134902000000,
                    "profitMargin": 0.25,
                    "operatingMargin": 0.30,
                    "returnOnEquity": 0.20,
                    "returnOnAssets": 0.15,
                    "debtToEquity": 0.20
                },
                "BRK-B": {
                    "name": "Berkshire Hathaway Inc.",
                    "shortName": "Berkshire",
                    "sector": "Financial Services",
                    "industry": "Insurance - Diversified",
                    "country": "United States",
                    "website": "https://www.berkshirehathaway.com",
                    "description": "버크셔 해서웨이는 다양한 사업을 소유하고 운영하는 지주회사입니다. 회사는 보험, 철도 운송, 에너지 생산 및 분배, 제조, 소매 및 서비스 사업을 운영합니다. 보험 사업은 자동차, 주택, 생명 및 재산 손해 보험을 제공합니다. 철도 운송 사업은 북미에서 화물 철도 서비스를 제공합니다. 에너지 사업은 전기 및 가스 유틸리티 서비스를 제공합니다. 제조 사업은 다양한 산업 제품을 제조합니다. 소매 사업은 가구, 보석, 의류 및 기타 소비자 제품을 판매합니다. 회사는 또한 다양한 기업에 투자하고 있으며, 주식 포트폴리오를 보유하고 있습니다. 버크셔 해서웨이는 1839년에 설립되었으며 네브래스카 오마하에 본사를 두고 있습니다.",
                    "originalDescription": "Berkshire Hathaway Inc. is a holding company that owns and operates various businesses. The company operates in insurance, railroad transportation, energy generation and distribution, manufacturing, retail, and service businesses. The insurance business provides auto, home, life, and property casualty insurance. The railroad transportation business provides freight rail services in North America. The energy business provides electric and gas utility services. The manufacturing business manufactures various industrial products. The retail business sells furniture, jewelry, clothing, and other consumer products. The company also invests in various companies and holds a portfolio of stocks. Berkshire Hathaway was founded in 1839 and is headquartered in Omaha, Nebraska.",
                    "employees": 372000,
                    "founded": "1839",
                    "ceo": "Mr. Warren E. Buffett",
                    "headquarters": "Omaha, NE, United States",
                    "marketCap": 1044361641984,
                    "enterpriseValue": 1000000000000,
                    "revenue": 364482000000,
                    "profitMargin": 0.15,
                    "operatingMargin": 0.20,
                    "returnOnEquity": 0.10,
                    "returnOnAssets": 0.05,
                    "debtToEquity": 0.30
                },
                "LLY": {
                    "name": "Eli Lilly and Company",
                    "shortName": "Eli Lilly",
                    "sector": "Healthcare",
                    "industry": "Drug Manufacturers - General",
                    "country": "United States",
                    "website": "https://www.lilly.com",
                    "description": "엘리 릴리는 전 세계적으로 인간 의약품을 발견, 개발, 제조 및 판매합니다. 회사는 당뇨병, 암, 면역학, 신경학, 심혈관 질환 및 기타 치료 영역을 위한 제품을 제공합니다. 주요 제품으로는 당뇨병 치료제, 암 치료제, 면역 질환 치료제, 정신 건강 치료제 등이 있습니다. 회사는 또한 동물 건강 제품을 개발하고 판매합니다. 엘리 릴리는 연구 개발에 상당한 투자를 하고 있으며, 새로운 치료법을 개발하기 위해 지속적으로 연구를 진행하고 있습니다. 회사는 전 세계적으로 제품을 판매하며, 다양한 지역에서 임상 시험을 진행하고 있습니다. 엘리 릴리는 1876년에 설립되었으며 인디애나 인디애나폴리스에 본사를 두고 있습니다.",
                    "originalDescription": "Eli Lilly and Company discovers, develops, manufactures, and sells human pharmaceuticals worldwide. The company offers products for diabetes, cancer, immunology, neuroscience, cardiovascular diseases, and other therapeutic areas. Key products include diabetes treatments, cancer treatments, immunology treatments, and mental health treatments. The company also develops and sells animal health products. Eli Lilly invests significantly in research and development and continuously conducts research to develop new treatments. The company sells products worldwide and conducts clinical trials in various regions. Eli Lilly was founded in 1876 and is headquartered in Indianapolis, Indiana.",
                    "employees": 42000,
                    "founded": "1876",
                    "ceo": "Mr. David A. Ricks",
                    "headquarters": "Indianapolis, IN, United States",
                    "marketCap": 729581092864,
                    "enterpriseValue": 700000000000,
                    "revenue": 34124000000,
                    "profitMargin": 0.20,
                    "operatingMargin": 0.25,
                    "returnOnEquity": 0.45,
                    "returnOnAssets": 0.15,
                    "debtToEquity": 0.40
                },
                "TSM": {
                    "name": "Taiwan Semiconductor Manufacturing",
                    "shortName": "TSMC",
                    "sector": "Technology",
                    "industry": "Semiconductors",
                    "country": "Taiwan",
                    "website": "https://www.tsmc.com",
                    "description": "대만 반도체 제조(TSMC)는 전 세계적으로 반도체를 제조하는 기업입니다. 회사는 다양한 고객을 위한 반도체 칩의 설계, 개발, 제조, 테스트 및 판매를 담당합니다. TSMC는 주로 다른 회사들이 설계한 반도체를 제조하는 파운드리 서비스를 제공합니다. 회사는 다양한 기술 노드에서 반도체를 제조하며, 최신 기술을 지속적으로 개발하고 있습니다. 주요 고객으로는 Apple, NVIDIA, AMD, Qualcomm 등이 있습니다. TSMC는 전 세계적으로 사업을 운영하며, 대만에 주요 생산 시설을 보유하고 있습니다. 회사는 반도체 산업의 기술 발전을 주도하고 있으며, 지속적으로 연구 개발에 투자하고 있습니다. TSMC는 1987년에 설립되었으며 대만 신주에 본사를 두고 있습니다.",
                    "originalDescription": "Taiwan Semiconductor Manufacturing Company (TSMC) manufactures semiconductors worldwide. The company is responsible for the design, development, manufacturing, testing, and sale of semiconductor chips for various customers. TSMC primarily provides foundry services, manufacturing semiconductors designed by other companies. The company manufactures semiconductors at various technology nodes and continuously develops the latest technologies. Key customers include Apple, NVIDIA, AMD, and Qualcomm. TSMC operates worldwide and has major production facilities in Taiwan. The company leads technological advancement in the semiconductor industry and continuously invests in research and development. TSMC was founded in 1987 and is headquartered in Hsinchu, Taiwan.",
                    "employees": 73000,
                    "founded": "1987",
                    "ceo": "Dr. C.C. Wei",
                    "headquarters": "Hsinchu, Taiwan",
                    "marketCap": 1273809338368,
                    "enterpriseValue": 1200000000000,
                    "revenue": 84500000000,
                    "profitMargin": 0.40,
                    "operatingMargin": 0.45,
                    "returnOnEquity": 0.35,
                    "returnOnAssets": 0.20,
                    "debtToEquity": 0.15
                },
                "V": {
                    "name": "Visa Inc.",
                    "shortName": "Visa",
                    "sector": "Financial Services",
                    "industry": "Credit Services",
                    "country": "United States",
                    "website": "https://www.visa.com",
                    "description": "비자는 전 세계적으로 디지털 결제를 위한 기술을 개발하고 운영합니다. 회사는 신용카드, 직불카드, 선불카드 및 기타 전자 결제 솔루션을 제공합니다. 비자는 결제 네트워크를 운영하며, 상인, 금융 기관, 정부 및 기타 조직이 전자 결제를 처리할 수 있도록 하는 서비스를 제공합니다. 회사는 또한 사이버 보안, 데이터 분석 및 기타 금융 기술 서비스를 제공합니다. 비자는 전 세계적으로 사업을 운영하며, 다양한 지역에서 현지화된 서비스를 제공합니다. 회사는 지속적으로 새로운 결제 기술을 개발하고 있으며, 모바일 결제, 디지털 지갑 및 기타 혁신적인 결제 솔루션에 투자하고 있습니다. 비자는 1958년에 설립되었으며 캘리포니아 샌프란시스코에 본사를 두고 있습니다.",
                    "originalDescription": "Visa Inc. develops and operates technology for digital payments worldwide. The company provides credit cards, debit cards, prepaid cards, and other electronic payment solutions. Visa operates a payment network and provides services that enable merchants, financial institutions, governments, and other organizations to process electronic payments. The company also provides cybersecurity, data analytics, and other financial technology services. Visa operates worldwide and provides localized services in various regions. The company continuously develops new payment technologies and invests in mobile payments, digital wallets, and other innovative payment solutions. Visa was founded in 1958 and is headquartered in San Francisco, California.",
                    "employees": 26500,
                    "founded": "1958",
                    "ceo": "Mr. Ryan McInerney",
                    "headquarters": "San Francisco, CA, United States",
                    "marketCap": 697477693440,
                    "enterpriseValue": 650000000000,
                    "revenue": 32300000000,
                    "profitMargin": 0.50,
                    "operatingMargin": 0.65,
                    "returnOnEquity": 0.40,
                    "returnOnAssets": 0.20,
                    "debtToEquity": 0.25
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

            # Mock 데이터로 시가총액 상위 10개 주식 (2025-07-27 기준 - 실제 Yahoo Finance 데이터) - 최신 업데이트
            top_stocks = [
                {
                    "symbol": "NVDA",
                    "name": "NVIDIA Corporation",
                    "price": 173.5,
                    "change": -0.24,
                    "changePercent": -0.138,
                    "marketCap": 4231248740352,  # 4.23T
                    "volume": 120814633
                },
                {
                    "symbol": "MSFT",
                    "name": "Microsoft Corporation",
                    "price": 513.71,
                    "change": 2.83,
                    "changePercent": 0.554,
                    "marketCap": 3818170351616,  # 3.82T
                    "volume": 18998701
                },
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "price": 213.88,
                    "change": 0.12,
                    "changePercent": 0.056,
                    "marketCap": 3194468958208,  # 3.19T
                    "volume": 38585030
                },
                {
                    "symbol": "AMZN",
                    "name": "Amazon.com Inc.",
                    "price": 231.44,
                    "change": -0.79,
                    "changePercent": -0.34,
                    "marketCap": 2457059721216,  # 2.46T
                    "volume": 28339929
                },
                {
                    "symbol": "GOOGL",
                    "name": "Alphabet Inc.",
                    "price": 193.18,
                    "change": 1.01,
                    "changePercent": 0.526,
                    "marketCap": 2341206228992,  # 2.34T
                    "volume": 39519098
                },
                {
                    "symbol": "META",
                    "name": "Meta Platforms Inc.",
                    "price": 712.68,
                    "change": -2.12,
                    "changePercent": -0.297,
                    "marketCap": 1791912706048,  # 1.79T
                    "volume": 8239722
                },
                {
                    "symbol": "AVGO",
                    "name": "Broadcom Inc.",
                    "price": 290.18,
                    "change": 1.47,
                    "changePercent": 0.51,
                    "marketCap": 1364852867072,  # 1.36T
                    "volume": 11906123
                },
                {
                    "symbol": "TSM",
                    "name": "Taiwan Semiconductor Manufacturing Company Limited",
                    "price": 245.6,
                    "change": 4.0,
                    "changePercent": 1.66,
                    "marketCap": 1273809338368,  # 1.27T
                    "volume": 11531815
                },
                {
                    "symbol": "BRK-B",
                    "name": "Berkshire Hathaway Inc.",
                    "price": 484.07,
                    "change": 3.47,
                    "changePercent": 0.72,
                    "marketCap": 1044361641984,  # 1.04T
                    "volume": 4194066
                },
                {
                    "symbol": "TSLA",
                    "name": "Tesla, Inc.",
                    "price": 316.06,
                    "change": 10.76,
                    "changePercent": 3.52,
                    "marketCap": 1019435745280,  # 1.02T
                    "volume": 147147702
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
        """지수별 상위 주식 조회 (Mock Data)"""
        try:
            # 캐시된 데이터 사용
            cached_data = self._get_cache(self._get_cache_key('INDEX_STOCKS', index_name=index_name))
            if cached_data:
                print(f"✅ Returning cached index stocks for {index_name}")
                return cached_data

            print(f"🔄 Fetching index stocks for {index_name} (Mock Data)")

            # Mock 지수별 주식 데이터
            mock_index_data = {
                "dow": [
                    {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 513.71, "change": 2.83, "changePercent": 0.55, "marketCap": 3818170351616, "volume": 18998701},
                    {"symbol": "AAPL", "name": "Apple Inc.", "price": 213.88, "change": 0.12, "changePercent": 0.06, "marketCap": 3194468958208, "volume": 38585030},
                    {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "price": 485.60, "change": 3.40, "changePercent": 0.70, "marketCap": 450000000000, "volume": 5000000},
                    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "price": 195.50, "change": 1.20, "changePercent": 0.62, "marketCap": 580000000000, "volume": 12000000},
                    {"symbol": "V", "name": "Visa Inc.", "price": 295.50, "change": 0.70, "changePercent": 0.24, "marketCap": 697477693440, "volume": 15000000},
                    {"symbol": "JNJ", "name": "Johnson & Johnson", "price": 165.30, "change": -0.70, "changePercent": -0.42, "marketCap": 400000000000, "volume": 8000000},
                    {"symbol": "PG", "name": "Procter & Gamble Co.", "price": 158.20, "change": 0.80, "changePercent": 0.51, "marketCap": 380000000000, "volume": 9000000},
                    {"symbol": "HD", "name": "Home Depot Inc.", "price": 385.40, "change": -2.10, "changePercent": -0.54, "marketCap": 380000000000, "volume": 7000000},
                    {"symbol": "MA", "name": "Mastercard Inc.", "price": 425.80, "change": 1.20, "changePercent": 0.28, "marketCap": 400000000000, "volume": 6000000},
                    {"symbol": "DIS", "name": "Walt Disney Co.", "price": 95.20, "change": -0.80, "changePercent": -0.83, "marketCap": 180000000000, "volume": 12000000}
                ],
                "nasdaq": [
                    {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 173.50, "change": -0.24, "changePercent": -0.14, "marketCap": 4231248740352, "volume": 120814633},
                    {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 513.71, "change": 2.83, "changePercent": 0.55, "marketCap": 3818170351616, "volume": 18998701},
                    {"symbol": "AAPL", "name": "Apple Inc.", "price": 213.88, "change": 0.12, "changePercent": 0.06, "marketCap": 3194468958208, "volume": 38585030},
                    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "price": 231.44, "change": -0.79, "changePercent": -0.34, "marketCap": 2457059721216, "volume": 28339929},
                    {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 193.18, "change": 1.01, "changePercent": 0.53, "marketCap": 2341206228992, "volume": 39519098},
                    {"symbol": "META", "name": "Meta Platforms, Inc.", "price": 712.68, "change": -2.12, "changePercent": -0.30, "marketCap": 1791912706048, "volume": 8239722},
                    {"symbol": "AVGO", "name": "Broadcom Inc.", "price": 290.18, "change": 1.47, "changePercent": 0.51, "marketCap": 1364852867072, "volume": 11906123},
                    {"symbol": "TSLA", "name": "Tesla, Inc.", "price": 316.06, "change": 10.76, "changePercent": 3.52, "marketCap": 1019435745280, "volume": 147147702},
                    {"symbol": "ORCL", "name": "Oracle Corporation", "price": 245.12, "change": 2.29, "changePercent": 0.94, "marketCap": 688500375552, "volume": 5685817},
                    {"symbol": "NFLX", "name": "Netflix, Inc.", "price": 1180.49, "change": -0.27, "changePercent": -0.02, "marketCap": 501620899840, "volume": 2621859}
                ],
                "sp500": [
                    {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 173.50, "change": -0.24, "changePercent": -0.14, "marketCap": 4231248740352, "volume": 120814633},
                    {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 513.71, "change": 2.83, "changePercent": 0.55, "marketCap": 3818170351616, "volume": 18998701},
                    {"symbol": "AAPL", "name": "Apple Inc.", "price": 213.88, "change": 0.12, "changePercent": 0.06, "marketCap": 3194468958208, "volume": 38585030},
                    {"symbol": "AMZN", "name": "Amazon.com Inc.", "price": 231.44, "change": -0.79, "changePercent": -0.34, "marketCap": 2457059721216, "volume": 45678901},
                    {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 193.18, "change": 1.01, "changePercent": 0.53, "marketCap": 2341206228992, "volume": 23456789},
                    {"symbol": "META", "name": "Meta Platforms Inc.", "price": 712.68, "change": -2.12, "changePercent": -0.30, "marketCap": 1791912706048, "volume": 15678901},
                    {"symbol": "BRK-B", "name": "Berkshire Hathaway Inc.", "price": 484.07, "change": 3.47, "changePercent": 0.72, "marketCap": 1044361641984, "volume": 4194066},
                    {"symbol": "LLY", "name": "Eli Lilly and Company", "price": 812.69, "change": 7.26, "changePercent": 0.90, "marketCap": 729581092864, "volume": 2974840},
                    {"symbol": "TSM", "name": "Taiwan Semiconductor Manufacturing", "price": 245.6, "change": 4.0, "changePercent": 1.66, "marketCap": 1273809338368, "volume": 11531815},
                    {"symbol": "V", "name": "Visa Inc.", "price": 295.50, "change": 0.70, "changePercent": 0.24, "marketCap": 697477693440, "volume": 15000000}
                ],
                "russell2000": [
                    {"symbol": "IWM", "name": "iShares Russell 2000 ETF", "price": 185.40, "change": 1.20, "changePercent": 0.65, "marketCap": 55000000000, "volume": 25000000},
                    {"symbol": "SMH", "name": "VanEck Vectors Semiconductor ETF", "price": 245.60, "change": 3.40, "changePercent": 1.40, "marketCap": 12000000000, "volume": 8000000},
                    {"symbol": "XBI", "name": "SPDR S&P Biotech ETF", "price": 85.20, "change": -0.80, "changePercent": -0.93, "marketCap": 8000000000, "volume": 12000000},
                    {"symbol": "ARKK", "name": "ARK Innovation ETF", "price": 45.80, "change": 1.20, "changePercent": 2.69, "marketCap": 9000000000, "volume": 15000000},
                    {"symbol": "TQQQ", "name": "ProShares UltraPro QQQ", "price": 65.40, "change": 2.10, "changePercent": 3.32, "marketCap": 15000000000, "volume": 20000000},
                    {"symbol": "SOXL", "name": "Direxion Daily Semiconductor Bull 3x Shares", "price": 35.60, "change": 1.80, "changePercent": 5.32, "marketCap": 5000000000, "volume": 18000000},
                    {"symbol": "LABU", "name": "Direxion Daily S&P Biotech Bull 3x Shares", "price": 12.40, "change": 0.60, "changePercent": 5.08, "marketCap": 2000000000, "volume": 10000000},
                    {"symbol": "DPST", "name": "Direxion Daily Regional Banks Bull 3x Shares", "price": 28.80, "change": -0.40, "changePercent": -1.37, "marketCap": 3000000000, "volume": 8000000},
                    {"symbol": "ERX", "name": "Direxion Daily Energy Bull 3x Shares", "price": 42.20, "change": 1.60, "changePercent": 3.94, "marketCap": 4000000000, "volume": 12000000},
                    {"symbol": "TMF", "name": "Direxion Daily 20+ Year Treasury Bull 3x Shares", "price": 15.60, "change": -0.20, "changePercent": -1.27, "marketCap": 2500000000, "volume": 6000000}
                ]
            }
            
            # 유효한 지수명인지 확인
            if index_name not in mock_index_data:
                raise ValueError(f"Invalid index name: {index_name}. Must be one of: {list(mock_index_data.keys())}")
            
            # Mock 데이터에서 지수별 주식 정보 가져오기
            stocks = mock_index_data[index_name]
            
            # 시가총액 순으로 정렬
            stocks.sort(key=lambda x: x.get("marketCap", 0), reverse=True)
            
            print(f"✅ Mock index stocks: Returned {len(stocks)} stocks for {index_name}")
            for stock in stocks[:5]:  # 상위 5개만 로깅
                print(f"   {stock['symbol']}: ${stock['price']:.2f} ({stock['changePercent']:+.2f}%)")
            
            # 캐시에 저장 (10분)
            self._set_cache(self._get_cache_key('INDEX_STOCKS', index_name=index_name), stocks, 600)
            
            return stocks
            
        except Exception as e:
            print(f"❌ Error in get_index_stocks: {e}")
            return []

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