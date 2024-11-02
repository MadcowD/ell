import React, { useMemo, useEffect } from 'react';
import HierarchicalTable from '../HierarchicalTable';
import { Card } from '../common/Card';
import { ContentsRenderer } from '../invocations/ContentsRenderer';
import LabelDisplay from './LabelDisplay';
import InvocationDetailsPopover from '../invocations/details/InvocationDetailsPopover';

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
  setSelectedTrace 
}) => {
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
    return Object.entries(groupedByInput).map(([inputHash, group]) => {
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
  }, [results]);

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
    }));
  }, [results]);

  const columns = [
    { 
      header: 'Input', 
      key: 'input',     
      render: (item, _, { expanded, isHovered }) => (
        item.isGroup && <div className={!item.isGroup ? ( isHovered ? 'opacity-75' : 'opacity-30' ) : ''}>
          <ContentsRenderer 
            item={item.invocation} 
            field="params"
            typeMatchLevel={1}
          />
        </div>
      ),
      maxWidth: 300,
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
    },
    ...labelerColumns,
  ];

  const handleRowClick = (item, toggleRow) => {
    if (item.isGroup) {
      // If it's a parent row, toggle its expanded state using the provided toggleRow function
      toggleRow(item.id);
    } else {
      // If it's a child row, set the selected trace
      setSelectedTrace(item.invocation);
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
        // Find all leaf nodes (non-group items) in the current data
        const leafNodes = resultsTableData.flatMap(group => group.children);
        const currentIndex = leafNodes.findIndex(item => item.invocation.id === selectedTrace.id);

        if (e.key === 'ArrowUp' && currentIndex > 0) {
          setSelectedTrace(leafNodes[currentIndex - 1].invocation);
        } else if (e.key === 'ArrowDown' && currentIndex < leafNodes.length - 1) {
          setSelectedTrace(leafNodes[currentIndex + 1].invocation);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [resultsTableData, selectedTrace, setSelectedTrace]);

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
      rowClassName={(item) => 
        !item.isGroup && item.invocation.id === selectedTrace?.id ? 'bg-blue-600 bg-opacity-30' : ''
      }
    />
  );
};

export default EvaluationRunResultsTable;