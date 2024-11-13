import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap, FiCode, FiChevronDown, FiChevronUp } from 'react-icons/fi';
import { Card, CardContent } from '../common/Card';
import VersionBadge from '../VersionBadge';
import { getTimeAgo } from '../../utils/lmpUtils';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import RunSummary from './RunSummary';
import { EvaluationCardTitle } from './EvaluationCardTitle';

const INITIAL_LMP_DISPLAY_COUNT = 2;

const EvaluationCard = ({ evaluation, isGraphMode = false }) => {
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
      <Card className={`hover:bg-accent/50 bg-accent/10 transition-colors duration-200 ${isGraphMode ? '' : 'mb-4'}`}>
        <CardContent className="p-4">
          <div className={`flex ${isGraphMode ? 'flex-col' : 'flex-col lg:flex-row'}`}>
            <div className={`flex-grow ${isGraphMode ? '' : 'lg:pr-4 lg:w-1/2'}`}>
              <EvaluationCardTitle 
                evaluation={evaluation}
                fontSize="sm"
                displayVersion={true}
                shortVersion={false}
                showRunCount={true}
                outlineStyle="solid"
                padding={false}
                additionalClassName="mb-2"
              />
              
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
                  <span>Dataset: {evaluation.dataset_id.substring(0, 8)}</span>
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
              
              {!isGraphMode && evaluatedLMPs.length > 0 && (
                <div className="border-t pt-3 mt-2 hidden lg:block">
                  <h3 className="text-xs font-semibold mb-1 flex items-center">
                    <FiCode className="mr-1" /> Evaluated LMPs
                  </h3>
                  <div className="space-y-1">
                    <Card className="p-0.5 hover:bg-accent/50 transition-colors duration-200">
                      {displayedLMPs.map((lmp) => (
                        <Link key={lmp.lmp_id} to={`/lmp/${lmp.name}/${lmp.lmp_id}`} className="block">
                          <LMPCardTitle lmp={lmp} displayVersion shortVersion={true} showInvocationCount={true} outlineStyle='dashed' additionalClassName="text-[10px]" paddingClassOverride='p-2'/>
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
              <div className={`mt-4 ${isGraphMode ? '' : 'lg:w-1/2 lg:flex-shrink-0 lg:border-l lg:pl-2  lg:mt-0'}`}>
                <h3 className="text-xs font-semibold mb-1 flex items-center">
                  <FiZap className="mr-1 h-3 w-3" /> Latest Run Summary
                </h3>
                <div className={isGraphMode ? '' : 'lg:hidden'}>
                  <Card >
                    <CardContent className="p-0">
                      <RunSummary
                        groupedRuns={groupedRuns}
                        totalRuns={totalRuns}
                        successfulRuns={successfulRuns}
                        isVertical={false}
                      />
                    </CardContent>
                  </Card>
                </div>
                {!isGraphMode && (
                  <div className={'hidden lg:block mt-2'}>
                    <RunSummary
                      groupedRuns={groupedRuns}
                    totalRuns={totalRuns}
                    successfulRuns={successfulRuns}
                    isVertical={false}
                    />
                  </div>
                )}
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
