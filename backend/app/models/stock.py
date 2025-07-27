from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime

# 차트 기간 열거형
class ChartPeriod(str, Enum):
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"
    SIX_MONTHS = "6mo"
    ONE_YEAR = "1y"
    TWO_YEARS = "2y"
    FIVE_YEARS = "5y"
    TEN_YEARS = "10y"
    YEAR_TO_DATE = "ytd"
    MAX = "max"

# 차트 간격 열거형
class ChartInterval(str, Enum):
    ONE_MINUTE = "1m"
    TWO_MINUTES = "2m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    SIXTY_MINUTES = "60m"
    NINETY_MINUTES = "90m"
    ONE_HOUR = "1h"
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"

# 차트 타입 열거형
class ChartType(str, Enum):
    LINE = "line"
    CANDLESTICK = "candlestick"
    AREA = "area"

# 주식 기본 정보 모델
class StockInfo(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    name: str = Field(..., description="회사명")
    currentPrice: float = Field(..., description="현재가")
    previousClose: float = Field(..., description="전일 종가")
    change: float = Field(..., description="변동폭")
    changePercent: float = Field(..., description="변동률 (%)")
    high: Optional[float] = Field(None, description="고가")
    low: Optional[float] = Field(None, description="저가")
    volume: Optional[int] = Field(None, description="거래량")
    marketCap: Optional[float] = Field(None, description="시가총액")
    peRatio: Optional[float] = Field(None, description="PER")
    dividendYield: Optional[float] = Field(None, description="배당수익률")
    beta: Optional[float] = Field(None, description="베타")
    fiftyTwoWeekHigh: Optional[float] = Field(None, description="52주 고가")
    fiftyTwoWeekLow: Optional[float] = Field(None, description="52주 저가")
    avgVolume: Optional[int] = Field(None, description="평균 거래량")
    currency: str = Field("USD", description="통화")
    exchange: Optional[str] = Field(None, description="거래소")
    sector: Optional[str] = Field(None, description="섹터")
    industry: Optional[str] = Field(None, description="산업")

# 차트 데이터 모델
class ChartDataPoint(BaseModel):
    timestamp: str = Field(..., description="타임스탬프")
    open: float = Field(..., description="시가")
    high: float = Field(..., description="고가")
    low: float = Field(..., description="저가")
    close: float = Field(..., description="종가")
    volume: int = Field(..., description="거래량")

# 차트 응답 모델
class ChartData(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    period: str = Field(..., description="차트 기간")
    interval: str = Field(..., description="차트 간격")
    data: List[ChartDataPoint] = Field(..., description="차트 데이터")

# 주식 검색 제안 모델
class StockSuggestion(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    name: str = Field(..., description="회사명")
    exchange: str = Field(..., description="거래소")
    type: str = Field(..., description="주식 타입")
    country: str = Field(..., description="국가")

# 검색 응답 모델
class SearchResponse(BaseModel):
    suggestions: List[StockSuggestion] = Field(..., description="검색 제안 목록")

# API 응답 래퍼 모델
class ApiResponse(BaseModel):
    success: bool = Field(..., description="성공 여부")
    data: Any = Field(..., description="응답 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="응답 시간")

# 제네릭 API 응답 모델들
class StockInfoResponse(BaseModel):
    success: bool = Field(..., description="성공 여부")
    data: StockInfo = Field(..., description="주식 정보")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="응답 시간")

class ChartDataResponse(BaseModel):
    success: bool = Field(..., description="성공 여부")
    data: ChartData = Field(..., description="차트 데이터")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="응답 시간")

class SearchResponseWrapper(BaseModel):
    success: bool = Field(..., description="성공 여부")
    data: SearchResponse = Field(..., description="검색 결과")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="응답 시간")

class StockListResponse(BaseModel):
    success: bool = Field(..., description="성공 여부")
    data: List[StockInfo] = Field(..., description="주식 목록")
    message: Optional[str] = Field(None, description="응답 메시지")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="응답 시간")

# 재무 데이터 모델
class FinancialData(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    period: str = Field(..., description="기간")
    revenue: Optional[float] = Field(None, description="매출")
    netIncome: Optional[float] = Field(None, description="순이익")
    operatingIncome: Optional[float] = Field(None, description="영업이익")
    totalAssets: Optional[float] = Field(None, description="총자산")
    totalLiabilities: Optional[float] = Field(None, description="총부채")
    cashFlow: Optional[float] = Field(None, description="현금흐름")

# 배당 데이터 모델
class DividendData(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    date: str = Field(..., description="배당일")
    amount: float = Field(..., description="배당금")
    type: str = Field(..., description="배당 타입")

# 기술적 지표 모델
class TechnicalIndicator(BaseModel):
    symbol: str = Field(..., description="주식 심볼")
    indicator: str = Field(..., description="지표명")
    value: float = Field(..., description="지표값")
    signal: str = Field(..., description="신호 (buy/sell/hold)")
    timestamp: str = Field(..., description="계산 시간")

# 에러 응답 모델
class ApiError(BaseModel):
    success: bool = Field(False, description="성공 여부")
    error: Dict[str, Any] = Field(..., description="에러 정보")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="에러 발생 시간") 