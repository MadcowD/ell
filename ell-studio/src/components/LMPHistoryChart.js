import React, { useMemo, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Brush, Legend } from 'recharts';
import { format, differenceInDays, differenceInHours, startOfDay, startOfHour, startOfMinute, eachDayOfInterval, eachHourOfInterval, eachMinuteOfInterval, addMinutes, getMinutes } from 'date-fns';

const LMPHistoryChart = ({ data, title }) => {
  const [dateRange, setDateRange] = useState(null);

  const aggregatedData = useMemo(() => {
    if (!data?.length) return [];

    const sortedData = [...data].sort((a, b) => new Date(a.date) - new Date(b.date));
    const zoomStart = dateRange?.start || new Date(sortedData[0].date);
    const zoomEnd = dateRange?.end || new Date(sortedData[sortedData.length - 1].date);

    const daysDiff = differenceInDays(zoomEnd, zoomStart);
    const hoursDiff = differenceInHours(zoomEnd, zoomStart);

    let aggregationInterval;
    let aggregationFunction;

    if (daysDiff > 30) {
      aggregationInterval = eachDayOfInterval;
      aggregationFunction = startOfDay;
    } else if (hoursDiff > 24) {
      aggregationInterval = eachHourOfInterval;
      aggregationFunction = startOfHour;
    } else {
      aggregationInterval = eachMinuteOfInterval;
      aggregationFunction = startOfMinute;
    }

    const aggregatedMap = new Map();
    sortedData.forEach((item) => {
      const date = new Date(item.date);
      if (date >= zoomStart && date <= zoomEnd) {
        const key = format(aggregationFunction(date), "yyyy-MM-dd'T'HH:mm");
        const existing = aggregatedMap.get(key) || 0;
        aggregatedMap.set(key, existing + item.count);
      }
    });

    return aggregationInterval({ start: zoomStart, end: zoomEnd }).map((date) => {
      const key = format(date, "yyyy-MM-dd'T'HH:mm");
      return {
        date: key,
        versions: aggregatedMap.get(key) || 0,
      };
    });
  }, [data, dateRange]);

  const formatXAxis = (tickItem) => {
    const date = new Date(tickItem);
    const daysDiff = differenceInDays(dateRange?.end || new Date(), dateRange?.start || new Date(data[0].date));
    if (daysDiff > 30) return format(date, "MMM d");
    if (daysDiff > 1) return format(date, "MMM d HH:mm");
    return format(date, "HH:mm");
  };

  const formatTooltip = (value, name, props) => {
    return [`${value} versions`, "LMPs Created"];
  };

  const handleZoom = (domain) => {
    setDateRange({
      start: new Date(domain.startDate),
      end: new Date(domain.endDate),
    });
  };

  return (
    <div className="bg-[#161b22] p-4 rounded-lg shadow-lg w-full h-full">
      <h3 className="text-lg font-semibold mb-2 text-white">{title}</h3>
      <ResponsiveContainer width="100%" height="90%">
        <AreaChart data={aggregatedData} margin={{ top: 5, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorVersions" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="date" stroke="#4a5568" tick={{ fill: "#4a5568", fontSize: 10 }} tickFormatter={formatXAxis} />
          <YAxis stroke="#4a5568" tick={{ fill: "#4a5568", fontSize: 10 }} />
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
          <Area type="monotone" dataKey="versions" stroke="#8884d8" fillOpacity={1} fill="url(#colorVersions)" name="LMPs Created" />
          <Brush dataKey="date" height={20} stroke="#8884d8" fill="#161b22" onChange={handleZoom} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LMPHistoryChart;