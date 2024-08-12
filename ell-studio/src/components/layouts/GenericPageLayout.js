import React from 'react';
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
  return (
    <ResizablePanelGroup direction="horizontal" className="w-full h-screen">
      <ResizablePanel defaultSize={selectedTrace ? 100 : 70} minSize={30}>
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
      {!selectedTrace && showSidebar && (
        <>
          <ResizableHandle withHandle className="my-handle" />
          <ResizablePanel defaultSize={30} minSize={20} className="bg-[#0d1117">
            <ScrollArea className="h-full">
              {sidebarContent}
            </ScrollArea>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};

export default GenericPageLayout;