import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 1. 티커 검색
@pytest.mark.asyncio
def test_search_stocks():
    response = client.get("/api/stocks/search", params={"query": "AAPL"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], dict)
    assert "suggestions" in data["data"]
    assert any(s["symbol"] == "AAPL" for s in data["data"]["suggestions"])

# 2. 인기 티커 목록
@pytest.mark.asyncio
def test_popular_stocks():
    response = client.get("/api/stocks/popular")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert any(stock["symbol"] == "AAPL" for stock in data["data"])

# 3. 주식 상세 정보
@pytest.mark.asyncio
def test_get_stock_info():
    response = client.get("/api/stocks/AAPL/info")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert "currentPrice" in data["data"]

# 4. 주가 차트 데이터
@pytest.mark.asyncio
def test_get_stock_chart():
    response = client.get("/api/stocks/AAPL/chart", params={"period": "1mo", "interval": "1d"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "AAPL"
    assert "data" in data["data"]
    assert isinstance(data["data"]["data"], list)

# 5. 잘못된 심볼 예외
@pytest.mark.asyncio
def test_get_stock_info_invalid():
    response = client.get("/api/stocks/INVALID/info")
    assert response.status_code in (400, 422, 500)
    data = response.json()
    assert "detail" in data 

# 6. 재무정보 조회
@pytest.mark.asyncio
def test_get_financial_data():
    response = client.get("/api/stocks/AAPL/financial")
    assert response.status_code in (200, 404, 500)
    data = response.json()
    assert "success" in data
    assert "data" in data

# 7. 배당정보 조회
@pytest.mark.asyncio
def test_get_dividend_history():
    response = client.get("/api/stocks/AAPL/dividends?years=3")
    assert response.status_code in (200, 404, 500)
    data = response.json()
    assert "success" in data
    assert "data" in data

# 8. 종목 비교
@pytest.mark.asyncio
def test_compare_stocks():
    response = client.get("/api/stocks/compare?symbols=AAPL,MSFT")
    assert response.status_code in (200, 400, 404, 500)
    data = response.json()
    assert "success" in data
    assert "data" in data 