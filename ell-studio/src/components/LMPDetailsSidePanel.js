import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiTag, FiGitCommit, FiZap, FiHash, FiCalendar } from 'react-icons/fi';
import { getTimeAgo } from '../utils/lmpUtils';
import VersionBadge from './VersionBadge';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { format } from 'date-fns';
import { useInvocationsFromLMP } from '../hooks/useBackend';
import { LMPCardTitle } from './depgraph/LMPCardTitle';

function StatItem({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span className="flex items-center text-gray-400"><Icon className="mr-2" size={14} />{label}</span>
      <span className="font-medium text-white">{value}</span>
    </div>
  );
}

function LMPDetailsSidePanel({ lmp, uses, versionHistory }) {
  const [timeScale, setTimeScale] = useState('1h');
  const [movingAverage, setMovingAverage] = useState(1);
  const { data: invocations } = useInvocationsFromLMP(lmp.name, lmp.lmp_id);

  const chartData = useMemo(() => {
    if (!invocations) return [];

    const now = new Date();
    const timeScaleDays = {
      '15m': 15 / (24 * 60), '1h': 1 / 24, '6h': 6 / 24, '1d': 1, '1w': 7, '1m': 30, '3m': 90, '1y': 365
    }[timeScale];
    const startDate = new Date(now.getTime() - timeScaleDays * 24 * 60 * 60 * 1000);

    const filteredInvocations = invocations.filter(inv => new Date(inv.created_at) >= startDate);

    // Group invocations by time intervals
    const intervalMs = timeScaleDays * 24 * 60 * 60 * 1000 / 20; // Divide the time range into 20 intervals
    const groupedData = filteredInvocations.reduce((acc, inv) => {
      const date = new Date(inv.created_at);
      const intervalIndex = Math.floor((date - startDate) / intervalMs);
      const intervalDate = new Date(startDate.getTime() + intervalIndex * intervalMs);
      const key = intervalDate.toISOString();
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    const sortedData = Object.entries(groupedData)
      .map(([date, count]) => ({ date, count }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));

    // Calculate moving average
    return sortedData.map((item, index, array) => {
      const start = Math.max(0, index - movingAverage + 1);
      const windowSlice = array.slice(start, index + 1);
      const avg = windowSlice.reduce((sum, i) => sum + i.count, 0) / windowSlice.length;
      return { ...item, movingAvg: avg };
    });
  }, [invocations, timeScale, movingAverage]);

  const formatXAxis = (tickItem) => {
    const date = new Date(tickItem);
    switch(timeScale) {
      case '15m':
      case '1h':
      case '6h':
        return format(date, 'HH:mm');
      case '1d':
        return format(date, 'HH:mm');
      case '1w':
        return format(date, 'EEE');
      case '1m':
      case '3m':
        return format(date, 'MMM d');
      case '1y':
        return format(date, 'MMM');
      default:
        return format(date, 'MMM d');
    }
  };

  const totalInvocations = invocations?.length || 0;
  const avgLatency = invocations?.reduce((sum, inv) => sum + inv.latency_ms, 0) / totalInvocations || 0;

  return (
    <aside className="w-[500px] bg-[#0d1117] p-4 overflow-y-auto">
      <h2 className="text-lg font-semibold mb-3 text-white">Details</h2>
      <div className="space-y-4">
        <div className="bg-[#161b22] p-3 rounded">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-semibold text-white">Version</h3>
            <VersionBadge version={lmp.version_number + 1} hash={lmp.lmp_id} />
          </div>
          <StatItem icon={FiClock} label="Created" value={getTimeAgo(new Date(lmp.created_at))} />
          <StatItem icon={FiTag} label="Is LMP" value={lmp.is_lm ? 'Yes' : 'No'} />
          <StatItem icon={FiZap} label="Total Invocations" value={totalInvocations} />
          <StatItem icon={FiHash} label="Avg. Latency" value={`${avgLatency.toFixed(2)}ms`} />
        </div>

        {lmp.lm_kwargs && (
          <div className="bg-[#161b22] p-3 rounded">
            <h3 className="text-sm font-semibold mb-2 text-white">LM Keywords</h3>
            <pre className="overflow-x-auto text-xs text-gray-300">
              <code>{JSON.stringify(lmp.lm_kwargs, null, 2)}</code>
            </pre>
          </div>
        )}

        <div className="bg-[#161b22] p-3 rounded">
          <h3 className="text-sm font-semibold mb-2 text-white">Uses</h3>
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

        <div className="bg-[#161b22] p-3 rounded">
          <h3 className="text-sm font-semibold mb-2 text-white">Invocations Over Time</h3>
          <div className="flex space-x-2 mb-2">
            <select
              className="bg-[#0d1117] text-white text-xs p-1 rounded"
              value={timeScale}
              onChange={(e) => setTimeScale(e.target.value)}
            >
              <option value="15m">15 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="6h">6 Hours</option>
              <option value="1d">1 Day</option>
              <option value="1w">1 Week</option>
              <option value="1m">1 Month</option>
              <option value="3m">3 Months</option>
              <option value="1y">1 Year</option>
            </select>
            <select
              className="bg-[#0d1117] text-white text-xs p-1 rounded"
              value={movingAverage}
              onChange={(e) => setMovingAverage(Number(e.target.value))}
            >
              <option value="1">No Average</option>
              <option value="3">3-Day Avg</option>
              <option value="7">7-Day Avg</option>
              <option value="30">30-Day Avg</option>
            </select>
          </div>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorAvg" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#82ca9d" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#82ca9d" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis 
                  dataKey="date" 
                  stroke="#4a5568" 
                  tick={{ fill: '#4a5568' }} 
                  tickFormatter={formatXAxis}
                />
                <YAxis stroke="#4a5568" tick={{ fill: '#4a5568' }} />
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: 'none', color: '#fff' }}
                  labelFormatter={(label) => format(new Date(label), 'PPpp')}
                />
                <Area type="monotone" dataKey="count" stroke="#8884d8" fillOpacity={1} fill="url(#colorCount)" name="Count" />
                <Area type="monotone" dataKey="movingAvg" stroke="#82ca9d" fillOpacity={1} fill="url(#colorAvg)" name="Moving Avg" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-[#161b22] p-3 rounded">
          <h3 className="text-sm font-semibold mb-2 text-white">Version History</h3>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {versionHistory.map((version, index) => (
              <Link
                key={version.lmp_id}
                to={`/lmp/${version.name}/${version.lmp_id}`}
                className={`block text-xs ${version.lmp_id === lmp.lmp_id ? 'text-blue-400 font-semibold' : 'text-gray-400'} hover:text-white`}
              >
                <div className="flex justify-between items-center">
                  <span>v{versionHistory.length - index}</span>
                  <span>{getTimeAgo(new Date(version.created_at))}</span>
                </div>
                {version.commit_message && (
                  <p className="text-gray-500 truncate">{version.commit_message}</p>
                )}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}

export default LMPDetailsSidePanel;