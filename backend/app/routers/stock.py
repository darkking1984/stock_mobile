from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ..services.stock_service import StockService
from ..models.stock import (
    StockInfo,
    ChartData,
    SearchResponse,
    StockSuggestion,
    ApiResponse,
    StockInfoResponse,
    ChartDataResponse,
    SearchResponseWrapper,
    StockListResponse,
    ChartPeriod,
    ChartInterval,
    ChartType
)

router = APIRouter(prefix="/stocks", tags=["stocks"])
stock_service = StockService()

logger = logging.getLogger(__name__)

@router.get("/search", response_model=SearchResponseWrapper)
async def search_stocks(
    query: str = Query(..., min_length=1, max_length=50, description="Search query for stock ticker or company name")
):
    """
    Search for stocks by ticker symbol or company name
    """
    try:
        suggestions = await stock_service.search_stocks(query)
        return ApiResponse(
            success=True,
            data=SearchResponse(suggestions=suggestions),
            message="Stock search completed successfully"
        )
    except Exception as e:
        logger.error(f"Error searching stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search stocks")

@router.get("/popular", response_model=StockListResponse)
async def get_popular_stocks():
    """
    Get list of popular stocks
    """
    try:
        stocks = await stock_service.get_popular_stocks()
        return ApiResponse(
            success=True,
            data=stocks,
            message="Popular stocks retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting popular stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get popular stocks")

@router.get("/{symbol}/info", response_model=StockInfoResponse)
async def get_stock_info(
    symbol: str = Path(..., pattern="^[A-Z]{1,5}(-[A-Z])?$", description="Stock ticker symbol")
):
    """
    Get detailed information for a specific stock
    """
    try:
        stock_info = await stock_service.get_stock_info(symbol.upper())
        if not stock_info:
            raise HTTPException(status_code=404, detail="Stock not found")
        
        return ApiResponse(
            success=True,
            data=stock_info,
            message="Stock information retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting stock info for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get stock information")

@router.get("/{symbol}/chart", response_model=ChartDataResponse)
async def get_stock_chart(
    symbol: str = Path(..., pattern="^[A-Z]{1,5}(-[A-Z])?$", description="Stock ticker symbol"),
    period: ChartPeriod = Query(ChartPeriod.ONE_MONTH, description="Chart period"),
    interval: ChartInterval = Query(ChartInterval.ONE_DAY, description="Chart interval"),
    chart_type: ChartType = Query(ChartType.LINE, description="Chart type")
):
    """
    Get chart data for a specific stock
    """
    try:
        chart_data = await stock_service.get_stock_chart(
            symbol.upper(),
            period=period,
            interval=interval
        )
        if not chart_data:
            raise HTTPException(status_code=404, detail="Chart data not found")
        return ApiResponse(
            success=True,
            data=chart_data,
            message="Chart data retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chart data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get chart data")

@router.get("/{symbol}/financial", response_model=ApiResponse)
async def get_financial_data(
    symbol: str = Path(..., pattern="^[A-Z]{1,5}(-[A-Z])?$", description="Stock ticker symbol")
):
    """
    Get financial data for a specific stock
    """
    try:
        financial_data = await stock_service.get_financial_data(symbol.upper())
        if not financial_data:
            raise HTTPException(status_code=404, detail="Financial data not found")
        
        return ApiResponse(
            success=True,
            data=financial_data,
            message="Financial data retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting financial data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get financial data")

@router.get("/{symbol}/dividends", response_model=ApiResponse)
async def get_dividend_history(
    symbol: str = Path(..., pattern="^[A-Z]{1,5}(-[A-Z])?$", description="Stock ticker symbol"),
    years: int = Query(5, ge=1, le=10, description="Number of years to retrieve")
):
    """
    Get dividend history for a specific stock
    """
    try:
        dividends = await stock_service.get_dividend_history(symbol.upper(), years)
        return ApiResponse(
            success=True,
            data=dividends,
            message="Dividend history retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting dividend history for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get dividend history")

@router.get("/compare", response_model=StockListResponse)
async def compare_stocks(
    symbols: str = Query(..., description="Comma-separated list of stock symbols (max 5)")
):
    """
    Compare multiple stocks
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        if len(symbol_list) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 stocks can be compared")
        
        if len(symbol_list) < 2:
            raise HTTPException(status_code=400, detail="At least 2 stocks required for comparison")
        
        comparison_data = await stock_service.compare_stocks(symbol_list)
        return ApiResponse(
            success=True,
            data=comparison_data,
            message="Stock comparison completed successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to compare stocks") 

@router.get("/{symbol}/description", response_model=ApiResponse)
async def get_company_description(
    symbol: str = Path(..., pattern="^[A-Z]{1,5}(-[A-Z])?$", description="Stock ticker symbol")
):
    """
    Get detailed company description and information
    """
    try:
        company_info = await stock_service.get_company_description(symbol.upper())
        if not company_info:
            raise HTTPException(status_code=404, detail="Company information not found")
        
        return ApiResponse(
            success=True,
            data=company_info,
            message="Company description retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company description for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get company description") 

@router.get("/top-market-cap", response_model=ApiResponse)
async def get_top_market_cap_stocks():
    """
    Get top 10 stocks by market capitalization
    """
    try:
        top_stocks = await stock_service.get_top_market_cap_stocks()
        return ApiResponse(
            success=True,
            data=top_stocks,
            message="Top market cap stocks retrieved successfully"
        )
    except Exception as e:
        logger.error(f"Error getting top market cap stocks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get top market cap stocks")

@router.get("/index/{index_name}/stocks", response_model=ApiResponse)
async def get_index_stocks(
    index_name: str = Path(..., description="Index name (dow, nasdaq, sp500, russell2000)")
):
    """
    Get top stocks by market capitalization for specific index
    """
    try:
        # 지수명을 소문자로 변환
        index_name = index_name.lower()
        
        # 유효한 지수명인지 확인
        valid_indices = ['dow', 'nasdaq', 'sp500', 'russell2000']
        if index_name not in valid_indices:
            raise HTTPException(status_code=400, detail="Invalid index name. Must be one of: dow, nasdaq, sp500, russell2000")
        
        index_stocks = await stock_service.get_index_stocks(index_name)
        return ApiResponse(
            success=True,
            data=index_stocks,
            message=f"Top stocks for {index_name.upper()} retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting index stocks for {index_name}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get index stocks") 