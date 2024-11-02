import React from 'react';
import { FiZap, FiClock, FiActivity, FiCpu, FiCheck, FiAlertCircle } from 'react-icons/fi';
import { motion } from 'framer-motion';
import SidePanel from '../../common/SidePanel';
import { Card } from '../../common/Card';
import { getTimeAgo } from '../../../utils/lmpUtils';

function EvaluationRunDetailsSidebar({ run, results }) {
  const totalInvocations = results?.length || 0;
  const duration = run?.end_time && run?.start_time ? 
    new Date(run.end_time) - new Date(run.start_time) : null;
  
  return (
    <SidePanel title="Run Details">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="space-y-2 text-sm"
      >
        <div className="bg-card p-2 rounded">
          <h3 className="text-sm font-semibold text-card-foreground mb-1">Run Info</h3>
          <div className="grid grid-cols-2 gap-y-0.5">
            <div className="flex items-center">
              <FiCheck className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Status:</span>
            </div>
            <div className="text-right flex items-center justify-end">
              {run?.success ? (
                <span className="text-emerald-400/75 flex items-center">
                  <FiCheck size={12} className="mr-1" /> Success
                </span>
              ) : run?.success === false ? (
                <span className="text-rose-400 flex items-center">
                  <FiAlertCircle size={12} className="mr-1" /> Failed
                </span>
              ) : (
                <span className="text-gray-400">Running</span>
              )}
            </div>

            <div className="flex items-center">
              <FiClock className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Started:</span>
            </div>
            <div className="text-right">
              {run?.start_time ? getTimeAgo(new Date(run.start_time)) : 'N/A'}
            </div>

            <div className="flex items-center">
              <FiCpu className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Duration:</span>
            </div>
            <div className="text-right">
              {duration ? `${(duration / 1000).toFixed(1)}s` : 'N/A'}
            </div>
            
            <div className="flex items-center">
              <FiZap className="mr-1 text-muted-foreground" size={12} />
              <span className="text-muted-foreground">Invocations:</span>
            </div>
            <div className="text-right">{totalInvocations}</div>
          </div>

          {run?.error && (
            <div className="mt-2 text-xs text-red-500 break-words">
              Error: {run.error}
            </div>
          )}
        </div>
      </motion.div>
    </SidePanel>
  );
}

export default EvaluationRunDetailsSidebar;