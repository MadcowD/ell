import React, { useState } from 'react';
import { FiBarChart2 } from 'react-icons/fi';
import TrendLine from '../graphing/TrendLine';
import MetricDisplay from './MetricDisplay';

const MetricTable = ({ summaries, historicalData, isVertical }) => {
  const [hoverIndex, setHoverIndex] = useState(null);

  return (
    <div className={`pt-0 p-2 grid grid-cols-1 ${isVertical ? '' : 'md:grid-cols-2'} gap-x-4 gap-y-2`}>
      {summaries.map((summary, index) => {
        const currentValue = hoverIndex !== null ? historicalData[summary.evaluation_labeler_id][hoverIndex].mean : summary.data.mean;
        const previousValue = historicalData[summary.evaluation_labeler_id][historicalData[summary.evaluation_labeler_id].length - 2]?.mean;

        return (
          <React.Fragment key={summary.evaluation_labeler_id}>
            <div className={`flex flex-col space-y-1 text-xs py-1 hover:bg-accent/50 transition-colors duration-100 pr-1`}>
              <div className={`w-full font-medium truncate flex items-center`} title={summary.evaluation_labeler.name}>
                <FiBarChart2 className="mr-1 h-3 w-3 text-muted-foreground flex-shrink-0" />
                <code className="metric-label text-xs font-medium truncate max-w-[calc(100%-1.5rem)]">
                  {summary.evaluation_labeler.name}
                </code>
              </div>
              <div className={`w-full flex items-center justify-between space-x-2`}>
                <div className="w-full min-w-[100px] max-w-[200px]">
                  <TrendLine 
                    data={historicalData[summary.evaluation_labeler_id].map(d => d.mean)} 
                    hoverIndex={hoverIndex}
                    onHover={setHoverIndex}
                  />
                </div>
                <div className="flex-shrink-0"></div>
                <MetricDisplay
                  currentValue={currentValue}
                  previousValue={previousValue}
                  label={summary.evaluation_labeler.name}
                  showTooltip={false}
                />
              </div>
            </div>
            {index < summaries.length - 1 && (
              <div className="border-b border-gray-900 my-0 md:hidden" />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default MetricTable;
