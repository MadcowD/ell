import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import HierarchicalTable from '../HierarchicalTable';
import React, { useMemo, useCallback, useEffect, useState } from 'react';
import { Card } from '../Card';
import { getTimeAgo } from '../../utils/lmpUtils';
import VersionBadge from '../VersionBadge';
import { useNavigate } from 'react-router-dom';

import { ContentsRenderer } from './ContentsRenderer';




const mapInvocation = (invocation) => ({
  name: invocation.lmp?.name || 'Unknown',
  id: invocation.id,
  version: invocation.lmp.version_number + 1,
  created_at: new Date(invocation.created_at),
  children: [],
  latency: invocation.latency_ms / 1000,
  total_tokens: (invocation.prompt_tokens || 0) + (invocation.completion_tokens || 0),
  ...invocation
});

const InvocationsTable = ({ invocations, currentPage, setCurrentPage, pageSize, onSelectTrace, currentlySelectedTrace, omitColumns = [], expandAll = false }) => {
  const navigate = useNavigate();

  const onClickLMP = useCallback(({lmp, id : invocationId}) => {
    navigate(`/lmp/${lmp.name}/${lmp.lmp_id}?i=${invocationId}`);
  }, [navigate]);
 

  const isLoading = !invocations;

  const invocationTableData = useMemo(() => {
    if (!invocations) return [];

    const invocationsMap = new Map();
    const rootInvocations = [];

    // First pass: map all invocations and identify roots
    invocations.forEach(invocation => {
      const mappedInvocation = mapInvocation(invocation);
      invocationsMap.set(invocation.id, mappedInvocation);
      
      if (!invocation.used_by_id) {
        rootInvocations.push(mappedInvocation);
      }
    });

    // Second pass: build the tree structure
    invocations.forEach(invocation => {
      if (invocation.used_by_id) {
        const parent = invocationsMap.get(invocation.used_by_id);
        if (parent) {
          if (!parent.children) parent.children = [];
          parent.children.push(invocationsMap.get(invocation.id));
        } else {
          // If parent is not found, treat as a root
          rootInvocations.push(invocationsMap.get(invocation.id));
        }
      }
    });
    return rootInvocations;
  }, [invocations]);

  const links = useMemo(() => {
    const generateLinks = (invocation) => {
      let links = [];
      
      // Add links for current invocation
      if (invocation.consumes) {
        links.push(...invocation.consumes.map(c => ({
          to: invocation.id,
          from: c.id
        })).filter(link => link.from !== invocation.id));
      }
      
      
      return links;
    };

    return invocations ? invocations.flatMap(generateLinks) : [];
  }, [invocations]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (currentlySelectedTrace) {
        const currentIndex = invocationTableData.findIndex(trace => trace.id === currentlySelectedTrace.id);
        if (e.key === 'ArrowUp' && currentIndex > 0) {
          onSelectTrace(invocationTableData[currentIndex - 1]);
        } else if (e.key === 'ArrowDown' && currentIndex < invocationTableData.length - 1) {
          onSelectTrace(invocationTableData[currentIndex + 1]);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [invocationTableData, currentlySelectedTrace, onSelectTrace]);

  useEffect(() => {
    console.log(`Displaying page ${currentPage + 1}, with ${invocations?.length} invocations`);
  }, [currentPage, invocations]);

  const defaultColumns = [
    { 
      header: 'LMP', 
      key: 'name', 
      render: (item) => (
        <Card noMinW={true}>
          <LMPCardTitle 
            lmp={item.lmp} 
            paddingClassOverride='pl-2'
            fontSize="xs" 
            onClick={(e) => {
              e.stopPropagation();
              onClickLMP(item);
            }} 
            showInvocationCount={false}
          />
        </Card>
      ), 
      sortable: true,
      
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
    { header: 'Input', key: 'input', maxWidth: 400, render: (item) => <ContentsRenderer typeMatchLevel={1} item={item} field={"params"} />},
    { header: 'Output', key: 'output', render: (item) => <ContentsRenderer item={item} field={"results"} />, maxWidth: 600 },
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
      render: (item) => <span className="text-red-400">{item.latency?.toFixed(2)}s</span>, 
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

  const initialSortConfig = { key: 'created_at', direction: 'desc' };

  const hasNextPage = invocationTableData.length === pageSize;

  if (isLoading) return <div>Loading...</div>;

  return (
    <HierarchicalTable
      schema={{
        columns: defaultColumns
      }}
      links={links}
      expandedLinkColumn={'name'}
      collapsedLinkColumn={'version'}
      expandAll={expandAll}
      omitColumns={omitColumns}
      data={invocationTableData}
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