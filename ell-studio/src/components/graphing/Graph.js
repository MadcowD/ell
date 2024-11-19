import React from 'react';
import { GraphRenderer, MetricAdder, useGraph } from './GraphSystem';

const Graph = ({ graphId, metrics, type = 'line' }) => {
  useGraph(graphId);

  return (
    <>
      {metrics.map((metric, index) => (
        <MetricAdder
          key={index}
          graphId={graphId}
          {...metric}
          type={type}
        />
      ))}
      <GraphRenderer graphId={graphId} />
    </>
  );
};

export default Graph;
