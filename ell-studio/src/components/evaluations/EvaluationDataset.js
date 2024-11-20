import React, { useMemo, useState } from 'react';
import { useDataset } from '../../hooks/useBackend';
import HierarchicalTable from '../HierarchicalTable';
import { ContentsRenderer } from '../invocations/ContentsRenderer';
import SearchAndFiltersBar from './runs/SearchAndFiltersBar';

function EvaluationDataset({ evaluation }) {
  const { data: datasetData, isLoading, isError, error } = useDataset(evaluation?.dataset_id);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredData = useMemo(() => {
    if (!datasetData?.data) return [];
    if (!searchQuery) return datasetData.data;

    const query = searchQuery.toLowerCase();
    
    return datasetData.data.filter(item => {
      // Convert the entire item to a string for searching
      const itemString = JSON.stringify(item).toLowerCase();
      return itemString.includes(query);
    });
  }, [datasetData, searchQuery]);

  const columns = useMemo(() => {
    if (!datasetData?.data?.[0]) return [];

    return Object.keys(datasetData.data[0]).map(key => ({
      header: key,
      key: key,
      render: (item) => (
        <ContentsRenderer 
          item={{
            contents: {
              results: item[key]
            }
          }}
          field="results"
          typeMatchLevel={1}
        />
      ),
      maxWidth: 300,
      sortable: true,
      sortFn: (a, b) => {
        const aValue = a[key];
        const bValue = b[key];
        
        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return aValue - bValue;
        }
        return String(aValue).localeCompare(String(bValue));
      }
    }));
  }, [datasetData]);

  // Handle case where there's no dataset
  if (!evaluation?.dataset_id) {
    return (
      <div className="text-sm text-muted-foreground">
        This evaluation was run without a dataset. Each example was generated on-the-fly.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {isLoading && (
        <div className="text-sm text-muted-foreground">Loading dataset...</div>
      )}
      {isError && (
        <div className="text-sm text-red-500">
          {error?.response?.data?.detail || 'Error loading dataset'}
        </div>
      )}
      {datasetData?.data && datasetData.data.length > 0 && (
        <div className="space-y-2">
          <div className="text-sm text-muted-foreground mb-4">
            Dataset size: {Math.round(datasetData.size / 1024)} KB • 
            {' '}{datasetData.data.length} examples
            {searchQuery && ` • ${filteredData.length} matches`}
          </div>

          <SearchAndFiltersBar 
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
          />
          
          <HierarchicalTable
            schema={{ columns }}
            data={filteredData}
            pageSize={10}
            showHierarchical={false}
            initialSortConfig={{ 
              key: datasetData.data[0] ? Object.keys(datasetData.data[0])[0] : null, 
              direction: 'asc' 
            }}
            className="max-h-[600px]"
          />
        </div>
      )}
      {!datasetData?.data && (
        <div className="text-sm text-muted-foreground">
          This evaluation was created without a dataset and is purely "generative".
        </div>
      )}
    </div>
  );
}

export default EvaluationDataset; 