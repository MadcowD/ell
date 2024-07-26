import { LMPCardTitle } from './depgraph/LMPCardTitle';
import HierarchicalTable from './HierarchicalTable';
import React, { useMemo } from 'react';
import { Card } from './Card';
import { getTimeAgo } from '../utils/lmpUtils';


const lstrCleanStringify = (obj_containing_lstrs) => {
  return JSON.stringify(obj_containing_lstrs, (key, value) => {
    if (value && value.__lstr === true) {
      return value.content;
    }
    return value;
  }, 2);
};



const TracesRunsPane = ({ invocations, onSelectTrace }) => {
  const traces = useMemo(() => {
    return invocations.map(inv => ({
      name:  inv.lmp?.name || 'Unknown',
      input: lstrCleanStringify(inv.args.length === 1 ? inv.args[0] : inv.args),
      output: lstrCleanStringify(inv.results),
      ...inv
    }));
  }, [invocations]);

  const schema = {
    columns: [
      { header: 'Name', key: 'name', render: (item) => <Card noMinW={true}><LMPCardTitle lmp={{name: item.name}} /></Card>, maxWidth: 200 },
      { header: 'Input', key: 'input', maxWidth: 300 },
      { header: 'Output', key: 'output', render: (item) => `${item.output}...`, maxWidth: 600 },
      { header: 'Start Time', key: 'created_at', render: (item) => <span className="text-gray-400">{getTimeAgo(new Date(item.created_at + "Z"))}</span>, maxWidth: 150 },
      { header: 'Latency', key: 'latency', render: (item) => <span className="text-red-400">{(item.latency_ms / 1000).toFixed(2)}s</span>, maxWidth: 100 },
      { header: 'Total Tokens', key: 'total_tokens', render: (item) => <span>{(item.prompt_tokens || 0) + (item.completion_tokens || 0)}</span>, maxWidth: 120 },
    ]
  };

  return (
    <HierarchicalTable
      schema={schema}
      data={traces}
      onRowClick={onSelectTrace}
    />
  );
};

export default TracesRunsPane;