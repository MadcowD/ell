import React from 'react';
import SidePanel from '../common/SidePanel';
import StatItem from '../common/StatItem';
import MetricCard from '../common/MetricCard';
import { FiZap, FiClock, FiHash, FiUsers, FiPercent, FiBox } from 'react-icons/fi';

const InvocationsAnalyticsSidePanel = ({ aggregateData, sidebarMetrics }) => {
  if (!aggregateData) return null;

  const statsData = [
    { icon: FiZap, label: "Total Invocations", value: aggregateData.total_invocations },
    { icon: FiClock, label: "Avg Latency", value: `${aggregateData.avg_latency.toFixed(2)}ms` },
    { icon: FiHash, label: "Total Tokens", value: aggregateData.total_tokens },
    { icon: FiUsers, label: "Unique LMPs", value: aggregateData.unique_lmps },
  ];

  return (
    <SidePanel title="Invocations Analytics">
      <div className="bg-[#21242c] p-3 rounded-md shadow-sm mb-4">
        {statsData.map((stat, index) => (
          <StatItem key={index} icon={stat.icon} label={stat.label} value={stat.value} />
        ))}
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

      <div className="bg-[#21242c] p-3 rounded-md shadow-sm mt-4">
        <h3 className="text-sm font-medium text-gray-300 mb-2">Top 5 LMPs</h3>
        <ul className="space-y-1">
          {sidebarMetrics.topLMPs.map(([lmp, count], index) => (
            <li key={lmp} className="flex justify-between items-center text-xs">
              <span className="text-gray-400">
                <span className="text-blue-400 mr-1">{index + 1}.</span>
                {lmp}
              </span>
              <span className="text-gray-500">{count} invocations</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-[#21242c] p-3 rounded-md shadow-sm mt-4">
        <h3 className="text-sm font-medium text-gray-300 mb-2">Additional Metrics</h3>
        <StatItem icon={FiPercent} label="Success Rate" value={`${aggregateData.success_rate?.toFixed(2)}%`} />
        <StatItem icon={FiBox} label="Avg Tokens per Invocation" value={(aggregateData.total_tokens / aggregateData.total_invocations).toFixed(2)} />
      </div>
    </SidePanel>
  );
};

export default InvocationsAnalyticsSidePanel;