import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent } from '../../common/Card';
import { EvaluationCardTitle } from '../EvaluationCardTitle';
import { LMPCardTitle } from '../../depgraph/LMPCardTitle';
import LMPSourceView from '../../source/LMPSourceView';

function EvaluationRunOverview({ run }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Link to={`/evaluations/${run?.evaluation_id}`}>
          <Card className="bg-card text-card-foreground">
            <div className="p-2 flex items-center space-x-2">
              <EvaluationCardTitle 
                evaluation={run?.evaluation}
                fontSize="text-sm"
                displayVersion={false}
                shortVersion={false}
                showRunCount={false}
                padding={false}
              />
            </div>
          </Card>
        </Link>
        <span className="text-muted-foreground">•</span>
        <div className="text-xl font-semibold">
          Run #{run?.id}
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-2">Evaluated LMP</h3>
        <div className="bg-accent/10">
          <CardContent className="p-4">
            <LMPCardTitle 
              lmp={run?.evaluated_lmp}
              displayVersion
              shortVersion={false}
            />
            <div className="mt-4">
              <LMPSourceView
                lmp={run?.evaluated_lmp}
                viewMode="Source"
                showDependenciesInitial={false}
              />
            </div>
          </CardContent>
        </div>
      </div>
    </div>
  );
}

export default EvaluationRunOverview; 