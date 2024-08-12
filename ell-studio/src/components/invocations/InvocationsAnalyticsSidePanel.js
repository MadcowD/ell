import React from 'react';
import { FiZap, FiClock, FiHash, FiUsers, FiPercent, FiBox } from 'react-icons/fi';
import SidePanel from '../common/SidePanel';
import StatItem from '../common/StatItem';
import MetricCard from '../common/MetricCard';
import { motion } from 'framer-motion';

const InvocationsAnalyticsSidePanel = ({ aggregateData, sidebarMetrics }) => {
  if (!aggregateData || !sidebarMetrics) return null;

  return (
    <SidePanel title="Invocations Analytics">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-6"
      >
        <div className="bg-card p-4 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-card-foreground mb-4">Overview</h3>
          <div className="grid grid-cols-2 gap-4">
            <StatItem icon={FiZap} label="Total Invocations" value={sidebarMetrics.totalInvocations} />
            <StatItem icon={FiClock} label="Avg. Latency" value={`${sidebarMetrics.avgLatency.toFixed(2)}ms`} />
            <StatItem icon={FiHash} label="Total Tokens" value={sidebarMetrics.totalTokens} />
            <StatItem icon={FiUsers} label="Unique LMPs" value={sidebarMetrics.uniqueLMPs} />
            <StatItem icon={FiPercent} label="Success Rate" value={`${sidebarMetrics.successRate.toFixed(2)}%`} />
            <StatItem icon={FiBox} label="Avg Tokens/Invocation" value={(sidebarMetrics.totalTokens / sidebarMetrics.totalInvocations).toFixed(2)} />
          </div>
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

        <div className="bg-card p-4 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-card-foreground mb-3">Top 5 LMPs</h3>
          <ul className="space-y-2">
            {sidebarMetrics.topLMPs.map(([lmp, count], index) => (
              <motion.li
                key={lmp}
                whileHover={{ scale: 1.02 }}
                className="flex justify-between items-center text-sm bg-muted p-2 rounded-md"
              >
                <span className="text-card-foreground">
                  <span className="text-primary mr-2">{index + 1}.</span>
                  {lmp}
                </span>
                <span className="text-muted-foreground">{count} invocations</span>
              </motion.li>
            ))}
          </ul>
        </div>
      </motion.div>
    </SidePanel>
  );
};

export default InvocationsAnalyticsSidePanel;