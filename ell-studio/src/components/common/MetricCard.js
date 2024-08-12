import React from 'react';
import MetricChart from '../MetricChart';

const MetricCard = ({ title, rawData, dataKey, color, yAxisLabel, aggregation }) => (
  <div className="bg-card rounded-md shadow-sm">
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