import React from 'react';
import { ChartPeriod, ChartInterval, ChartType } from '../../types/stock';

interface ChartControlsProps {
  period: ChartPeriod;
  interval: ChartInterval;
  chartType: ChartType;
  onPeriodChange: (period: ChartPeriod) => void;
  onIntervalChange: (interval: ChartInterval) => void;
  onChartTypeChange: (type: ChartType) => void;
  className?: string;
}

const ChartControls: React.FC<ChartControlsProps> = ({
  period,
  interval,
  chartType,
  onPeriodChange,
  onIntervalChange,
  onChartTypeChange,
  className
}) => {
  const periods = [
    { value: '1d', label: '1일' },
    { value: '5d', label: '5일' },
    { value: '1mo', label: '1개월' },
    { value: '3mo', label: '3개월' },
    { value: '6mo', label: '6개월' },
    { value: '1y', label: '1년' },
    { value: '2y', label: '2년' },
    { value: '5y', label: '5년' },
    { value: '10y', label: '10년' },
    { value: 'ytd', label: '연초부터' },
    { value: 'max', label: '전체' }
  ];

  const intervals = [
    { value: '1m', label: '1분' },
    { value: '2m', label: '2분' },
    { value: '5m', label: '5분' },
    { value: '15m', label: '15분' },
    { value: '30m', label: '30분' },
    { value: '60m', label: '1시간' },
    { value: '90m', label: '1.5시간' },
    { value: '1h', label: '1시간' },
    { value: '1d', label: '1일' },
    { value: '5d', label: '5일' },
    { value: '1wk', label: '1주' },
    { value: '1mo', label: '1개월' },
    { value: '3mo', label: '3개월' }
  ];

  const chartTypes = [
    { value: 'line', label: '라인' },
    { value: 'candlestick', label: '캔들스틱' },
    { value: 'area', label: '영역' }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-4 ${className}`}>
      <div className="flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">기간</label>
          <select
            value={period}
            onChange={(e) => onPeriodChange(e.target.value as ChartPeriod)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {periods.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">간격</label>
          <select
            value={interval}
            onChange={(e) => onIntervalChange(e.target.value as ChartInterval)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {intervals.map((i) => (
              <option key={i.value} value={i.value}>
                {i.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">차트 타입</label>
          <select
            value={chartType}
            onChange={(e) => onChartTypeChange(e.target.value as ChartType)}
            className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {chartTypes.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
};

export default ChartControls; 