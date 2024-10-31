import React, { useMemo } from 'react';
import HierarchicalTable from '../HierarchicalTable';
import { Card } from '../common/Card';
import { ContentsRenderer } from '../invocations/ContentsRenderer';

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

const EvaluationRunResultsTable = ({ results, currentPage, setCurrentPage, pageSize }) => {
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

    // Calculate mean values for each group and structure the data
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

      // Calculate mean values for the group
      const meanLabels = {};
      if (children.length > 0) {
        const firstChild = children[0];
        Object.keys(firstChild.labels).forEach(labelerId => {
          const values = children
            .map(child => child.labels[labelerId])
            .filter(value => typeof value === 'number');
          
          if (values.length > 0) {
            const sum = values.reduce((a, b) => a + b, 0);
            meanLabels[labelerId] = sum / values.length;
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
            results: outputs // Store all outputs for the preview
          }
        },
        labels: meanLabels,
        children: children,
        isGroup: true
      };
    });
  }, [results]);

  // Get unique labeler IDs from the first result
  const labelerColumns = useMemo(() => {
    if (!results?.[0]?.labels) return [];
    
    return results[0].labels.map(label => ({
      header: label.labeler_id.split('-')[3] || 'Label', // Extract metric name from ID
      key: label.labeler_id,
      render: (item) => (
        <div className="font-mono text-sm">
          {typeof item.labels[label.labeler_id] === 'number' 
            ? item.isGroup 
              ? `${item.labels[label.labeler_id].toFixed(2)}`
              : item.labels[label.labeler_id].toFixed(2)
            : item.labels[label.labeler_id]}
        </div>
      ),
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

  const hasNextPage = resultsTableData.length === pageSize;

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
    />
  );
};

export default EvaluationRunResultsTable;