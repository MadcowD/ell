import React from "react";
import { BiCube } from "react-icons/bi";

export function LMPCardTitle({lmp, fontSize, ...rest}) {
    return (
      <div className="flex items-center p-1" {...rest}>
        {lmp.is_lmp  ? 
          <div className="h-2.5 w-3 o">
            <img src="/gif.gif" alt="logo" className="h-full invert" />
          </div>
        : <BiCube />} 
        <code className={`rounded-md ml-1 ${(lmp.is_lmp ) ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800 '} text-${fontSize}`}>
          {lmp.name}()
        </code>
      </div>
    );
  }