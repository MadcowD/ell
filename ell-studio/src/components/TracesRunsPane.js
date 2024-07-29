import { LMPCardTitle } from './depgraph/LMPCardTitle';
import HierarchicalTable from './HierarchicalTable';
import React, { useMemo, useCallback  } from 'react';
import { Card } from './Card';
import { getTimeAgo } from '../utils/lmpUtils';
import VersionBadge from './VersionBadge';
import { useNavigate } from 'react-router-dom';
import { lstrCleanStringify } from './lstrCleanStringify';
const TracesRunsPane = ({ invocations, onSelectTrace }) => {

  const navigate = useNavigate();

  const onClickLMP = useCallback((lmp) => {
    navigate(`/lmp/${lmp.name}/${lmp.lmp_id}`);
  }, [navigate]);
  const traces = useMemo(() => {
    return invocations.map(inv => ({
      name: inv.lmp?.name || 'Unknown',
      input: lstrCleanStringify(inv.args.length === 1 ? inv.args[0] : inv.args),
      output: lstrCleanStringify(inv.results.length === 1 ? inv.results[0] : inv.results),
      version: inv.lmp.version_number + 1,
      created_at: new Date(inv.created_at),
      latency: inv.latency_ms / 1000,
      total_tokens: (inv.prompt_tokens || 0) + (inv.completion_tokens || 0),
      ...inv
    }));
  }, [invocations]);


  const schema = {
    columns: [
      { 
        header: 'LMP', 
        key: 'name', 
        render: (item) => <Card noMinW={true}><LMPCardTitle lmp={item.lmp} fontSize="sm" onClick={(e) => {
          e.stopPropagation();
          onClickLMP(item.lmp);
        }} /></Card>, 
        // maxWidth: 200,
        sortable: true
      },
      { 
        header: 'Version', 
        key: 'version', 
        render: (item) => <VersionBadge version={item.version} lmpId={item.lmp.id} className='text-xs scale-85 inline-block' />, 
        maxWidth: 150,
        sortable: true
      },
      { header: 'Input', key: 'input', maxWidth: 300 },
      { header: 'Output', key: 'output', render: (item) => `${item.output}...`, maxWidth: 600 },
      { 
        header: 'Start Time', 
        key: 'created_at', 
        render: (item) => <span className="text-gray-400">{getTimeAgo(new Date(item.created_at))}</span>, 
        maxWidth: 150,
        sortable: true
      },
      { 
        header: 'Latency', 
        key: 'latency', 
        render: (item) => <span className="text-red-400">{item.latency.toFixed(2)}s</span>, 
        maxWidth: 100,
        sortable: true
      },
      { 
        header: 'Total Tokens', 
        key: 'total_tokens', 
        render: (item) => <span>{item.total_tokens}</span>, 
        maxWidth: 120,
        sortable: true
      },
    ]
  };

  const initialSortConfig = { key: 'created_at', direction: 'desc' };

  return (
    <HierarchicalTable
      schema={schema}
      data={traces}
      onRowClick={onSelectTrace}
      initialSortConfig={initialSortConfig}
    />
  );
};

export default TracesRunsPane;