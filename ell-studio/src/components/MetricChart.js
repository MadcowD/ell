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
  Legend,
} from "recharts";
import {
  format,
  differenceInDays,
  differenceInHours,
  differenceInMinutes,
  startOfMinute,
  endOfMinute,
  eachMinuteOfInterval,
  eachHourOfInterval,
  eachDayOfInterval,
  startOfHour,
  endOfHour,
  startOfDay,
  endOfDay,
  addMinutes,
  getMinutes,
  subMonths,
  subDays,
  subHours,
} from "date-fns";

function MetricChart({ rawData, dataKey, color, title, yAxisLabel, aggregation="sum" }) {
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
     if(!rawData)
        return true;
    else {
        // if the range extends beyond the available data, don't show it
        const earliestDate = new Date(rawData[0]?.date);
        if(range.value === "all")
            return true;
        else {
            const start = range.value === "1m" ? subMonths(new Date(), 1) :
                          range.value === "7d" ? subDays(new Date(), 7) :
                          range.value === "24h" ? subHours(new Date(), 24) :
                          range.value === "12h" ? subHours(new Date(), 12) :
                          range.value === "1h" ? subHours(new Date(), 1) :
                          new Date(); // Default case, shouldn't occur
            return start >= earliestDate;
        }
    }
  }), [rawData]);

  useEffect(() => {
    const latestNow = new Date();
    if (rawData?.length > 0) {
      let start = rawData[0]?.date;
      
      switch (selectedTimeRange) {
        case "1m":
          start = subMonths(latestNow, 1);
          break;
        case "7d":
          start = subDays(latestNow, 7);
          break;
        case "24h":
          start = subHours(latestNow, 24);
          break;
        case "12h":
          start = subHours(latestNow, 12);
          break;
        case "1h":
          start = subHours(latestNow, 1);
          break;
        default:
          // "all" - use the earliest date in rawData
          break;
      }

      setDateRange({
        start: new Date(Math.max(new Date(start), new Date(rawData[0]?.date))),
        end: latestNow,
      });
    }
  }, [rawData, selectedTimeRange]);

  // Determine aggregation based on zoom
  const aggregatedData = useMemo(() => {
    if (!rawData?.length || !dateRange) return [];

    const zoomStart =  dateRange.start;
    const zoomEnd = dateRange.end;

    const daysDiff = differenceInDays(zoomEnd, zoomStart);
    const hoursDiff = differenceInHours(zoomEnd, zoomStart);
    const minutesDiff = differenceInMinutes(zoomEnd, zoomStart);

    let aggregationInterval;
    let aggregationFunction;

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

  // Memoize formatting functions
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
    (value, name, props) => {
      return [`${value} ${yAxisLabel || title.toLowerCase()}`, title];
    },
    [yAxisLabel, title]
  );

  const handleZoom = (domain) => {
  };

  return (
    <div className="bg-[#161b22] p-4 rounded-lg shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-md font-semibold text-white">{title}</h3>
        <select
          className="bg-[#0d1117] text-white text-sm border border-gray-700 rounded px-2 py-1"
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
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={aggregatedData}
            margin={{ top: 5, right: 20, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id={`color${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.8} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="date"
              stroke="#4a5568"
              tick={{ fill: "#4a5568", fontSize: 10 }}
              tickFormatter={formatXAxis}
            />
            <YAxis
              stroke="#4a5568"
              tick={{ fill: "#4a5568", fontSize: 10 }}
              label={{
                value: yAxisLabel,
                angle: -90,
                position: "insideLeft",
                fill: "#4a5568",
                fontSize: 12,
              }}
            />
            <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1f2937",
                border: "none",
                color: "#fff",
                fontSize: 12,
              }}
              labelFormatter={(label) => format(new Date(label), "PPpp")}
              formatter={formatTooltip}
            />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              fillOpacity={1}
              fill={`url(#color${title})`}
              name={title}
            />
            <Brush
              dataKey="date"
              height={20}
              stroke={color}
              fill="#161b22"
              onChange={handleZoom}
              startIndex={0}
              endIndex={aggregatedData.length - 1}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default React.memo(MetricChart);