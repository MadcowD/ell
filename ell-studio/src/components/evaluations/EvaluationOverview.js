import React from 'react';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap, FiCopy } from 'react-icons/fi';
import { Card, CardContent } from '../common/Card';
import RunSummary from './RunSummary';
import { getTimeAgo } from '../../utils/lmpUtils';
import LMPSourceView from "../source/LMPSourceView";
import VersionBadge from "../VersionBadge";
import toast from "react-hot-toast";

function EvaluationOverview({ evaluation, groupedRuns }) {
  const handleCopyCode = (lmp) => {
    const fullCode = `${lmp.dependencies.trim()}\n\n${lmp.source.trim()}`;
    navigator.clipboard
      .writeText(fullCode)
      .then(() => {
        toast.success("Code copied to clipboard", {
          duration: 2000,
          position: "top-center",
        });
      })
      .catch((err) => {
        console.error("Failed to copy code: ", err);
        toast.error("Failed to copy code", {
          duration: 2000,
          position: "top-center",
        });
      });
  };

  const renderLMPSourceView = (lmp, title) => (
    <div className=" bg-card rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center space-x-4">
          <h2 className="text-md font-semibold text-card-foreground">{title}</h2>
          <VersionBadge version={lmp.version_number + 1} />
        </div>
        <div className="flex space-x-4 items-center">
          <button
            className="p-1 rounded bg-secondary hover:bg-secondary/80 transition-colors"
            onClick={() => handleCopyCode(lmp)}
          >
            <FiCopy className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="overflow-hidden">
        <LMPSourceView
          lmp={lmp}
          showDependenciesInitial={true}
          viewMode="Source"
        />
        {/* {console.log(lmp)} */}
      </div>
    </div>
  );

  return (
    <>
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Evaluation</h2>
        {evaluation.labelers.map((labeler, index) => (
          renderLMPSourceView(labeler.labeling_lmp, `Metric: ${labeler.name}`)
        ))}
      </div>

   
    </>
  );
}

export default EvaluationOverview;
