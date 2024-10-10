import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiUsers, FiCheckCircle, FiZap, FiCode } from 'react-icons/fi';
import { Card, CardHeader, CardContent } from '../common/Card';
import { Badge } from '../common/Badge';
import VersionBadge from '../VersionBadge';
import { getTimeAgo } from '../../utils/lmpUtils';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import RunSummary from './RunSummary';

const INITIAL_LMP_DISPLAY_COUNT = 2;

const EvaluationCard = ({ evaluation }) => {
  const [showAllLMPs, setShowAllLMPs] = useState(false);
  const totalRuns = evaluation.runs.length;
  const successfulRuns = evaluation.runs.filter(run => run.success).length;

  // Group runs by LMP FQN
  const groupedRuns = useMemo(() => {
    const groups = {};
    evaluation.runs.forEach(run => {
      const fqn = `${run.evaluated_lmp.name}.${run.evaluated_lmp.lmp_id}`;
      if (!groups[fqn]) {
        groups[fqn] = [];
      }
      groups[fqn].push(run);
    });
    return groups;
  }, [evaluation.runs]);

  // Get the latest run for each LMP
  const latestRuns = useMemo(() => {
    return Object.values(groupedRuns).map(runs => runs[runs.length - 1]);
  }, [groupedRuns]);

  // Extract the evaluated LMPs from the latest runs
  const evaluatedLMPs = latestRuns.map(run => run.evaluated_lmp)
    .sort((a, b) => b.version_number - a.version_number);

  const displayedLMPs = showAllLMPs ? evaluatedLMPs : evaluatedLMPs.slice(0, INITIAL_LMP_DISPLAY_COUNT);

  return (
    <Link to={`/evaluations/${evaluation.id}`}>
      <Card className="hover:bg-accent/50 transition-colors duration-200">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-2">
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
              {totalRuns > 0 && (
                <div className="flex items-center text-xs text-gray-400" title={`${totalRuns} runs`}>
                  <FiZap className="w-3 h-3 mr-1" />
                  {totalRuns}
                </div>
              )}
            </div>
            <Badge variant={totalRuns > 0 ? 'success' : 'default'}>
              {totalRuns > 0 ? 'Active' : 'Draft'}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4 text-sm text-muted-foreground mb-4">
            <div className="flex items-center">
              <FiBarChart2 className="mr-2" />
              <span>{evaluation.n_evals} datapoints</span>
            </div>
            <div className="flex items-center">
              <FiDatabase className="mr-2" />
              <span>Dataset: {evaluation.dataset_hash.substring(0, 8)}</span>
            </div>
            <div className="flex items-center">
              <FiTag className="mr-2" />
              <span>{evaluation.labelers.length} metrics</span>
            </div>
            <div className="flex items-center">
              <FiClock className="mr-2" />
              <span>Created: {getTimeAgo(new Date(evaluation.created_at))}</span>
            </div>
          </div>
          
          {evaluatedLMPs.length > 0 && (
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-semibold mb-2 flex items-center">
                <FiCode className="mr-2" /> Evaluated LMPs
              </h3>
              <div className="space-y-0.5">
                {displayedLMPs.map((lmp) => (
                  <Link key={lmp.lmp_id} to={`/lmp/${lmp.name}/${lmp.lmp_id}`} className="block">
                    <Card className="p-0.5 hover:bg-accent/50 transition-colors duration-200">
                      <LMPCardTitle lmp={lmp} displayVersion showInvocationCount={true} additionalClassName="text-xs" paddingClassOverride='p-2'/>
                    </Card>
                  </Link>
                ))}
                {!showAllLMPs && evaluatedLMPs.length > INITIAL_LMP_DISPLAY_COUNT && (
                  <div className="text-xs text-muted-foreground italic mt-1">
                    and {evaluatedLMPs.length - INITIAL_LMP_DISPLAY_COUNT} more LMP{evaluatedLMPs.length - INITIAL_LMP_DISPLAY_COUNT > 1 ? 's' : ''}
                  </div>
                )}
              </div>
              {evaluatedLMPs.length > INITIAL_LMP_DISPLAY_COUNT && (
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    setShowAllLMPs(!showAllLMPs);
                  }}
                  className="mt-2 text-xs text-blue-600 hover:text-blue-800 font-medium"
                >
                  {showAllLMPs ? 'Show less' : 'Show all LMPs'}
                </button>
              )}
            </div>
          )}

          {totalRuns > 0 && (
            <RunSummary
              groupedRuns={groupedRuns}
              totalRuns={totalRuns}
              successfulRuns={successfulRuns}
            />
          )}

          {evaluation.commit_message && (
            <p className="mt-4 text-sm text-muted-foreground">{evaluation.commit_message}</p>
          )}
        </CardContent>
      </Card>
    </Link>
  );
};

export default EvaluationCard;