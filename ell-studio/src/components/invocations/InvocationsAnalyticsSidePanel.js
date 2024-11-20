import React from 'react';
import { FiZap, FiClock, FiHash, FiUsers, FiPercent, FiBox } from 'react-icons/fi';
import { Link } from 'react-router-dom';
import SidePanel from '../common/SidePanel';
import MetricChart from '../oldgraph/OldMetricChart';
import { motion } from 'framer-motion';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { Card } from '../common/Card';

const InvocationsAnalyticsSidePanel = ({ aggregateData, sidebarMetrics }) => {
  if (!aggregateData || !sidebarMetrics) return null;

  return (
    <SidePanel title="Invocations Analytics">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-2 text-sm"
      >
        <div className="bg-card p-2 rounded">
          <h3 className="text-sm font-semibold text-card-foreground mb-1">Overview</h3>
          <div className="grid grid-cols-2 gap-y-0.5">
            <div className="flex items-center">
              <FiZap className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Total Invocations:</span>
            </div>
            <div className="text-right">{sidebarMetrics.totalInvocations}</div>
            <div className="flex items-center">
              <FiClock className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Avg. Latency:</span>
            </div>
            <div className="text-right">{sidebarMetrics.avgLatency?.toFixed(2)}ms</div>
            <div className="flex items-center">
              <FiHash className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Total Tokens:</span>
            </div>
            <div className="text-right">{sidebarMetrics.totalTokens}</div>
            <div className="flex items-center">
              <FiUsers className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Unique LMPs:</span>
            </div>
            <div className="text-right">{sidebarMetrics.uniqueLMPs}</div>
            <div className="flex items-center">
              <FiPercent className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Success Rate:</span>
            </div>
            <div className="text-right">{sidebarMetrics.successRate.toFixed(2)}%</div>
            <div className="flex items-center">
              <FiBox className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Avg Tokens/Invocation:</span>
            </div>
            <div className="text-right">{(sidebarMetrics.totalTokens / sidebarMetrics.totalInvocations)?.toFixed(2)}</div>
          </div>
        </div>

        <MetricChart
          title="Invocations Over Time"
          rawData={aggregateData.graph_data}
          dataKey="count"
          aggregation="sum"
          color="#8884d8"
          yAxisLabel="Count"
        />

        <MetricChart
          title="Latency Over Time"
          rawData={aggregateData.graph_data}
          dataKey="avg_latency"
          aggregation="avg"
          color="#82ca9d"
          yAxisLabel="ms"
        />

        <MetricChart
          title="Tokens Over Time"
          rawData={aggregateData.graph_data}
          dataKey="tokens"
          color="#ffc658"
          yAxisLabel="Tokens"
        />

        {/* <div className="bg-card p-2 rounded">
          <h3 className="text-sm font-semibold text-card-foreground mb-1">Top 5 LMPs</h3>
          <ul className="space-y-0.5">
            {sidebarMetrics.topLMPs.map(([lmpName, count], index) => (
              <motion.li
                key={lmpName}
                whileHover={{ scale: 1.01 }}
                className="p-0.5 rounded"
              >
                <Link to={`/lmp/${lmpName}`} className="text-primary hover:text-primary/80 transition-colors">
                  <Card className="relative">
                    <LMPCardTitle 
                      lmp={{ name: lmpName, is_lm: false }} // Assuming we don't have full LMP data here
                      displayVersion={false}
                      scale={50}
                    />
                    <div className="absolute top-0 right-0 bg-muted text-muted-foreground text-xs px-1 rounded-bl">
                      {count} invocations
                    </div>
                    <div className="mt-1 bg-primary/5 h-1 rounded-full overflow-hidden">
                      <div 
                        className="bg-primary h-full" 
                        style={{ width: `${(count / sidebarMetrics.totalInvocations) * 100}%` }}
                      ></div>
                    </div>
                  </Card>
                </Link>
              </motion.li>
            ))}
          </ul>
        </div> */}
      </motion.div>
    </SidePanel>
  );
};

export default InvocationsAnalyticsSidePanel;