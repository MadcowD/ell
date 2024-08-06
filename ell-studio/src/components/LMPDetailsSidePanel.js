import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiTag, FiGitCommit, FiZap, FiHash, FiCalendar } from 'react-icons/fi';
import { getTimeAgo } from '../utils/lmpUtils';
import VersionBadge from './VersionBadge';
import MetricChart from './MetricChart';
import { useInvocationsFromLMP } from '../hooks/useBackend';
import { LMPCardTitle } from './depgraph/LMPCardTitle';
import { subDays, format, addDays, endOfMonth } from 'date-fns';
import { ScrollArea } from './common/ScrollArea';

function StatItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center text-gray-400"><Icon className="mr-2" size={14} />{label}</span>
      <span className="font-medium text-white">{value}</span>
    </div>
  );
}

function LMPDetailsSidePanel({ lmp, uses, versionHistory }) {
  // TODO: update this for all versions aswell..
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
    // <ScrollArea className="h-full">
      <div className="p-4">
        <h2 className="text-lg font-semibold mb-3 text-white">Details</h2>
        <div className="space-y-4">
          <div className="bg-[#161b22] p-3 rounded">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-md font-semibold text-white">Version</h3>
              <VersionBadge version={lmp.version_number + 1} hash={lmp.lmp_id} />
            </div>
            <StatItem icon={FiClock} label="Created" value={getTimeAgo(new Date(lmp.created_at))} />
            <StatItem icon={FiTag} label="Is LMP" value={lmp.is_lm ? 'Yes' : 'No'} />
            <StatItem icon={FiZap} label="Total Invocations" value={totalInvocations} />
            <StatItem icon={FiHash} label="Avg. Latency" value={`${avgLatency.toFixed(2)}ms`} />
          </div>

          {lmp.lm_kwargs && (
            <div className="bg-[#161b22] p-3 rounded">
              <h3 className="text-md font-semibold mb-2 text-white">LM Keywords</h3>
              <pre className="overflow-x-auto text-xs text-gray-300">
                <code>{JSON.stringify(lmp.lm_kwargs, null, 2)}</code>
              </pre>
            </div>
          )}

          <div className="bg-[#161b22] p-3 rounded">
            <h3 className="text-md font-semibold mb-2 text-white">Uses</h3>
            {uses && uses.length > 0 ? (
              <ul className="space-y-1">
                {uses.filter(use => !!use).map((use) => (
                  <li key={use.lmp_id} className="text-sm">
                    <Link to={`/lmp/${use.name}/${use.lmp_id}`} className="text-blue-400 hover:text-blue-300">
                      <LMPCardTitle lmp={use} displayVersion scale={50} shortVersion={true} />
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-400">No dependencies</p>
            )}
          </div>

          <MetricChart 
            rawData={chartData}
            dataKey="count"
            color="#8884d8"
            title="Invocations"
            yAxisLabel="Count"
          />

          <MetricChart 
            rawData={chartData}
            dataKey="latency"
            color="#82ca9d"
            title="Latency"
            aggregation="avg"
            yAxisLabel="ms"
          />

          <div className="bg-[#161b22] p-3 rounded">
            <h3 className="text-sm font-semibold mb-2 text-white">Version History</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {versionHistory.map((version, index) => (
                <Link
                  key={version.lmp_id}
                  to={`/lmp/${version.name}/${version.lmp_id}`}
                  className={`block p-2 rounded ${
                    version.lmp_id === lmp.lmp_id
                      ? 'bg-blue-900 bg-opacity-30'
                      : 'hover:bg-gray-800'
                  }`}
                >
                  <div className="flex justify-between items-center text-sm">
                    <span className={`font-semibold ${
                      version.lmp_id === lmp.lmp_id ? 'text-blue-400' : 'text-white'
                    }`}>
                      v{versionHistory.length - index}
                    </span>
                    <span className="text-gray-400 text-xs">
                      <FiCalendar className="inline mr-1" size={12} />
                      {format(new Date(version.created_at), 'MMM d, yyyy')}
                    </span>
                  </div>
                  {version.commit_message && (
                    <p className="text-gray-400 text-xs mt-1 truncate">
                      <FiGitCommit className="inline mr-1" size={12} />
                      {version.commit_message}
                    </p>
                  )}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    // </ScrollArea>
  );
}

export default LMPDetailsSidePanel;