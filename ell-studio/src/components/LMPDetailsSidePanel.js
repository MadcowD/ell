import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiTag, FiGitCommit, FiZap, FiHash, FiCalendar, FiChevronRight } from 'react-icons/fi';
import { getTimeAgo } from '../utils/lmpUtils';
import VersionBadge from './VersionBadge';
import { useInvocationsFromLMP } from '../hooks/useBackend';
import { LMPCardTitle } from './depgraph/LMPCardTitle';
import { format } from 'date-fns';
import SidePanel from './common/SidePanel';
import StatItem from './common/StatItem';
import MetricCard from './common/MetricCard';
import { motion } from 'framer-motion';

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
        className="space-y-6"
      >
        <div className="bg-card p-4 rounded-lg shadow-md">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-card-foreground">Version Info</h3>
            <VersionBadge version={lmp.version_number + 1} hash={lmp.lmp_id} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <StatItem icon={FiClock} label="Created" value={getTimeAgo(new Date(lmp.created_at))} />
            <StatItem icon={FiTag} label="Is LMP" value={lmp.is_lm ? 'Yes' : 'No'} />
            <StatItem icon={FiZap} label="Total Invocations" value={totalInvocations} />
            <StatItem icon={FiHash} label="Avg. Latency" value={`${avgLatency.toFixed(2)}ms`} />
          </div>
        </div>

        {lmp.lm_kwargs && (
          <div className="bg-card p-4 rounded-lg shadow-md">
            <h3 className="text-lg font-semibold text-card-foreground mb-3">LM Keywords</h3>
            <pre className="overflow-x-auto text-sm text-muted-foreground bg-muted p-3 rounded-md">
              <code>{JSON.stringify(lmp.lm_kwargs, null, 2)}</code>
            </pre>
          </div>
        )}

        <div className="bg-card p-4 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-card-foreground mb-3">Uses</h3>
          {uses && uses.length > 0 ? (
            <ul className="space-y-2">
              {uses.filter(use => !!use).map((use) => (
                <motion.li
                  key={use.lmp_id}
                  whileHover={{ scale: 1.02 }}
                  className="text-sm bg-muted p-2 rounded-md"
                >
                  <Link to={`/lmp/${use.name}/${use.lmp_id}`} className="text-primary hover:text-primary/80 transition-colors">
                    <LMPCardTitle lmp={use} displayVersion scale={50} shortVersion={true} />
                  </Link>
                </motion.li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">No dependencies</p>
          )}
        </div>

        <MetricCard
          title="Invocations"
          rawData={chartData}
          dataKey="count"
          color="#8884d8"
          yAxisLabel="Count"
        />

        <MetricCard
          title="Latency"
          rawData={chartData}
          dataKey="latency"
          color="#82ca9d"
          aggregation="avg"
          yAxisLabel="ms"
        />

        <div className="bg-card p-4 rounded-lg shadow-md">
          <h3 className="text-lg font-semibold text-card-foreground mb-3">Version History</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
            {versionHistory.map((version, index) => (
              <motion.div
                key={version.lmp_id}
                whileHover={{ scale: 1.02 }}
                className={`p-3 rounded-md text-sm ${
                  version.lmp_id === lmp.lmp_id
                    ? 'bg-primary/10'
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                <Link to={`/lmp/${version.name}/${version.lmp_id}`} className="block">
                  <div className="flex justify-between items-center">
                    <span className={`font-medium ${
                      version.lmp_id === lmp.lmp_id ? 'text-primary' : 'text-card-foreground'
                    }`}>
                      v{versionHistory.length - index}
                    </span>
                    <span className="text-muted-foreground">
                      <FiCalendar className="inline mr-1" size={12} />
                      {format(new Date(version.created_at), 'MMM d, yyyy')}
                    </span>
                  </div>
                  {version.commit_message && (
                    <p className="text-muted-foreground mt-1 truncate">
                      <FiGitCommit className="inline mr-1" size={12} />
                      {version.commit_message}
                    </p>
                  )}
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>
    </SidePanel>
  );
}

export default LMPDetailsSidePanel;