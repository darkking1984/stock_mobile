import yfinance as yf
from typing import Optional, Dict, Any, List
import pandas as pd
import requests
import asyncio
from datetime import datetime, timedelta
from ..models.stock import StockInfo, ChartData, ChartDataPoint, StockSuggestion, FinancialData, DividendData

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
    
    async def get_stock_info(self, symbol: str) -> StockInfo:
        """주식 기본 정보 조회 (캐시 적용)"""
        try:
            # 캐시된 데이터 확인
            cache_key = self._get_cache_key('STOCK_INFO', symbol=symbol)
            cached_data = self._get_cache(cache_key, duration=120)  # 2분 캐시
            
            if cached_data:
                print(f"Returning cached stock info for {symbol}")
                return cached_data
            
            print(f"Fetching stock info for {symbol}")
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            current_price = info.get("currentPrice", 0)
            previous_close = info.get("previousClose", 0)
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close > 0 else 0
            
            stock_info = StockInfo(
                symbol=symbol,
                name=info.get("longName", ""),
                currentPrice=current_price,
                previousClose=previous_close,
                change=change,
                changePercent=change_percent,
                high=info.get("dayHigh", 0),
                low=info.get("dayLow", 0),
                volume=info.get("volume", 0),
                marketCap=info.get("marketCap", 0),
                pe=info.get("trailingPE", 0),
                dividendYield=info.get("dividendYield", 0),
                beta=info.get("beta", 0),
                fiftyTwoWeekHigh=info.get("fiftyTwoWeekHigh", 0),
                fiftyTwoWeekLow=info.get("fiftyTwoWeekLow", 0),
                avgVolume=info.get("averageVolume", 0),
                currency=info.get("currency", "USD"),
                exchange=info.get("exchange", ""),
                sector=info.get("sector", ""),
                industry=info.get("industry", "")
            )
            
            # 캐시에 저장
            self._set_cache(cache_key, stock_info, duration=120)
            
            return stock_info
            
        except Exception as e:
            raise ValueError(f"Failed to fetch stock info for {symbol}: {str(e)}")
    
    async def get_stock_chart(self, symbol: str, period: str = "1y", interval: str = "1d") -> dict:
        """주식 차트 데이터 조회"""
        try:
            print(f"Fetching chart data for {symbol}, period: {period}, interval: {interval}")
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            print(f"Raw history data shape: {hist.shape}")
            print(f"Raw history data columns: {hist.columns.tolist()}")
            print(f"First few rows: {hist.head()}")
            
            data = []
            for index, row in hist.iterrows():
                try:
                    # JSON 직렬화 문제 해결을 위해 모든 값을 기본 타입으로 변환
                    chart_point = {
                        "timestamp": index.isoformat(),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"])
                    }
                    data.append(chart_point)
                    print(f"Created chart point: {chart_point}")
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
                    print(f"Row data: {row}")
                    continue
            
            print(f"Processed {len(data)} chart data points")
            if data:
                print(f"First data point: {data[0]}")
                print(f"Last data point: {data[-1]}")
                print(f"Sample data point keys: {list(data[0].keys())}")
                print(f"Sample data point values: {list(data[0].values())}")
            
            # ChartData 모델 대신 직접 딕셔너리 반환
            result = {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": data
            }
            
            print(f"Returning result with {len(result['data'])} points")
            print(f"Result type: {type(result)}")
            print(f"Result data type: {type(result['data'])}")
            if result['data']:
                print(f"First result data point: {result['data'][0]}")
                print(f"First result data point type: {type(result['data'][0])}")
            
            return result
            
        except Exception as e:
            print(f"Error in get_stock_chart: {e}")
            raise ValueError(f"Failed to fetch chart data for {symbol}: {str(e)}")
    
    async def search_stocks(self, query: str, limit: int = 10) -> List[StockSuggestion]:
        """주식 검색 - 한글 검색 지원"""
        try:
            # 한글 검색어를 영어로 변환
            english_query = self._translate_korean_to_english(query)
            
            # 영어 쿼리로 Yahoo Finance 검색
            search_results = yf.Tickers(english_query)
            
            # 검색 결과가 없으면 기본 인기 주식 목록에서 검색
            if not search_results.tickers:
                return await self._search_popular_stocks(query, limit)
            
            suggestions = []
            for ticker in search_results.tickers[:limit]:
                try:
                    # 티커 정보 가져오기
                    ticker_info = ticker.info
                    
                    # 기본 정보 추출
                    symbol = ticker.ticker
                    name = ticker_info.get("longName", ticker_info.get("shortName", ""))
                    exchange = ticker_info.get("exchange", "")
                    
                    # 유효한 주식인지 확인 (가격 정보가 있는지)
                    if ticker_info.get("currentPrice") or ticker_info.get("regularMarketPrice"):
                        suggestions.append(StockSuggestion(
                            symbol=symbol,
                            name=name,
                            exchange=exchange,
                            type="Common Stock",
                            country="US"
                        ))
                except Exception as e:
                    # 개별 티커 오류는 무시하고 계속 진행
                    continue
            
            # 검색 결과가 부족하면 인기 주식에서 추가 검색
            if len(suggestions) < limit:
                popular_suggestions = await self._search_popular_stocks(query, limit - len(suggestions))
                # 중복 제거
                existing_symbols = {s.symbol for s in suggestions}
                for suggestion in popular_suggestions:
                    if suggestion.symbol not in existing_symbols:
                        suggestions.append(suggestion)
            
            return suggestions[:limit]
            
        except Exception as e:
            # Yahoo Finance 검색 실패 시 인기 주식에서 검색
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
        """인기 주식 목록 조회"""
        try:
            popular_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META"]
            popular_stocks = []
            
            for symbol in popular_symbols:
                try:
                    stock_info = await self.get_stock_info(symbol)
                    popular_stocks.append(stock_info)
                except:
                    continue
            
            return popular_stocks
        except Exception as e:
            raise ValueError(f"Failed to fetch popular stocks: {str(e)}")

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
        """회사 상세설명 조회"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 회사 설명을 한글로 번역
            original_description = info.get("longBusinessSummary", "")
            korean_description = self._translate_to_korean(original_description)
            
            # 회사 기본 정보
            company_info = {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "shortName": info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "country": info.get("country", ""),
                "website": info.get("website", ""),
                "description": korean_description,  # 한글로 번역된 설명
                "originalDescription": original_description,  # 원본 영어 설명도 포함
                "employees": info.get("fullTimeEmployees", 0),
                "founded": info.get("founded", ""),
                "ceo": info.get("companyOfficers", [{}])[0].get("name", "") if info.get("companyOfficers") else "",
                "headquarters": info.get("city", "") + ", " + info.get("state", "") + ", " + info.get("country", ""),
                "marketCap": info.get("marketCap", 0),
                "enterpriseValue": info.get("enterpriseValue", 0),
                "revenue": info.get("totalRevenue", 0),
                "profitMargin": info.get("profitMargins", 0),
                "operatingMargin": info.get("operatingMargins", 0),
                "returnOnEquity": info.get("returnOnEquity", 0),
                "returnOnAssets": info.get("returnOnAssets", 0),
                "debtToEquity": info.get("debtToEquity", 0),
                "currentRatio": info.get("currentRatio", 0),
                "quickRatio": info.get("quickRatio", 0),
                "cashPerShare": info.get("totalCashPerShare", 0),
                "bookValue": info.get("bookValue", 0),
                "priceToBook": info.get("priceToBook", 0),
                "priceToSales": info.get("priceToSalesTrailing12Months", 0),
                "enterpriseToRevenue": info.get("enterpriseToRevenue", 0),
                "enterpriseToEbitda": info.get("enterpriseToEbitda", 0),
            }
            
            return company_info
            
        except Exception as e:
            raise Exception(f"Failed to get company description for {symbol}: {str(e)}") 

    async def get_top_market_cap_stocks(self) -> List[Dict[str, Any]]:
        """시가총액 상위 10개 주식 조회 (최적화된 배치 처리)"""
        try:
            # 캐시된 데이터 사용
            cached_data = self._get_cache(self._get_cache_key('TOP_MARKET_CAP'))
            if cached_data:
                print(f"Returning cached top market cap stocks")
                return cached_data

            # 주요 대형주 티커 리스트 (시가총액 순)
            top_tickers = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", 
                "META", "BRK-B", "LLY", "TSM", "V"
            ]
            
            print(f"Fetching top market cap stocks for {len(top_tickers)} tickers")
            
            # 배치로 주식 정보 가져오기 (동시 처리)
            stock_infos = await self.get_stock_info_batch(top_tickers)
            
            # 결과 변환
            top_stocks = []
            for stock_info in stock_infos:
                if stock_info and stock_info.marketCap > 0:
                    top_stocks.append({
                        "symbol": stock_info.symbol,
                        "name": stock_info.name,
                        "price": stock_info.currentPrice,
                        "change": stock_info.change,
                        "changePercent": stock_info.changePercent,
                        "marketCap": stock_info.marketCap,
                        "volume": stock_info.volume
                    })
            
            # 시가총액 순으로 정렬
            top_stocks.sort(key=lambda x: x.get("marketCap", 0), reverse=True)
            
            print(f"Successfully fetched {len(top_stocks)} stocks")
            
            # 캐시에 저장
            self._set_cache(self._get_cache_key('TOP_MARKET_CAP'), top_stocks)
            
            return top_stocks[:10]  # 상위 10개만 반환
            
        except Exception as e:
            raise Exception(f"Failed to get top market cap stocks: {str(e)}")

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
            
            # 선택된 지수의 구성 주식들
            constituents = index_constituents[index_name]
            
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
            
            return stocks[:10]  # 상위 10개만 반환
            
        except Exception as e:
            raise Exception(f"Failed to get index stocks for {index_name}: {str(e)}")

    async def get_stock_info_batch(self, tickers: List[str]) -> List[Optional[StockInfo]]:
        """여러 주식 정보를 배치로 가져오기"""
        # 캐시된 데이터 사용
        cache_key = self._get_cache_key('BATCH_STOCKS', tickers=tickers)
        cached_data = self._get_cache(cache_key)
        
        if cached_data:
            print(f"Returning cached batch stocks for {len(tickers)} tickers")
            return cached_data

        async def fetch_single_stock(ticker: str) -> Optional[StockInfo]:
            try:
                return await self.get_stock_info(ticker)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                return None
        
        # 동시 요청 제한 (최대 3개)
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def fetch_with_semaphore(ticker: str) -> Optional[StockInfo]:
            async with semaphore:
                return await fetch_single_stock(ticker)
        
        tasks = [fetch_with_semaphore(ticker) for ticker in tickers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 결과 필터링
        stock_infos = []
        for result in results:
            if isinstance(result, StockInfo) and result is not None:
                stock_infos.append(result)
            elif isinstance(result, Exception):
                print(f"Task failed with exception: {result}")
        
        # 캐시에 저장
        self._set_cache(cache_key, stock_infos)
        
        return stock_infos

    # get_index_constituents 메서드는 get_index_stocks로 통합되었으므로 제거 