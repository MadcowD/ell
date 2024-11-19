import React, { useState, useEffect } from "react";
import { FiX, FiMaximize2, FiMinimize2, FiCopy, FiInfo, FiList } from "react-icons/fi";
import { useLocation } from 'react-router-dom';
import ResizableSidebar from '../../ResizableSidebar';
import { InvocationInfoPane } from '../InvocationInfoPane';
import InvocationDataPane from './InvocationDataPane';
import { motion } from 'framer-motion';
import { LMPCardTitle } from "../../depgraph/LMPCardTitle";
import { Card } from "../../common/Card";
import { useLMPs } from "../../../hooks/useBackend";
import { ScrollArea } from "@radix-ui/react-scroll-area";

const InvocationDetailsPopover = ({ invocation : invocationWithoutLMP, onClose, onResize }) => {
  const [activeTab, setActiveTab] = useState("I/O");
  const [sidebarWidth, setSidebarWidth] = useState(window.innerWidth / 2);
  const [isExpanded, setIsExpanded] = useState(false);
  const { data: lmpData } = useLMPs(null, invocationWithoutLMP.lmp_id);
  const lmp = lmpData && lmpData.length > 0 ? lmpData[0] : invocationWithoutLMP.lmp;

  const invocation = { 
    ...invocationWithoutLMP, 
    lmp,
    labels: invocationWithoutLMP.labels
  };

  const handleResize = (newWidth) => {
    setSidebarWidth(newWidth);
    onResize(newWidth);
  };

  const isNarrowForInfo = sidebarWidth < 700;

  const toggleExpand = () => {
    setIsExpanded(!isExpanded);
    onResize(isExpanded ? window.innerWidth / 2 : window.innerWidth);
  };

  const copyInvocationId = () => {
    navigator.clipboard.writeText(invocation.id);
    // Optionally, you can add a toast notification here to inform the user that the ID has been copied
  };

  const location = useLocation();
  const isLmpPage = location.pathname.startsWith('/lmp');

  if(!invocation.lmp) {
    return null;
  }

  return (
    <ResizableSidebar onResize={handleResize} isExpanded={isExpanded}>
      <motion.div 
        className="flex flex-col h-full bg-background text-foreground"
        initial={{ opacity: 0, x: 50 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 50 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center justify-between p-4 bg-card">
          <div className="flex items-center space-x-4 min-w-0 flex-1">
            {!isLmpPage && (
              <div className="flex-shrink-0">
                <Card className="bg-card text-card-foreground">
                  <LMPCardTitle lmp={invocation.lmp} displayVersion shortVersion={true}/>
                </Card>
              </div>
            )}
            <div className="flex items-center min-w-0">
              <div className="flex items-center bg-secondary/20 rounded-md overflow-hidden border border-secondary/30 min-w-0">
                <span className="text-sm font-mono font-medium text-secondary-foreground px-3 py-1.5 truncate">
                  {isNarrowForInfo
                    ? `${invocation.id.slice(0, 8)}...`
                    : invocation.id}
                </span>
                <button
                  onClick={copyInvocationId}
                  className="flex-shrink-0 bg-secondary/30 hover:bg-secondary/40 text-secondary-foreground px-2 py-1.5 transition-colors duration-200"
                  title="Copy Invocation ID"
                >
                  <FiCopy size={12} />
                </button>
              </div>
            </div>
          </div>
          <div className="flex-shrink-0 ml-4">
            <button 
              onClick={onClose} 
              className="text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              <FiX />
            </button>
          </div>
        </div>
      
        <div className="flex space-x-2 p-2 ml-2 bg-muted/30 border-b border-border">
          {[
            { name: "I/O", icon: FiList },
            ...(isNarrowForInfo ? [{ name: "Info", icon: FiInfo }] : [])
          ].map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-all duration-200 ${
                activeTab === name
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
              onClick={() => setActiveTab(name)}
            >
              <Icon className="mr-2" size={16} />
              {name}
            </button>
          ))}
        </div>
        
        <div className="flex flex-grow overflow-hidden">
          <motion.div 
            className={`flex-grow overflow-y-auto ${isNarrowForInfo || activeTab === "Info" ? 'w-full' : 'w-2/3'}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === "I/O" && (
              <ScrollArea>
                <InvocationDataPane invocation={invocation} />
              </ScrollArea>
            )}
            {(activeTab === "Info" || isNarrowForInfo) && (
              <ScrollArea>
                <InvocationInfoPane invocation={invocation} isFullWidth={true} />
              </ScrollArea>
            )}
          </motion.div>
          {!isNarrowForInfo && activeTab === "I/O" && (
            <motion.div 
              className="w-1/3 overflow-y-auto border-l border-gray-700"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
            >
              <InvocationInfoPane invocation={invocation} isFullWidth={false} />
            </motion.div>
          )}
        </div>
      </motion.div>
    </ResizableSidebar>
  );
};

export default InvocationDetailsPopover;