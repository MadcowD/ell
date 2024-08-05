import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import HierarchicalTable from '../HierarchicalTable';
import React, { useMemo, useCallback, useEffect, useState } from 'react';
import { Card } from '../Card';
import { getTimeAgo } from '../../utils/lmpUtils';
import VersionBadge from '../VersionBadge';
import { useNavigate } from 'react-router-dom';
import { lstrCleanStringify } from '../../utils/lstrCleanStringify';
import { useInvocations } from '../../hooks/useBackend';

const InvocationsTable = ({ invocations, currentPage, setCurrentPage, pageSize, onSelectTrace, currentlySelectedTrace, omitColumns = [] }) => {
  const navigate = useNavigate();



  const onClickLMP = useCallback(({lmp, id : invocationId}) => {
    navigate(`/lmp/${lmp.name}/${lmp.lmp_id}?i=${invocationId}`);
  }, [navigate]);

  const isLoading = !invocations;


  const traces = useMemo(() => {
    if (!invocations) return [];
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

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (currentlySelectedTrace) {
        const currentIndex = traces.findIndex(trace => trace.id === currentlySelectedTrace.id);
        if (e.key === 'ArrowUp' && currentIndex > 0) {
          onSelectTrace(traces[currentIndex - 1]);
        } else if (e.key === 'ArrowDown' && currentIndex < traces.length - 1) {
          onSelectTrace(traces[currentIndex + 1]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [traces, currentlySelectedTrace, onSelectTrace]);

  const defaultColumns = [
    { 
      header: 'LMP', 
      key: 'name', 
      render: (item) => (
        <Card noMinW={true}>
          <LMPCardTitle 
            lmp={item.lmp} 
            fontSize="sm" 
            onClick={(e) => {
              e.stopPropagation();
              onClickLMP(item);
            }} 
          />
        </Card>
      ), 
      sortable: true
    },
    { 
      header: 'Version', 
      key: 'version', 
      render: (item) => (
        <VersionBadge 
          version={item.version} 
          lmpId={item.lmp.id} 
          className='text-xs scale-85 inline-block' 
        />
      ), 
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
  ];

  const schema = {
    columns: defaultColumns.filter(column => !omitColumns.includes(column.key))
  };

  const initialSortConfig = { key: 'created_at', direction: 'desc' };

  const hasNextPage = traces.length === pageSize;

  if (isLoading) return <div>Loading...</div>;

  return (
    <HierarchicalTable
      schema={schema}
      data={traces}
      onRowClick={onSelectTrace}
      initialSortConfig={initialSortConfig}
      rowClassName={(item) => 
        item.id === currentlySelectedTrace?.id ? 'bg-blue-600 bg-opacity-30' : ''
      }
      currentPage={currentPage}
      onPageChange={setCurrentPage}
      pageSize={pageSize}
      hasNextPage={hasNextPage}
    />
  );
};

export default InvocationsTable;