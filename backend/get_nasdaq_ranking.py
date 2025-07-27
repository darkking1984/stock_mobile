import yfinance as yf
import pandas as pd
from datetime import datetime

def get_nasdaq_top_stocks():
    """Yahoo Finance에서 나스닥 상위 주식 데이터를 가져옵니다."""
    
    # 나스닥 100 지수 구성종목 (NASDAQ-100)
    nasdaq_symbols = [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'PEP',
        'COST', 'ADBE', 'NFLX', 'INTC', 'AMD', 'ORCL', 'CSCO', 'TMUS', 'QCOM', 'INTU',
        'HON', 'ADP', 'ISRG', 'GILD', 'REGN', 'VRTX', 'ADI', 'KLAC', 'LRCX', 'MU',
        'SNPS', 'CDNS', 'MCHP', 'MRVL', 'WDAY', 'ROST', 'MNST', 'ODFL', 'PAYX', 'CPRT',
        'FAST', 'IDXX', 'BIIB', 'ILMN', 'ALGN', 'DXCM', 'VRSK', 'CTAS', 'EXC', 'XEL',
        'WBD', 'LCID', 'RIVN', 'ZS', 'CRWD', 'OKTA', 'TEAM', 'ZM', 'DOCU', 'SNOW',
        'PLTR', 'COIN', 'MELI', 'JD', 'PDD', 'BIDU', 'NTES', 'TCOM', 'VIPS', 'BABA',
        'NIO', 'XP', 'LI', 'XPEV', 'DIDI', 'BILI', 'TME', 'HUYA', 'DOYU', 'FUTU',
        'TIGR', 'DASH', 'UBER', 'LYFT', 'ABNB', 'SPOT', 'PINS', 'SNAP', 'TWTR', 'SQ',
        'PYPL', 'SHOP', 'ROKU', 'TTD', 'MTCH', 'ZM', 'DOCU', 'SNOW', 'PLTR', 'COIN'
    ]
    
    print("나스닥 상위 주식 데이터를 가져오는 중...")
    print(f"조회할 종목 수: {len(nasdaq_symbols)}")
    print("-" * 80)
    
    stock_data = []
    
    for i, symbol in enumerate(nasdaq_symbols, 1):
        try:
            print(f"[{i}/{len(nasdaq_symbols)}] {symbol} 조회 중...")
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 필요한 정보 추출
            market_cap = info.get('marketCap', 0)
            current_price = info.get('currentPrice', 0)
            previous_close = info.get('previousClose', 0)
            
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
            else:
                change = 0
                change_percent = 0
            
            volume = info.get('volume', 0)
            name = info.get('longName', symbol)
            
            if market_cap > 0:  # 시가총액이 있는 종목만 포함
                stock_data.append({
                    'symbol': symbol,
                    'name': name,
                    'price': current_price,
                    'change': round(change, 2),
                    'changePercent': round(change_percent, 2),
                    'marketCap': market_cap,
                    'volume': volume
                })
                print(f"  ✓ {symbol}: ${current_price} ({change_percent:+.2f}%), 시가총액: ${market_cap/1e9:.1f}B")
            else:
                print(f"  ✗ {symbol}: 시가총액 데이터 없음")
                
        except Exception as e:
            print(f"  ✗ {symbol}: 오류 - {str(e)}")
            continue
    
    # 시가총액 순으로 정렬
    stock_data.sort(key=lambda x: x['marketCap'], reverse=True)
    
    print("\n" + "=" * 80)
    print("나스닥 상위 20개 주식 (시가총액 순)")
    print("=" * 80)
    
    for i, stock in enumerate(stock_data[:20], 1):
        market_cap_b = stock['marketCap'] / 1e9
        market_cap_t = stock['marketCap'] / 1e12
        
        if market_cap_t >= 1:
            cap_str = f"${market_cap_t:.2f}T"
        else:
            cap_str = f"${market_cap_b:.1f}B"
            
        print(f"{i:2d}. {stock['symbol']:6s} - {stock['name'][:30]:30s} | "
              f"${stock['price']:8.2f} | {stock['changePercent']:+6.2f}% | {cap_str}")
    
    # 상위 10개만 반환
    top_10 = stock_data[:10]
    
    print("\n" + "=" * 80)
    print("Mock 데이터용 JSON 형식 (상위 10개)")
    print("=" * 80)
    
    for stock in top_10:
        print(f'{{"symbol": "{stock["symbol"]}", "name": "{stock["name"]}", '
              f'"price": {stock["price"]}, "change": {stock["change"]}, '
              f'"changePercent": {stock["changePercent"]}, "marketCap": {stock["marketCap"]}, '
              f'"volume": {stock["volume"]}}},')
    
    return top_10

if __name__ == "__main__":
    top_stocks = get_nasdaq_top_stocks() 