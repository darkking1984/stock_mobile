import yfinance as yf
from datetime import datetime

print(f"현재 시스템 날짜: {datetime.now().strftime('%Y-%m-%d')}")

tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'BRK-B', 'LLY', 'TSM', 'V', 'TSLA', 'PLTR']

print("\n=== 주식 상세 정보 ===")
for ticker in tickers:
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        print(f"\n{ticker} - {info.get('longName', 'N/A')}")
        print(f"현재가: ${info.get('currentPrice', 'N/A')}")
        print(f"전일종가: ${info.get('previousClose', 'N/A')}")
        print(f"변동: ${info.get('regularMarketChange', 'N/A')}")
        print(f"변동률: {info.get('regularMarketChangePercent', 'N/A')}%")
        print(f"고가: ${info.get('dayHigh', 'N/A')}")
        print(f"저가: ${info.get('dayLow', 'N/A')}")
        print(f"거래량: {info.get('volume', 'N/A'):,}")
        print(f"시가총액: ${info.get('marketCap', 'N/A'):,}")
        print(f"P/E 비율: {info.get('trailingPE', 'N/A')}")
        print(f"배당수익률: {info.get('dividendYield', 'N/A')}")
        print(f"베타: {info.get('beta', 'N/A')}")
        print(f"52주 최고: ${info.get('fiftyTwoWeekHigh', 'N/A')}")
        print(f"52주 최저: ${info.get('fiftyTwoWeekLow', 'N/A')}")
        print(f"평균거래량: {info.get('averageVolume', 'N/A'):,}")
        print(f"거래소: {info.get('exchange', 'N/A')}")
        print(f"섹터: {info.get('sector', 'N/A')}")
        print(f"산업: {info.get('industry', 'N/A')}")
        print("-" * 50)
        
    except Exception as e:
        print(f"{ticker}: 오류 - {e}")
        print("-" * 50) 