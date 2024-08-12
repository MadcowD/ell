import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiTag, FiGitCommit, FiZap, FiHash, FiCalendar } from 'react-icons/fi';
import { getTimeAgo } from '../utils/lmpUtils';
import VersionBadge from './VersionBadge';
import { useInvocationsFromLMP } from '../hooks/useBackend';
import { LMPCardTitle } from './depgraph/LMPCardTitle';
import { format } from 'date-fns';
import SidePanel from './common/SidePanel';
import StatItem from './common/StatItem';
import MetricCard from './common/MetricCard';

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
      <div className="bg-card p-3 rounded-md shadow-sm mb-4">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-sm font-medium text-card-foreground">Version</h3>
          <VersionBadge version={lmp.version_number + 1} hash={lmp.lmp_id} />
        </div>
        <StatItem icon={FiClock} label="Created" value={getTimeAgo(new Date(lmp.created_at))} />
        <StatItem icon={FiTag} label="Is LMP" value={lmp.is_lm ? 'Yes' : 'No'} />
        <StatItem icon={FiZap} label="Total Invocations" value={totalInvocations} />
        <StatItem icon={FiHash} label="Avg. Latency" value={`${avgLatency.toFixed(2)}ms`} />
      </div>

      {lmp.lm_kwargs && (
        <div className="bg-card p-3 rounded-md shadow-sm mb-4">
          <h3 className="text-sm font-medium text-card-foreground mb-2">LM Keywords</h3>
          <pre className="overflow-x-auto text-xs text-muted-foreground bg-muted p-2 rounded">
            <code>{JSON.stringify(lmp.lm_kwargs, null, 2)}</code>
          </pre>
        </div>
      )}

      <div className="bg-card p-3 rounded-md shadow-sm mb-4">
        <h3 className="text-sm font-medium text-card-foreground mb-2">Uses</h3>
        {uses && uses.length > 0 ? (
          <ul className="space-y-1">
            {uses.filter(use => !!use).map((use) => (
              <li key={use.lmp_id} className="text-xs">
                <Link to={`/lmp/${use.name}/${use.lmp_id}`} className="text-primary hover:text-primary/80 transition-colors">
                  <LMPCardTitle lmp={use} displayVersion scale={50} shortVersion={true} />
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-muted-foreground">No dependencies</p>
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

      <div className="bg-card p-3 rounded-md shadow-sm mt-4">
        <h3 className="text-sm font-medium text-card-foreground mb-2">Version History</h3>
        <div className="space-y-2 max-h-48 overflow-y-auto pr-2">
          {versionHistory.map((version, index) => (
            <Link
              key={version.lmp_id}
              to={`/lmp/${version.name}/${version.lmp_id}`}
              className={`block p-2 rounded text-xs ${
                version.lmp_id === lmp.lmp_id
                  ? 'bg-primary/10'
                  : 'hover:bg-muted'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className={`font-medium ${
                  version.lmp_id === lmp.lmp_id ? 'text-primary' : 'text-muted-foreground'
                }`}>
                  v{versionHistory.length - index}
                </span>
                <span className="text-muted-foreground">
                  <FiCalendar className="inline mr-1" size={10} />
                  {format(new Date(version.created_at), 'MMM d, yyyy')}
                </span>
              </div>
              {version.commit_message && (
                <p className="text-muted-foreground mt-1 truncate">
                  <FiGitCommit className="inline mr-1" size={10} />
                  {version.commit_message}
                </p>
              )}
            </Link>
          ))}
        </div>
      </div>
    </SidePanel>
  );
}

export default LMPDetailsSidePanel;