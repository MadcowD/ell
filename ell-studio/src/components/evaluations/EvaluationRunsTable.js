import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import HierarchicalTable from '../HierarchicalTable';
import { Card } from '../common/Card';
import { getTimeAgo } from '../../utils/lmpUtils';
import VersionBadge from '../VersionBadge';

const EvaluationRunsTable = ({ runs, currentPage, setCurrentPage, pageSize, onSelectRun, currentlySelectedRun }) => {
  const navigate = useNavigate();

  const onClickLMP = (run) => {
    navigate(`/lmp/${run.evaluated_lmp.name}/${run.evaluated_lmp.lmp_id}`);
  };

  const runsTableData = useMemo(() => {
    return runs.map(run => ({
      ...run,
      id: run.id,
      name: run.evaluated_lmp.name,
      version: run.evaluated_lmp.version_number + 1,
      created_at: new Date(run.end_time),
    }));
  }, [runs]);

  const getMetricColumns = () => {
    if (runs.length === 0 || !runs[0].labeler_summaries) return [];
    
    return runs[0].labeler_summaries.map(summary => ({
      header: summary.evaluation_labeler.name,
      key: summary.evaluation_labeler.id,
      render: (item) => {
        const metricSummary = item.labeler_summaries.find(s => s.evaluation_labeler_id === summary.evaluation_labeler_id);
        return (
          <div className="font-mono text-sm font-semibold">
            {metricSummary ? metricSummary.data.mean.toFixed(2) : 'N/A'}
          </div>
        );
      },
      maxWidth: 150,
      sortable: true,
    }));
  };

  const columns = [
    { 
      header: 'LMP', 
      key: 'name', 
      render: (item) => (
        <Card noMinW={true}>
          <LMPCardTitle 
            lmp={item.evaluated_lmp} 
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
      maxWidth: 200,
    },
    { 
      header: 'Version', 
      key: 'version', 
      render: (item) => (
        <VersionBadge 
          version={item.version} 
          lmpId={item.evaluated_lmp.lmp_id} 
          className='text-xs scale-85 inline-block' 
        />
      ), 
      maxWidth: 150,
      sortable: true
    },

    ...getMetricColumns(),
    { 
        header: 'Finished', 
        key: 'created_at', 
        render: (item) => <span className="text-gray-400">{getTimeAgo(item.created_at)}</span>, 
        maxWidth: 150,
        sortable: true
      },
  ];

  const initialSortConfig = { key: 'created_at', direction: 'desc' };

  const hasNextPage = runsTableData.length === pageSize;

  return (
    <HierarchicalTable
      schema={{
        columns: columns
      }}
      data={runsTableData}
      onRowClick={onSelectRun}
      initialSortConfig={initialSortConfig}
      rowClassName={(item) => 
        item.id === currentlySelectedRun?.id ? 'bg-blue-600 bg-opacity-30' : ''
      }
      currentPage={currentPage}
      onPageChange={setCurrentPage}
      pageSize={pageSize}
      hasNextPage={hasNextPage}
      links={[]}
    />
  );
};

export default EvaluationRunsTable;
