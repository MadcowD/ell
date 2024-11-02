import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiTag, FiZap, FiHash, FiChevronRight, FiCode } from 'react-icons/fi';
import { getTimeAgo } from '../utils/lmpUtils';
import VersionBadge from './VersionBadge';
import { useInvocationsFromLMP } from '../hooks/useBackend';
import { LMPCardTitle } from './depgraph/LMPCardTitle';
import { format } from 'date-fns';
import SidePanel from './common/SidePanel';
import MetricChart from './oldgraph/OldMetricChart';
import { motion } from 'framer-motion';
import {Card} from './common/Card';

function LMPDetailsSidePanel({ lmp, uses, versionHistory }) {
  const { data: invocations } = useInvocationsFromLMP(lmp.name, lmp.lmp_id, 0, 100);

  const chartData = useMemo(() => {
    if (!invocations || invocations.length === 0) return [];
    return invocations
      .map(inv => ({
        date: new Date(inv.created_at),
        count: 1,
        latency: inv.latency_ms
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [invocations]);

  const totalInvocations = useMemo(() => invocations?.length || 0, [invocations]);
  const avgLatency = useMemo(() => {
    if (!invocations || invocations.length === 0) return 0;
    const sum = invocations.reduce((acc, inv) => acc + inv.latency_ms, 0);
    return sum / invocations.length;
  }, [invocations]);

  return (
    <SidePanel title="LMP Details">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-2 text-sm"
      >
        <div className="bg-card p-2 rounded">
          <div className="flex justify-between items-center mb-1">
            <h3 className="text-sm font-semibold text-card-foreground">Version Info</h3>
            <VersionBadge version={lmp.version_number + 1} hash={lmp.lmp_id} />
          </div>
          <div className="grid grid-cols-2 gap-y-0.5">
            <div className="flex items-center">
              <FiClock className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Created:</span>
            </div>
            <div className="text-right">{getTimeAgo(new Date(lmp.created_at))}</div>
            <div className="flex items-center">
              <FiTag className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Is LMP:</span>
            </div>
            <div className="text-right">{lmp.is_lm ? 'Yes' : 'No'}</div>
            <div className="flex items-center">
              <FiZap className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Invocations:</span>
            </div>
            <div className="text-right">{totalInvocations}</div>
            <div className="flex items-center">
              <FiHash className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Avg. Latency:</span>
            </div>
            <div className="text-right">{avgLatency.toFixed(2)}ms</div>
          </div>
        </div>

        {lmp.api_params && (
          <div className="bg-card p-2 rounded">
            <h3 className="text-sm font-semibold text-card-foreground mb-1 flex items-center">
              <FiCode className="mr-1" size={14} /> LM Keywords
            </h3>
            <pre className="overflow-x-auto text-xs text-muted-foreground bg-muted p-1 rounded">
              <code>{JSON.stringify(lmp.api_params, null, 2)}</code>
            </pre>
          </div>
        )}

        <div className="bg-card p-2 rounded">
          <h3 className="text-sm font-semibold text-card-foreground mb-1">Uses</h3>
          {uses && uses.length > 0 ? (
            <ul className="space-y-0.5">
              {uses.filter(use => !!use).map((use) => (
                <motion.li
                  key={use.lmp_id}
                  whileHover={{ scale: 1.01 }}
                  className=" p-0.5 rounded"
                >
                  <Link to={`/lmp/${use.name}/${use.lmp_id}`} className="text-primary hover:text-primary/80 transition-colors">
                    <Card>
                    <LMPCardTitle lmp={use} displayVersion scale={50}  />
                    </Card>
                  </Link>
                </motion.li>
              ))}
            </ul>
          ) : (
            <p className="text-muted-foreground">No dependencies</p>
          )}
        </div>

        <MetricChart
          title="Invocations"
          rawData={chartData}
          dataKey="count"
          color="#8884d8"
          yAxisLabel="Count"
        />

        <MetricChart
          title="Latency"
          rawData={chartData}
          dataKey="latency"
          color="#82ca9d"
          aggregation="avg"
          yAxisLabel="ms"
        />
{/* 
        <div className="bg-card p-2 rounded">
          <h3 className="text-sm font-semibold text-card-foreground mb-1">Version History</h3>
          <div className="space-y-0.5 max-h-40 overflow-y-auto pr-1">
            {versionHistory.map((version, index) => (
              <motion.div
                key={version.lmp_id}
                whileHover={{ scale: 1.01 }}
                className={`p-0.5 rounded ${
                  version.lmp_id === lmp.lmp_id
                    ? 'bg-primary/10 border-l-2 border-primary'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                <Link to={`/lmp/${version.name}/${version.lmp_id}`} className="block">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-1">
                      <span className="font-semibold">v{versionHistory.length - index}</span>
                      <span className="text-xs text-muted-foreground">
                        {format(new Date(version.created_at), 'MMM d, yyyy HH:mm')}
                      </span>
                    </div>
                    <FiChevronRight className="text-muted-foreground" size={12} />
                  </div>
                  {version.commit_message && (
                    <p className="text-xs text-muted-foreground truncate">
                      {version.commit_message}
                    </p>
                  )}
                </Link>
              </motion.div>
            ))}
          </div>
        </div> */}
      </motion.div>
    </SidePanel>
  );
}

export default LMPDetailsSidePanel;