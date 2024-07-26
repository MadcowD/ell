import React from "react";
import { BiCube } from "react-icons/bi";

export function LMPCardTitle({lmp, fontSize, displayVersion, ...rest}) {
    return (
        <div className="flex items-center p-2 space-x-2" {...rest}>
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
            {displayVersion && <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 border border-gray-300">
                v{lmp.version_number + 1}
            </span>}
        </div>
    );
}