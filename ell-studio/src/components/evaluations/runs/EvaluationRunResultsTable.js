import React, { useMemo, useEffect } from 'react';
import HierarchicalTable from '../../HierarchicalTable';
import { Card } from '../../common/Card';
import { ContentsRenderer } from '../../invocations/ContentsRenderer';
import LabelDisplay from '../LabelDisplay';
import InvocationDetailsPopover from '../../invocations/details/InvocationDetailsPopover';

const MAX_PREVIEW_ITEMS = 3;

const OutputPreview = ({ outputs, invocation, isExpanded }) => {
  const totalOutputs = outputs.length;
  
  if (isExpanded) {
    return (
      <div className="text-xs text-muted-foreground">
        {totalOutputs} outputs
      </div>
    );
  }
  
  const previewOutputs = outputs.slice(0, MAX_PREVIEW_ITEMS);
  
  return (
    <div className="space-y-0.5">
      {previewOutputs.map((output, idx) => (
        <div key={idx} className="text-sm border-l-2 border-muted pl-2">
          <ContentsRenderer 
            item={{
              contents: {
                results: output
              }
            }}
            field="results"
          />
        </div>
      ))}
      {totalOutputs > MAX_PREVIEW_ITEMS && (
        <div className="text-xs text-muted-foreground pl-2 mt-1">
          & {totalOutputs - MAX_PREVIEW_ITEMS} more...
        </div>
      )}
    </div>
  );
};

