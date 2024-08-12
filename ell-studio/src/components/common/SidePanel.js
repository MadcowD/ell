import React from 'react';
import { ScrollArea } from './ScrollArea';

const SidePanel = ({ title, children }) => (
  <ScrollArea className="h-full bg-[#0d1117] p-4">
    <h2 className="text-lg font-semibold mb-4 text-gray-200 border-b border-gray-700 pb-2">{title}</h2>
    <div className="space-y-4">
      {children}
    </div>
  </ScrollArea>
);

export default SidePanel;