import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import HierarchicalTable from '../HierarchicalTable';
import React, { useMemo, useCallback, useEffect, useState } from 'react';
import { OldCard } from '../OldCard';
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

    // First pass: map all invocations
    invocations.forEach(invocation => {
      const mappedInvocation = mapInvocation(invocation);
      invocationsMap.set(invocation.id, mappedInvocation);
      
      if (!invocation.used_by_id) {
        rootInvocations.push(mappedInvocation);
      }
    });

    // Helper function to build clusters within a single level
    const buildLevelClusters = (levelInvocations) => {
      const visited = new Set();
      const levelClusters = new Map();
      let clusterId = 0;

      const buildCluster = (startId, clusterId) => {
        const stack = [startId];
        const clusterItems = [];
        
        while (stack.length > 0) {
          const currentId = stack.pop();
          if (visited.has(currentId)) continue;
          
          // Only visit nodes that are part of this level
          const currentItem = levelInvocations.find(inv => inv.id === currentId);
          if (!currentItem) continue;
          
          visited.add(currentId);
          currentItem.clusterId = clusterId;
          clusterItems.push(currentItem);

          // Find linked items within this level
          const linkedIds = [];
          if (currentItem.consumes) {
            currentItem.consumes.forEach(c => {
              if (c.id !== currentId && levelInvocations.some(inv => inv.id === c.id)) {
                linkedIds.push(c.id);
              }
            });
          }
          // Add items that consume currentItem (within this level)
          levelInvocations.forEach(inv => {
            if (inv.consumes && inv.consumes.some(c => c.id === currentId)) {
              if (inv.id !== currentId) linkedIds.push(inv.id);
            }
          });

          linkedIds.forEach(id => {
            if (!visited.has(id)) stack.push(id);
          });
        }
        return clusterItems;
      };

      // Build clusters for this level
      levelInvocations.forEach(inv => {
        if (!visited.has(inv.id)) {
          const clusterItems = buildCluster(inv.id, clusterId);
          const earliestDate = Math.min(...clusterItems.map(item => new Date(item.created_at).getTime()));
          clusterItems.forEach(item => {
            item.clusterDate = earliestDate;
          });
          levelClusters.set(clusterId, clusterItems);
          clusterId++;
        }
      });

      // Sort clusters and items within clusters
      const sortedClusters = Array.from(levelClusters.values())
        .sort((a, b) => b[0].clusterDate - a[0].clusterDate);
      
      sortedClusters.forEach(cluster => {
        cluster.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      });

      return sortedClusters.flat();
    };

    // Recursive function to process each level of the tree
    const processTreeLevel = (nodes) => {
      if (!nodes || nodes.length === 0) return [];

      // Sort current level nodes using clustering
      const sortedNodes = buildLevelClusters(nodes);

      // Process children recursively
      sortedNodes.forEach(node => {
        if (node.children && node.children.length > 0) {
          node.children = processTreeLevel(node.children);
        }
      });

      return sortedNodes;
    };

    // Second pass: build the tree structure
    invocations.forEach(invocation => {
      if (invocation.used_by_id) {
        const parent = invocationsMap.get(invocation.used_by_id);
        if (parent) {
          if (!parent.children) parent.children = [];
          parent.children.push(invocationsMap.get(invocation.id));
        } else {
          rootInvocations.push(invocationsMap.get(invocation.id));
        }
      }
    });

    // Process and sort each level of the tree
    return processTreeLevel(rootInvocations);
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
      if (e.key === 'Escape') {
        onSelectTrace(null);
        return;
      }

      if (currentlySelectedTrace) {
        const currentIndex = invocationTableData.findIndex(trace => trace.id === currentlySelectedTrace.id);
        if (e.key === 'ArrowUp' && currentIndex > 0) {
          e.preventDefault();
          onSelectTrace(invocationTableData[currentIndex - 1]);
        } else if (e.key === 'ArrowDown' && currentIndex < invocationTableData.length - 1) {
          e.preventDefault();
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
        <OldCard noMinW={true}>
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
        </OldCard>
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

  const initialSortConfig = null; // Sorting is handled during tree construction

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