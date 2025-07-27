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
        """Get detailed stock information for a single symbol"""
        print(f"🔄 Fetching stock info for {symbol}")
        
        # 캐시 확인
        cache_key = f"stock_info_{symbol}"
        cached_data = self._get_cache(cache_key)
        if cached_data:
            print(f"✅ Using cached data for {symbol}")
            return cached_data
        
        # Rate limiting: 더 긴 대기 시간 적용
        await asyncio.sleep(3.0)  # 2.0s → 3.0s로 증가
        
        try:
            ticker = yf.Ticker(symbol)
            
            # 첫 번째 시도: ticker.info 사용
            try:
                info = ticker.info
                print(f" Raw info for {symbol}: {len(info)} fields")
                
                # 사용 가능한 필드 로깅
                print(f"🔍 Available fields for {symbol}:")
                for key, value in list(info.items())[:10]:  # 처음 10개만 로깅
                    print(f"   {key}: {value}")
                
            except Exception as e:
                print(f"⚠️ ticker.info failed for {symbol}: {e}")
                # 대안: ticker.history 사용
                try:
                    history = ticker.history(period="1d")
                    if not history.empty:
                        latest = history.iloc[-1]
                        info = {
                            'longName': symbol,
                            'currentPrice': float(latest['Close']),
                            'regularMarketVolume': int(latest['Volume']),
                            'fullExchangeName': 'NASDAQ',  # 기본값
                            'sector': 'Unknown',
                            'industry': 'Unknown',
                            'currency': 'USD'
                        }
                        print(f"✅ Using history fallback for {symbol}")
                    else:
                        print(f"❌ No history data for {symbol}")
                        return None
                except Exception as history_error:
                    print(f"❌ History fallback also failed for {symbol}: {history_error}")
                    return None
            
            # StockInfo 객체 생성
            stock_info = StockInfo(
                symbol=symbol,
                name=info.get('longName', symbol),
                currentPrice=info.get('currentPrice', 0.0),
                previousClose=info.get('regularMarketPreviousClose', 0.0),
                change=info.get('regularMarketChange', 0.0),
                changePercent=info.get('regularMarketChangePercent', 0.0),
                high=info.get('regularMarketDayHigh'),
                low=info.get('regularMarketDayLow'),
                volume=info.get('regularMarketVolume'),
                marketCap=info.get('marketCap'),
                peRatio=info.get('trailingPE'),
                dividendYield=info.get('trailingAnnualDividendYield'),
                beta=info.get('beta'),
                fiftyTwoWeekHigh=info.get('fiftyTwoWeekHigh'),
                fiftyTwoWeekLow=info.get('fiftyTwoWeekLow'),
                avgVolume=info.get('averageDailyVolume3Month'),
                currency=info.get('currency', 'USD'),
                exchange=info.get('fullExchangeName', 'NASDAQ'),
                sector=info.get('sector'),
                industry=info.get('industry')
            )
            
            print(f" Stock Info Details for {symbol}:")
            print(f"   Name: {stock_info.name}")
            print(f"   Price: ${stock_info.currentPrice}")
            print(f"   High: ${stock_info.high}")
            print(f"   Low: ${stock_info.low}")
            print(f"   Volume: {stock_info.volume}")
            print(f"   Market Cap: ${stock_info.marketCap}")
            print(f"   Exchange: {stock_info.exchange}")
            print(f"   Sector: {stock_info.sector}")
            
            # 캐시에 저장 (5분 → 10분으로 증가)
            self._set_cache(cache_key, stock_info, 600)
            
            return stock_info
            
        except HTTPError as e:
            if e.response.status_code == 429:
                print(f"⚠️ Rate limit hit for {symbol}, waiting 15 seconds...")
                await asyncio.sleep(15.0)  # 10s → 15s로 증가
                
                # 재시도
                try:
                    await asyncio.sleep(8.0)  # 추가 대기 시간 증가
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    stock_info = StockInfo(
                        symbol=symbol,
                        name=info.get('longName', symbol),
                        currentPrice=info.get('currentPrice', 0.0),
                        previousClose=info.get('regularMarketPreviousClose', 0.0),
                        change=info.get('regularMarketChange', 0.0),
                        changePercent=info.get('regularMarketChangePercent', 0.0),
                        high=info.get('regularMarketDayHigh'),
                        low=info.get('regularMarketDayLow'),
                        volume=info.get('regularMarketVolume'),
                        marketCap=info.get('marketCap'),
                        peRatio=info.get('trailingPE'),
                        dividendYield=info.get('trailingAnnualDividendYield'),
                        beta=info.get('beta'),
                        fiftyTwoWeekHigh=info.get('fiftyTwoWeekHigh'),
                        fiftyTwoWeekLow=info.get('fiftyTwoWeekLow'),
                        avgVolume=info.get('averageDailyVolume3Month'),
                        currency=info.get('currency', 'USD'),
                        exchange=info.get('fullExchangeName', 'NASDAQ'),
                        sector=info.get('sector'),
                        industry=info.get('industry')
                    )
                    
                    self._set_cache(cache_key, stock_info, 600)
                    return stock_info
                    
                except Exception as retry_error:
                    print(f"❌ Retry failed for {symbol}: {retry_error}")
                    return None
            else:
                print(f"❌ HTTP error for {symbol}: {e}")
                return None
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return None
    
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
            print(f"🔍 Searching for: '{query}'")
            
            # 한글 검색어를 영어로 변환
            english_query = self._translate_korean_to_english(query)
            print(f"🔄 Translated to: '{english_query}'")
            
            # 먼저 인기 주식에서 검색 (빠른 응답)
            popular_suggestions = await self._search_popular_stocks(query, limit)
            print(f"📊 Found {len(popular_suggestions)} popular matches")
            
            # 인기 주식에서 충분한 결과를 찾았으면 반환
            if len(popular_suggestions) >= limit:
                return popular_suggestions[:limit]
            
            # Yahoo Finance 검색 시도 (추가 결과용)
            try:
                # 영어 쿼리로 Yahoo Finance 검색
                search_results = yf.Tickers(english_query)
                
                if search_results.tickers:
                    print(f"🔍 Yahoo Finance found {len(search_results.tickers)} results")
                    
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
                            print(f"⚠️ Error processing ticker {ticker.ticker}: {e}")
                            continue
                    
                    # 인기 주식 결과와 합치기
                    existing_symbols = {s.symbol for s in popular_suggestions}
                    for suggestion in suggestions:
                        if suggestion.symbol not in existing_symbols:
                            popular_suggestions.append(suggestion)
                            if len(popular_suggestions) >= limit:
                                break
                else:
                    print("⚠️ No Yahoo Finance results found")
                    
            except Exception as e:
                print(f"⚠️ Yahoo Finance search failed: {e}")
            
            print(f"✅ Total search results: {len(popular_suggestions)}")
            return popular_suggestions[:limit]
            
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
        """시가총액 상위 10개 주식 조회 (단순화된 처리)"""
        try:
            # 캐시된 데이터 사용
            cached_data = self._get_cache(self._get_cache_key('TOP_MARKET_CAP'))
            if cached_data:
                print(f"✅ Returning cached top market cap stocks")
                return cached_data

            # 주요 대형주 티커 리스트 (시가총액 순)
            top_tickers = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", 
                "META", "BRK-B", "LLY", "TSM", "V"
            ]
            
            print(f"🔄 Fetching top market cap stocks for {len(top_tickers)} tickers")
            print(f"📊 Tickers: {', '.join(top_tickers)}")
            
            # 단순화: 하나씩 순차적으로 처리
            top_stocks = []
            for i, ticker in enumerate(top_tickers):
                try:
                    print(f"📊 Processing {i+1}/{len(top_tickers)}: {ticker}")
                    
                    # 각 요청 사이에 충분한 지연
                    if i > 0:
                        print(f"⏳ Waiting 5 seconds between requests...")
                        await asyncio.sleep(5.0)
                    
                    stock_info = await self.get_stock_info(ticker)
                    if stock_info and stock_info.marketCap > 0:
                        stock_data = {
                            "symbol": stock_info.symbol,
                            "name": stock_info.name,
                            "price": stock_info.currentPrice,
                            "change": stock_info.change,
                            "changePercent": stock_info.changePercent,
                            "marketCap": stock_info.marketCap,
                            "volume": stock_info.volume
                        }
                        top_stocks.append(stock_data)
                        print(f"✅ {stock_info.symbol}: ${stock_info.currentPrice:.2f} (시총: ${stock_info.marketCap/1e9:.1f}B)")
                    else:
                        print(f"⚠️ {ticker}: 데이터 없음 또는 시가총액 0")
                        
                except Exception as e:
                    print(f"❌ Error fetching {ticker}: {e}")
                    continue
            
            # 시가총액 순으로 정렬
            top_stocks.sort(key=lambda x: x.get("marketCap", 0), reverse=True)
            
            print(f"🎉 Successfully fetched {len(top_stocks)} stocks")
            
            # 캐시에 저장
            self._set_cache(self._get_cache_key('TOP_MARKET_CAP'), top_stocks)
            
            return top_stocks[:10]  # 상위 10개만 반환
            
            # 결과 변환
            top_stocks = []
            for i, stock_info in enumerate(stock_infos):
                if stock_info and stock_info.marketCap > 0:
                    stock_data = {
                        "symbol": stock_info.symbol,
                        "name": stock_info.name,
                        "price": stock_info.currentPrice,
                        "change": stock_info.change,
                        "changePercent": stock_info.changePercent,
                        "marketCap": stock_info.marketCap,
                        "volume": stock_info.volume
                    }
                    top_stocks.append(stock_data)
                    print(f"✅ {stock_info.symbol}: ${stock_info.currentPrice:.2f} (시총: ${stock_info.marketCap/1e9:.1f}B)")
                else:
                    print(f"⚠️ {top_tickers[i]}: 데이터 없음 또는 시가총액 0")
            
            # 시가총액 순으로 정렬
            top_stocks.sort(key=lambda x: x.get("marketCap", 0), reverse=True)
            
            print(f"🎉 Successfully fetched {len(top_stocks)} stocks")
            
            # 캐시에 저장
            self._set_cache(self._get_cache_key('TOP_MARKET_CAP'), top_stocks)
            
            return top_stocks[:10]  # 상위 10개만 반환
            
        except Exception as e:
            print(f"❌ Failed to get top market cap stocks: {str(e)}")
            import traceback
            traceback.print_exc()
            # 빈 리스트 반환하여 앱이 크래시되지 않도록 함
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