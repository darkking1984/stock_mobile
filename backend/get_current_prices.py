import yfinance as yf
from datetime import datetime

print(f"현재 시스템 날짜: {datetime.now().strftime('%Y-%m-%d')}")

tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'BRK-B', 'LLY', 'TSM', 'V', 'TSLA', 'PLTR']

print("\n현재 주식 가격:")
for ticker in tickers:
    try:
        ticker_obj = yf.Ticker(ticker)
        current_price = ticker_obj.info.get('currentPrice')
        if current_price:
            print(f"{ticker}: ${current_price}")
        else:
            print(f"{ticker}: 데이터 없음")
    except Exception as e:
        print(f"{ticker}: 오류 - {e}") 