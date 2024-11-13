import React from 'react';
import { FiZap, FiBarChart2, FiDatabase, FiTag, FiClock, FiHash } from 'react-icons/fi';
import MetricTable from './MetricTable';
import { getTimeAgo } from '../../utils/lmpUtils';
import SidePanel from '../common/SidePanel';
import { motion } from 'framer-motion';
import VersionBadge from '../VersionBadge';

function EvaluationDetailsSidebar({ evaluation }) {
  return (
    <SidePanel title="Evaluation Details">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-2 text-sm"
      >
        <div className="bg-card p-2 rounded">
          <div className="flex justify-between items-center mb-1">
            <h3 className="text-sm font-semibold text-card-foreground">Version Info</h3>
            <VersionBadge version={evaluation?.version_number || 1} hash={evaluation?.id} />
          </div>
          <div className="grid grid-cols-2 gap-y-0.5">
            <div className="flex items-center">
              <FiClock className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Created:</span>
            </div>
            <div className="text-right">{getTimeAgo(new Date(evaluation?.created_at))}</div>
            <div className="flex items-center">
              <FiZap className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Runs:</span>
            </div>
            <div className="text-right">{evaluation?.runs.length}</div>
            <div className="flex items-center">
              <FiBarChart2 className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Datapoints:</span>
            </div>
            <div className="text-right">{evaluation?.n_evals}</div>
            <div className="flex items-center">
              <FiHash className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Dataset:</span>
            </div>
            <div className="text-right">{evaluation?.dataset_id.substring(0, 8)}</div>
            <div className="flex items-center">
              <FiTag className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Metrics:</span>
            </div>
            <div className="text-right">{evaluation?.labelers.length}</div>
          </div>
        </div>
        {/* TODO ADD MROE INFO. */}
        <div className="bg-card p-2 rounded">
          {/* <h3 className="text-sm font-semibold text-card-foreground mb-1">Metrics</h3> */}
          {/* {evaluation && (
            // <MetricTable 
            //   summaries={evaluation.runs[evaluation.runs.length - 1].labeler_summaries.filter(summary => summary.is_scalar)}
            //   historicalData={evaluation.runs.reduce((acc, run) => {
            //     run.labeler_summaries.forEach(summary => {
            //       if (!acc[summary.evaluation_labeler_id]) {
            //         acc[summary.evaluation_labeler_id] = [];
            //       }
            //       acc[summary.evaluation_labeler_id].push(summary.data);
            //     });
            //     return acc;
            //   }, {})}
            //   isVertical={true}
            // />
          )} */}
        </div>
      </motion.div>
    </SidePanel>
  );
}

export default EvaluationDetailsSidebar;
