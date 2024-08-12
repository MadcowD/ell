import React from 'react';
import { FiZap, FiClock, FiHash, FiUsers, FiPercent, FiBox } from 'react-icons/fi';
import SidePanel from '../common/SidePanel';
import StatItem from '../common/StatItem';
import MetricCard from '../common/MetricCard';

const InvocationsAnalyticsSidePanel = ({ aggregateData, sidebarMetrics }) => {
  if (!aggregateData || !sidebarMetrics) return null;

  return (
    <SidePanel title="Invocations Analytics">
      <div className="bg-card p-3 rounded-md shadow-sm mb-4">
        <StatItem icon={FiZap} label="Total Invocations" value={sidebarMetrics.totalInvocations} />
        <StatItem icon={FiClock} label="Avg. Latency" value={`${sidebarMetrics.avgLatency.toFixed(2)}ms`} />
        <StatItem icon={FiHash} label="Total Tokens" value={sidebarMetrics.totalTokens} />
        <StatItem icon={FiUsers} label="Unique LMPs" value={sidebarMetrics.uniqueLMPs} />
        <StatItem icon={FiPercent} label="Success Rate" value={`${sidebarMetrics.successRate.toFixed(2)}%`} />
        <StatItem icon={FiBox} label="Avg Tokens per Invocation" value={(sidebarMetrics.totalTokens / sidebarMetrics.totalInvocations).toFixed(2)} />
      </div>

      <MetricCard
        title="Invocations Over Time"
        rawData={aggregateData.graph_data}
        dataKey="count"
        aggregation="sum"
        color="#8884d8"
        yAxisLabel="Count"
      />

      <MetricCard
        title="Latency Over Time"
        rawData={aggregateData.graph_data}
        dataKey="avg_latency"
        aggregation="avg"
        color="#82ca9d"
        yAxisLabel="ms"
      />

      <MetricCard
        title="Tokens Over Time"
        rawData={aggregateData.graph_data}
        dataKey="tokens"
        color="#ffc658"
        yAxisLabel="Tokens"
      />

      <div className="bg-card p-3 rounded-md shadow-sm mt-4">
        <h3 className="text-sm font-medium text-card-foreground mb-2">Top 5 LMPs</h3>
        <ul className="space-y-1">
          {sidebarMetrics.topLMPs.map(([lmp, count], index) => (
            <li key={lmp} className="flex justify-between items-center text-xs">
              <span className="text-muted-foreground">
                <span className="text-primary mr-1">{index + 1}.</span>
                {lmp}
              </span>
              <span className="text-muted-foreground">{count} invocations</span>
            </li>
          ))}
        </ul>
      </div>
    </SidePanel>
  );
};

export default InvocationsAnalyticsSidePanel;