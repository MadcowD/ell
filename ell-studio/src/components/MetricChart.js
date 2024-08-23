import React, { useMemo, useCallback, useState, useEffect } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Brush,
} from "recharts";
import {
  format,
  differenceInDays,
  differenceInHours,
  startOfMinute,
  eachMinuteOfInterval,
  eachHourOfInterval,
  eachDayOfInterval,
  startOfHour,
  startOfDay,
  addMinutes,
  getMinutes,
  subMonths,
  subDays,
  subHours,
} from "date-fns";

function MetricChart({ rawData, dataKey, color, yAxisLabel, aggregation="sum", title }) {
  const [dateRange, setDateRange] = useState(null);
  const [selectedTimeRange, setSelectedTimeRange] = useState("all");

  const timeRangeOptions = useMemo(() => [
    { value: "all", label: "All Time" },
    { value: "1m", label: "Last Month" },
    { value: "7d", label: "Last 7 Days" },
    { value: "24h", label: "Last 24 Hours" },
    { value: "12h", label: "Last 12 Hours" },
    { value: "1h", label: "Last Hour" },
  ].filter((range) => {
    if(!rawData) return true;
    const earliestDate = new Date(rawData[0]?.date);
    if(range.value === "all") return true;
    const start = range.value === "1m" ? subMonths(new Date(), 1) :
                  range.value === "7d" ? subDays(new Date(), 7) :
                  range.value === "24h" ? subHours(new Date(), 24) :
                  range.value === "12h" ? subHours(new Date(), 12) :
                  range.value === "1h" ? subHours(new Date(), 1) :
                  new Date();
    return start >= earliestDate;
  }), [rawData]);

  useEffect(() => {
    const latestNow = new Date();
    if (rawData?.length > 0) {
      let start = rawData[0]?.date;
      
      switch (selectedTimeRange) {
        case "1m": start = subMonths(latestNow, 1); break;
        case "7d": start = subDays(latestNow, 7); break;
        case "24h": start = subHours(latestNow, 24); break;
        case "12h": start = subHours(latestNow, 12); break;
        case "1h": start = subHours(latestNow, 1); break;
        default: break;
      }

      setDateRange({
        start: new Date(Math.max(new Date(start), new Date(rawData[0]?.date))),
        end: latestNow,
      });
    }
  }, [rawData, selectedTimeRange]);

  const aggregatedData = useMemo(() => {
    if (!rawData?.length || !dateRange) return [];

    const zoomStart = dateRange.start;
    const zoomEnd = dateRange.end;

    const daysDiff = differenceInDays(zoomEnd, zoomStart);
    const hoursDiff = differenceInHours(zoomEnd, zoomStart);

    let aggregationInterval, aggregationFunction;

    if (daysDiff > 30) {
      aggregationInterval = eachDayOfInterval;
      aggregationFunction = startOfDay;
    } else if (hoursDiff > 24) {
      aggregationInterval = eachHourOfInterval;
      aggregationFunction = startOfHour;
    } else if (hoursDiff > 1) {
      aggregationInterval = (interval) => {
        const start = startOfHour(interval.start);
        const end = interval.end;
        const result = [];
        for (let current = start; current <= end; current = addMinutes(current, 15)) {
          result.push(current);
        }
        return result;
      };
      aggregationFunction = (date) => {
        const minutes = getMinutes(date);
        const roundedMinutes = Math.floor(minutes / 15) * 15;
        return startOfMinute(addMinutes(startOfHour(date), roundedMinutes));
      };
    } else {
      aggregationInterval = eachMinuteOfInterval;
      aggregationFunction = startOfMinute;
    }

    const aggregatedMap = new Map();
    rawData.forEach((item) => {
      const date = new Date(item.date);
      if (date >= zoomStart && date <= zoomEnd) {
        const key = format(aggregationFunction(date), "yyyy-MM-dd'T'HH:mm");
        const existing = aggregatedMap.get(key) || { sum: 0, count: 0 };
        aggregatedMap.set(key, { sum: existing.sum + item[dataKey], count: existing.count + 1 });
      }
    });

    return aggregationInterval({ start: zoomStart, end: zoomEnd }).map(
      (date) => {
        const key = format(date, "yyyy-MM-dd'T'HH:mm");
        const { sum, count } = aggregatedMap.get(key) || { sum: 0, count: 0 };
        return {
          date: key,
          [dataKey]: aggregation === "avg" ? (count > 0 ? sum / count : 0) : sum,
        };
      }
    );
  }, [rawData, dateRange, dataKey, aggregation]);

  const formatXAxis = useCallback(
    (tickItem) => {
      const date = new Date(tickItem);
      const daysDiff = differenceInDays(dateRange.end, dateRange.start);
      if (daysDiff > 30) return format(date, "MMM d");
      if (daysDiff > 1) return format(date, "MMM d HH:mm");
      return format(date, "HH:mm");
    },
    [dateRange]
  );

  const formatTooltip = useCallback(
    (value) => {
      return [`${value} ${yAxisLabel || ''}`, ''];
    },
    [yAxisLabel]
  );

  return (
    <div className="bg-card p-2 rounded">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-semibold text-card-foreground">{title}</h3>
        <select
          className="bg-muted text-muted-foreground text-xs border border-input rounded px-1 py-0.5"
          value={selectedTimeRange}
          onChange={(e) => setSelectedTimeRange(e.target.value)}
        >
          {timeRangeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={aggregatedData}
            margin={{ top: 5, right: 5, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id={`color${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.8} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              stroke="#718096"
              tick={{ fill: "#718096", fontSize: 9 }}
              tickFormatter={formatXAxis}
            />
            <YAxis
              stroke="#718096"
              tick={{ fill: "#718096", fontSize: 9 }}
              label={{
                value: yAxisLabel,
                angle: -90,
                position: "insideLeft",
                fill: "#718096",
                fontSize: 10,
              }}
            />
            <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#2D3748",
                border: "1px solid #4A5568",
                color: "#E2E8F0",
                fontSize: 10,
              }}
              labelFormatter={(label) => format(new Date(label), "PPpp")}
              formatter={formatTooltip}
            />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              fillOpacity={1}
              fill={`url(#color${dataKey})`}
            />
            <Brush
              dataKey="date"
              height={15}
              stroke={color}
              fill="#2D3748"
              tickFormatter={formatXAxis}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default React.memo(MetricChart);