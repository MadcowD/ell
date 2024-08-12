import React, { useState, useEffect } from 'react';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "../common/Resizable";
import { ScrollArea } from '../common/ScrollArea';
import InvocationsLayout from '../invocations/InvocationsLayout';

const GenericPageLayout = ({
  children,
  selectedTrace,
  setSelectedTrace,
  sidebarContent,
  showSidebar = true,
}) => {
  const [sidebarVisible, setSidebarVisible] = useState(!selectedTrace && showSidebar);

  useEffect(() => {
    setSidebarVisible(!selectedTrace && showSidebar);
  }, [selectedTrace, showSidebar]);

  return (
    <ResizablePanelGroup direction="horizontal" className="w-full h-screen">
      <ResizablePanel defaultSize={sidebarVisible ? 70 : 100} minSize={30}>
        <InvocationsLayout
          selectedTrace={selectedTrace}
          setSelectedTrace={setSelectedTrace}
          showSidebar={showSidebar}
          containerClass={' flex flex-col h-full'}
        >
            <div className="p-6">
          {children}
            </div>
        </InvocationsLayout>
      </ResizablePanel>
      <ResizableHandle withHandle className="my-handle" />
      <ResizablePanel defaultSize={30} minSize={20} className="bg-[#0d1117]" style={{ display: sidebarVisible ? 'block' : 'none' }}>
        <ScrollArea className="h-full">
          {sidebarContent}
        </ScrollArea>
      </ResizablePanel>
    </ResizablePanelGroup>
  );
};

export default GenericPageLayout;