import React from "react";
import { FiZap } from "react-icons/fi";
import VersionBadge from "../VersionBadge";
import EvaluationsIcon from "./EvaluationsIcon";

export function EvaluationCardTitle({
    evaluation,
    fontSize = "sm",
    displayVersion = true,
    padding = true,
    scale = 1,
    additionalClassName = '',
    clickable = true,
    shortVersion = false,
    paddingClassOverride = '',
    nameOverride = null,
    showRunCount = true,
    outlineStyle = 'solid',
    ...rest
}) {
    const paddingClass = paddingClassOverride ? paddingClassOverride : padding ? 'p-2' : '';
    
    const scaleClass = `scale-${scale}`;
    const hoverClass = clickable ? 'duration-200 ease-in-out hover:bg-opacity-80 hover:bg-gray-700' : '';
    const cursorClass = clickable ? 'cursor-pointer' : '';

    const outlineClasses = {
        solid: 'bg-blue-100 text-blue-800',
        dashed: 'bg-transparent text-blue-500 border border-dotted border-blue-400'
    };

    return (
        <div className={`flex items-center space-x-2 ${paddingClass} ${scaleClass} transition-colors ${additionalClassName} ${hoverClass} ${cursorClass} rounded-md overflow-hidden`} {...(clickable ? rest : {})}>
            <div className="flex-shrink-0 mr-1">
                <EvaluationsIcon className="w-4 h-4 text-yellow-600" />
            </div>
            {nameOverride ? nameOverride : (
                <code className={`px-2 py-1 rounded-md ${outlineClasses[outlineStyle]} text-${fontSize} font-medium truncate`}>
                    {evaluation.name}
                </code>
            )}
            {displayVersion && (
                <VersionBadge 
                    version={evaluation.version_number} 
                    hash={evaluation.id} 
                    shortVersion={shortVersion}
                    truncationLength={20}
                />
            )}
            {showRunCount && evaluation.runs && evaluation.runs.length > 0 && (
                <div className="flex items-center text-xs text-gray-400" title={`${evaluation.runs.length} runs`}>
                    <FiZap className="w-3 h-3 mr-1" />
                    {evaluation.runs.length}
                </div>
            )}
        </div>
    );
}
