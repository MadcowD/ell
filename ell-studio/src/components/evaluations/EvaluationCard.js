import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap, FiCode, FiChevronDown, FiChevronUp } from 'react-icons/fi';
import { Card, CardHeader, CardContent } from '../common/Card';
import VersionBadge from '../VersionBadge';
import { getTimeAgo } from '../../utils/lmpUtils';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import RunSummary from './RunSummary';

const INITIAL_LMP_DISPLAY_COUNT = 2;

const EvaluationCard = ({ evaluation }) => {
  const [showAllLMPs, setShowAllLMPs] = useState(false);
  const totalRuns = evaluation.runs.length;
  const successfulRuns = evaluation.runs.filter(run => run.success).length;

  const groupedRuns = useMemo(() => {
    const groups = {};
    evaluation.runs.forEach(run => {
      const lmpName = run.evaluated_lmp.name;
      if (!groups[lmpName]) groups[lmpName] = [];
      groups[lmpName].push(run);
    });
    return groups;
  }, [evaluation.runs]);

  const latestRuns = useMemo(() => 
    Object.values(groupedRuns).map(runs => 
      runs.reduce((latest, current) => 
        new Date(current.end_time) > new Date(latest.end_time) ? current : latest
      )
    ), [groupedRuns]);

  const evaluatedLMPs = latestRuns.map(run => run.evaluated_lmp)
    .sort((a, b) => b.version_number - a.version_number);

  const displayedLMPs = showAllLMPs ? evaluatedLMPs : evaluatedLMPs.slice(0, INITIAL_LMP_DISPLAY_COUNT);

  return (
    <Link to={`/evaluations/${evaluation.id}`}>
      <Card className="hover:bg-accent/50 transition-colors duration-200">
        <CardContent className="p-4">
          <div className="flex">
            <div className="flex-grow pr-4">
              <div className="flex items-center space-x-2 mb-2">
                <FiBarChart2 className="h-4 w-4 text-yellow-600" />
                <code className="px-2 py-1 rounded-md bg-blue-100 text-blue-800 text-sm font-medium truncate">
                  {evaluation.name}
                </code>
                <VersionBadge 
                  version={evaluation.version_number} 
                  hash={evaluation.id} 
                  shortVersion={false}
                  truncationLength={20}
                />
                <div className="flex items-center text-xs text-gray-400" title={`${totalRuns} runs`}>
                  <FiZap className="w-3 h-3 mr-1" />
                  {totalRuns}
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground mb-2">
                <div className="flex items-center">
                  <FiZap className="mr-1 h-3 w-3" />
                  <span>{totalRuns} runs ({successfulRuns} successful)</span>
                </div>
                <div className="flex items-center">
                  <FiBarChart2 className="mr-1 h-3 w-3" />
                  <span>{evaluation.n_evals} datapoints</span>
                </div>
                <div className="flex items-center">
                  <FiDatabase className="mr-1 h-3 w-3" />
                  <span>Dataset: {evaluation.dataset_hash.substring(0, 8)}</span>
                </div>
                <div className="flex items-center">
                  <FiTag className="mr-1 h-3 w-3" />
                  <span>{evaluation.labelers.length} metrics</span>
                </div>
                <div className="flex items-center col-span-2">
                  <FiClock className="mr-1 h-3 w-3" />
                  <span>Created: {getTimeAgo(new Date(evaluation.created_at))}</span>
                </div>
              </div>
              
              {evaluatedLMPs.length > 0 && (
                <div className="border-t pt-3 mt-2">
                  <h3 className="text-xs font-semibold mb-1 flex items-center">
                    <FiCode className="mr-1" /> Evaluated LMPs
                  </h3>
                  <div className="space-y-1">
                    <Card className="p-0.5 hover:bg-accent/50 transition-colors duration-200">
                      {displayedLMPs.map((lmp) => (
                        <Link key={lmp.lmp_id} to={`/lmp/${lmp.name}/${lmp.lmp_id}`} className="block">
                          <LMPCardTitle lmp={lmp} displayVersion shortVersion={true} showInvocationCount={true} additionalClassName="text-[10px]" paddingClassOverride='p-2'/>
                        </Link>
                      ))}
                    </Card>
                  </div>
                  {evaluatedLMPs.length > INITIAL_LMP_DISPLAY_COUNT && (
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        setShowAllLMPs(!showAllLMPs);
                      }}
                      className="mt-1 text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center"
                    >
                      {showAllLMPs ? (
                        <>
                          <FiChevronUp className="mr-1" /> Show less
                        </>
                      ) : (
                        <>
                          <FiChevronDown className="mr-1" /> Show {evaluatedLMPs.length - INITIAL_LMP_DISPLAY_COUNT} more
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}
            </div>
            
            {totalRuns > 0 && (
              <div className="w-1/3 flex-shrink-0 border-l pl-4">
                <RunSummary
                  groupedRuns={groupedRuns}
                  totalRuns={totalRuns}
                  successfulRuns={successfulRuns}
                />
              </div>
            )}
          </div>

          {evaluation.commit_message && (
            <p className="mt-2 text-xs text-muted-foreground italic">{evaluation.commit_message}</p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
};

export default EvaluationCard;