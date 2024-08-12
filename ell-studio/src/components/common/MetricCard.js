import React from 'react';
import MetricChart from '../MetricChart';

const MetricCard = ({ title, rawData, dataKey, color, yAxisLabel, aggregation }) => (
  <div className="bg-[#21242c] p-3 rounded-md shadow-sm">
    <h3 className="text-sm font-medium text-gray-300 mb-2">{title}</h3>
    <MetricChart 
      rawData={rawData}
      dataKey={dataKey}
      color={color}
      yAxisLabel={yAxisLabel}
      aggregation={aggregation}
      title={title}
    />
  </div>
);

export default MetricCard;