import React from "react";
import { BiCube } from "react-icons/bi";
import { FiZap, FiTool } from "react-icons/fi";
import VersionBadge from "../VersionBadge";

export function LMPCardTitle({
    lmp,
    fontSize,
    displayVersion,
    padding = true,
    scale = 1,
    additionalClassName = '',
    clickable = true,
    shortVersion = false,
    paddingClassOverride = '',
    nameOverride = null,
    showInvocationCount = true,
    outlineStyle = 'solid',
    nameOverridePrint = null,  // New prop for printing name override
    ...rest
}) {
    const paddingClass = paddingClassOverride ? paddingClassOverride : padding ? 'p-2' : '';
    
    const scaleClass = `scale-${scale}`;
    const hoverClass = clickable ? ' duration-200 ease-in-out hover:bg-opacity-80 hover:bg-gray-700' : '';
    const cursorClass = clickable ? 'cursor-pointer' : '';

    // Define outline styles
    const outlineClasses = {
        solid: lmp.is_lmp ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800',
        dashed: lmp.is_lmp ? 'bg-transparent text-blue-500 border border-dotted border-blue-400' : 'bg-transparent text-yellow-500 border border-dotted border-yellow-400'
    };

    return (
        <div className={`flex items-center space-x-2 ${paddingClass} ${scaleClass} transition-colors ${additionalClassName} ${hoverClass} ${cursorClass} rounded-md overflow-hidden`} {...(clickable ? rest : {})}>
            <div className="flex-shrink-0">
                {lmp.lmp_type === "LM" ? 
                    <BiCube className="h-4 w-4 text-yellow-600" />
                : lmp.lmp_type === "TOOL" ?
                    <FiTool className="h-4 w-4 text-white-600" />
                : lmp.lmp_type === "METRIC" ?
                    <FiZap className="h-4 w-4 text-blue-600" />
                : <BiCube className="h-4 w-4 text-yellow-600" />}
            </div>
            {nameOverride ? nameOverride : <code className={`px-2 py-1 rounded-md ${outlineClasses[outlineStyle]} text-${fontSize} font-medium truncate`}>
                 {nameOverridePrint || lmp.name}()
            </code> }
            {displayVersion && <VersionBadge version={lmp.version_number + 1} lmpId={lmp.lmp_id} shortVersion={shortVersion} />}
            {showInvocationCount && lmp.num_invocations > 0 && (
                <div className="flex items-center text-xs text-gray-400" title={`${lmp.num_invocations} invocations`}>
                    <FiZap className="w-3 h-3 mr-1" />
                    {lmp.num_invocations}
                </div>
            )}
        </div>
    );
}