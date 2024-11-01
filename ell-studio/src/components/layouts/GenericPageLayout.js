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
  minimizeSidebar = false,
}) => {
  const [sidebarVisible, setSidebarVisible] = useState(!selectedTrace && showSidebar);
  const [isSmallScreen, setIsSmallScreen] = useState(false);

  useEffect(() => {
    // Function to check window size
    const checkWindowSize = () => {
      setIsSmallScreen(window.innerWidth < 1024); // 1024px is typical laptop width
    };

    // Initial check
    checkWindowSize();

    // Add event listener
    window.addEventListener('resize', checkWindowSize);

    // Cleanup
    return () => window.removeEventListener('resize', checkWindowSize);
  }, []);

  useEffect(() => {
    setSidebarVisible(!selectedTrace && showSidebar && !(minimizeSidebar && isSmallScreen));
  }, [selectedTrace, showSidebar, minimizeSidebar, isSmallScreen]);

  return (
    <ResizablePanelGroup direction="horizontal" className="w-full h-screen bg-background">
      <ResizablePanel 
        defaultSize={sidebarVisible ? (minimizeSidebar ? 80 : 70) : 100} 
        minSize={30}
      >
        <InvocationsLayout
          selectedTrace={selectedTrace}
          setSelectedTrace={setSelectedTrace}
          showSidebar={showSidebar}
          containerClass="flex flex-col h-full bg-background"
        >
          <div className="p-6 bg-background">
            {children}
          </div>
        </InvocationsLayout>
      </ResizablePanel>
      {sidebarVisible && (
        <>
          <ResizableHandle withHandle className="my-handle bg-border" />
          <ResizablePanel 
            defaultSize={minimizeSidebar ? 20 : 30} 
            minSize={20} 
            className="bg-background"
          >
            <ScrollArea className="h-full bg-background">
              {sidebarContent}
            </ScrollArea>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};

export default GenericPageLayout;