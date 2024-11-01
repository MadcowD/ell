import React from 'react';
import { Card } from '../common/Card';

function EvaluationRunMetrics({ run }) {
  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Metrics</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {run?.labeler_summaries?.map((summary, index) => (
          <Card key={index} className="p-4">
            <h4 className="text-sm font-medium mb-2">{summary.name}</h4>
            <div className="h-32 bg-accent/10 rounded flex items-center justify-center">
              <span className="text-muted-foreground">Histogram placeholder</span>
            </div>
            <div className="mt-2 text-sm">
              <div>Mean: {summary.data.mean.toFixed(2)}</div>
              <div>Std: {summary.data.std.toFixed(2)}</div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export default EvaluationRunMetrics; 