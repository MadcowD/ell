import React from "react";

export function Card({ children, title, ...rest }) {
  return (
    <div
      className="relative rounded-lg border border-gray-700 text-white min-w-[150px] max-h-[300px]"
      {...rest}
    >
      
      <div
        className="h-full flex items-center justify-center"
      >
        {children}
      </div>
    </div>
  );
}