const EvaluationRunResultsTable = ({ 
  results, 
  currentPage, 
  setCurrentPage, 
  pageSize,
  selectedTrace,
  setSelectedTrace,
  searchQuery,
  onFilteredResultsChange 
}) => {
  const createInvocationWithLabels = (item, results) => {
    const result = results.find(r => r.id === item.id);
    return {
      ...item.invocation,
      labels: result?.labels || []
    };
  };

  const resultsTableData = useMemo(() => {
    if (!results) return [];
    
    // Group results by input hash
    const groupedByInput = results.reduce((acc, result) => {
      const inputHash = JSON.stringify(result.invocation_being_labeled.contents.params);
      if (!acc[inputHash]) {
        acc[inputHash] = {
          items: [],
          input: result.invocation_being_labeled.contents.params,
        };
      }
      acc[inputHash].items.push(result);
      return acc;
    }, {});

    // Calculate mean values and stats for each group
    let tableData = Object.entries(groupedByInput).map(([inputHash, group]) => {
      // If there's only one item in the group, return it directly without grouping
      if (group.items.length === 1) {
        const result = group.items[0];
        return {
          id: result.id,
          invocation: result.invocation_being_labeled,
          labels: result.labels.reduce((acc, label) => {
            acc[label.labeler_id] = label.label_invocation.contents.results;
            return acc;
          }, {}),
          children: []
        };
      }

      // Rest of the existing grouping logic for multiple items
      const children = group.items.map(result => ({
        id: result.id,
        invocation: result.invocation_being_labeled,
        labels: result.labels.reduce((acc, label) => {
          acc[label.labeler_id] = label.label_invocation.contents.results;
          return acc;
        }, {}),
        children: []
      }));

      // Calculate stats for the group
      const labelStats = {};
      if (children.length > 0) {
        const firstChild = children[0];
        Object.keys(firstChild.labels).forEach(labelerId => {
          const values = children
            .map(child => child.labels[labelerId])
            .filter(value => typeof value === 'number' || typeof value === 'boolean');
          
          if (values.length > 0) {
            const mean = values.reduce((a, b) => a + b, 0) / values.length;
            const stdDev = Math.sqrt(
              values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length
            );
            labelStats[labelerId] = {
              mean,
              stdDev,
              min: Math.min(...values),
              max: Math.max(...values)
            };
          }
        });
      }

      // Get all outputs for the preview
      const outputs = children.map(child => 
        child.invocation.contents.results?.content || child.invocation.contents.results
      );

      return {
        id: inputHash,
        invocation: {
          contents: {
            params: group.input,
            results: outputs
          }
        },
        labels: Object.fromEntries(
          Object.entries(labelStats).map(([key, stats]) => [key, stats.mean])
        ),
        labelStats,
        children: children,
        isGroup: true
      };
    });

    // Apply search filter if there's a search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      
      // Helper function to check if an item matches the search query
      const itemMatches = (item) => {
        // For leaf nodes (children)
        if (!item.isGroup) {
          const inputMatch = JSON.stringify(item.invocation.contents.params)
            .toLowerCase()
            .includes(query);

          const outputMatch = JSON.stringify(item.invocation.contents.results)
            .toLowerCase()
            .includes(query);

          const labelMatch = Object.values(item.labels).some(value => 
            String(value).toLowerCase().includes(query)
          );

          return inputMatch || outputMatch || labelMatch;
        }
        
        // For group nodes, check if any children match
        return item.children.some(child => itemMatches(child));
      };

      // Filter the table data, keeping groups that have matching children
      tableData = tableData.map(group => {
        const matchingChildren = group.children.filter(itemMatches);
        
        if (matchingChildren.length > 0) {
          return {
            ...group,
            children: matchingChildren
          };
        }
        return null;
      }).filter(Boolean);

      // Create filtered results array for metrics
      const filteredResults = tableData.flatMap(group => 
        group.children.map(child => {
          // Find original result that matches this child
          return results.find(result => result.id === child.id);
        })
      );
      
      // Notify parent component of filtered results
      onFilteredResultsChange(filteredResults);
    } else {
      // If no search query, reset filtered results
      onFilteredResultsChange(null);
    }

    return tableData;
  }, [results, searchQuery, onFilteredResultsChange]);

  const labelerColumns = useMemo(() => {
    if (!results?.[0]?.labels) return [];
    
    return results[0].labels.map(label => ({
      header: label.labeler_id.split('-')[3] || 'Label',
      key: label.labeler_id,
      render: (item) => {
        return (
          <LabelDisplay 
            value={item.labels[label.labeler_id]} 
            isAggregate={item.isGroup}
            stats={item.isGroup ? {
              min: item.labelStats[label.labeler_id]?.min,
              max: item.labelStats[label.labeler_id]?.max,
              stdDev: item.labelStats[label.labeler_id]?.stdDev
            } : null}
          />
        );
      },
      maxWidth: 150,
      sortable: true,
      sortFn: (a, b) => {
        const aValue = a.labels[label.labeler_id] ?? -Infinity;
        const bValue = b.labels[label.labeler_id] ?? -Infinity;
        return aValue - bValue;
      }
    }));
  }, [results]);

  const columns = [
    { 
      header: 'Input', 
      key: 'input',     
      render: (item, _, { expanded, isHovered }) => (
        <div className={item.isGroup ? '' : (isHovered ? 'opacity-75' : 'opacity-30')}>
          <ContentsRenderer 
            item={item.invocation} 
            field="params"
            typeMatchLevel={1}
          />
        </div>
      ),
      maxWidth: 300,
      sortable: true,
      sortFn: (a, b) => {
        const aInput = JSON.stringify(a.invocation.contents.params);
        const bInput = JSON.stringify(b.invocation.contents.params);
        return aInput.localeCompare(bInput);
      }
    },
    { 
      header: 'Output', 
      key: 'output', 
      render: (item, _, { expanded }) => (
        item.isGroup ? (
          <OutputPreview 
            outputs={item.invocation.contents.results}
            invocation={item.invocation}
            isExpanded={expanded}
          />
        ) : (
          <ContentsRenderer 
            item={item.invocation} 
            field="results"
          />
        )
      ),
      maxWidth: 300,
      sortable: true,
      sortFn: (a, b) => {
        const aOutput = JSON.stringify(a.invocation.contents.results);
        const bOutput = JSON.stringify(b.invocation.contents.results);
        return aOutput.localeCompare(bOutput);
      }
    },
    ...labelerColumns,
  ];

  const handleRowClick = (item, toggleRow) => {
    if (item.isGroup) {
      toggleRow(item.id);
    } else {
      const trace = createInvocationWithLabels(item, results);
      setSelectedTrace(trace);
    }
  };

  const hasNextPage = resultsTableData.length === pageSize;

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectedTrace(null);
        return;
      }

      if (selectedTrace) {
        // Get all navigable items - both ungrouped items and children of grouped items
        const allItems = resultsTableData.flatMap(item => 
          item.isGroup ? item.children : [item]
        );
        
        const currentIndex = allItems.findIndex(item => 
          item.invocation.id === selectedTrace.id
        );

        if (e.key === 'ArrowUp' && currentIndex > 0) {
          e.preventDefault();
          const prevItem = allItems[currentIndex - 1];
          const trace = createInvocationWithLabels(prevItem, results);
          setSelectedTrace(trace);
        } else if (e.key === 'ArrowDown' && currentIndex < allItems.length - 1) {
          e.preventDefault();
          const nextItem = allItems[currentIndex + 1];
          const trace = createInvocationWithLabels(nextItem, results);
          setSelectedTrace(trace);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [resultsTableData, selectedTrace, setSelectedTrace, results]);

  return (
    <HierarchicalTable
      schema={{ columns }}
      data={resultsTableData}
      currentPage={currentPage}
      onPageChange={setCurrentPage}
      pageSize={pageSize}
      hasNextPage={hasNextPage}
      showHierarchical={true}
      expandAll={false}
      initialSortConfig={{ key: 'id', direction: 'desc' }}
      onRowClick={handleRowClick}
      hierarchicalSort={true}
      rowClassName={(item) => 
        !item.isGroup && item.invocation.id === selectedTrace?.id ? 'bg-blue-600 bg-opacity-30' : ''
      }
    />
  );
};

export default EvaluationRunResultsTable;