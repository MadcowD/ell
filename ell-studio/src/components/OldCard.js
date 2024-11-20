import React from "react";

export function OldCard({ children, title, noMinW, ...rest }) {
  return (
    <div
      className={`relative rounded-lg border border-gray-700 text-white inline-block ${noMinW ? '' : 'min-w-[150px]'}`}
      {...rest}
    >
        {children}
    </div>
  );
}
