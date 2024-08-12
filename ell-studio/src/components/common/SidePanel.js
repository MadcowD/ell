import React from 'react';
import { ScrollArea } from './ScrollArea';

const SidePanel = ({ title, children }) => (
  <ScrollArea className="h-full bg-background p-4">
    <h2 className="text-lg font-semibold mb-4 text-foreground border-b border-border pb-2">{title}</h2>
    <div className="space-y-4">
      {children}
    </div>
  </ScrollArea>
);

export default SidePanel;