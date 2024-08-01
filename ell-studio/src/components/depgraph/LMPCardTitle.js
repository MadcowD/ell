import React from "react";
import { BiCube } from "react-icons/bi";
import VersionBadge from "../VersionBadge";

export function LMPCardTitle({
    lmp,
    fontSize,
    displayVersion,
    padding = true,
    scale = 1,
    additionalClassName = '',
    clickable = true,
    ...rest
}) {
    const paddingClass = padding ? 'p-2' : '';
    const scaleClass = `scale-${scale}`;
    const hoverClass = clickable ? ' duration-200 ease-in-out hover:bg-opacity-80 hover:bg-gray-700' : '';
    const cursorClass = clickable ? 'cursor-pointer' : '';

    return (
        <div className={`flex items-center space-x-2 ${paddingClass} ${scaleClass} transition-colors ${additionalClassName} ${hoverClass} ${cursorClass} rounded-md`} {...(clickable ? rest : {})}>
            <div className="flex-shrink-0">
                {lmp.is_lmp ? 
                    <div className="h-4 w-4">
                        <img src="/gif.gif" alt="LMP logo" className="h-full w-full object-contain invert" />
                    </div>
                : <BiCube className="h-4 w-4 text-yellow-600" />}
            </div>
            <code className={`px-2 py-1 rounded-md ${lmp.is_lmp ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800'} text-${fontSize} font-medium`}>
                {lmp.name}()
            </code>
            {displayVersion && <VersionBadge version={lmp.version_number + 1} lmpId={lmp.id} />}
        </div>
    );
}