import React, { useEffect, useState } from 'react'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '../common/Resizable'
import { ScrollArea } from '../common/ScrollArea'
import InvocationsLayout from '../invocations/InvocationsLayout'

const GenericPageLayout = ({ children, selectedTrace, setSelectedTrace, sidebarContent, showSidebar = true }) => {
    const [sidebarVisible, setSidebarVisible] = useState(!selectedTrace && showSidebar)

    useEffect(() => {
        setSidebarVisible(!selectedTrace && showSidebar)
    }, [selectedTrace, showSidebar])

    return (
        <ResizablePanelGroup direction="horizontal" className="w-full h-screen bg-background">
            <ResizablePanel defaultSize={sidebarVisible ? 70 : 100} minSize={30}>
                <InvocationsLayout
                    selectedTrace={selectedTrace}
                    setSelectedTrace={setSelectedTrace}
                    showSidebar={showSidebar}
                    containerClass="flex flex-col h-full bg-background">
                    <div className="p-6 bg-background">{children}</div>
                </InvocationsLayout>
            </ResizablePanel>
            <ResizableHandle withHandle className="my-handle bg-border" />
            <ResizablePanel
                defaultSize={30}
                minSize={20}
                className="bg-background"
                style={{ display: sidebarVisible ? 'block' : 'none' }}>
                <ScrollArea className="h-full bg-background">{sidebarContent}</ScrollArea>
            </ResizablePanel>
        </ResizablePanelGroup>
    )
}

export default GenericPageLayout
