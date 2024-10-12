import React from 'react';
import { GraphRenderer, MetricAdder, useGraph } from './GraphSystem';

const Graph = ({ graphId, metrics }) => {
  useGraph(graphId);

  return (
    <>
      {metrics.map((metric, index) => (
        <MetricAdder
          key={index}
          graphId={graphId}
          {...metric}
        />
      ))}
      <GraphRenderer graphId={graphId} />
    </>
  );
};

export default Graph;
