export interface StockInfo {
  symbol: string;
  name: string;
  currentPrice: number;
  previousClose: number;
  change: number;
  changePercent: number;
  high?: number;
  low?: number;
  volume?: number;
  marketCap?: number;
  peRatio?: number;
  dividendYield?: number;
  beta?: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
  avgVolume?: number;
  currency: string;
  exchange?: string;
  sector?: string;
  industry?: string;
}

export interface ChartData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartResponse {
  symbol: string;
  period: string;
  interval: string;
  data: ChartData[];
}

export interface StockSuggestion {
  symbol: string;
  name: string;
  exchange: string;
  type: string;
  country: string;
}

export interface SearchResponse {
  success: boolean;
  data: StockSuggestion[];
  total: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
  };
  timestamp: string;
}

export type ChartPeriod = '1d' | '5d' | '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y' | '10y' | 'ytd' | 'max';
export type ChartInterval = '1m' | '2m' | '5m' | '15m' | '30m' | '60m' | '90m' | '1h' | '1d' | '5d' | '1wk' | '1mo' | '3mo';
export type ChartType = 'line' | 'candlestick' | 'area'; 