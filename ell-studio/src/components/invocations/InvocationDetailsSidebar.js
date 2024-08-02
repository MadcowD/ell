import React, { useState, useRef, useEffect, useMemo } from "react";
import { FiLink, FiCopy, FiChevronDown, FiClock, FiTag } from "react-icons/fi";
import { lstrCleanStringify } from '../../utils/lstrCleanStringify';
import { CodeSection } from '../source/CodeSection';
import { TraceGraph } from './TraceGraph';
import ResizableSidebar from '../ResizableSidebar';
import { InvocationInfoPane } from './InvocationInfoPane';
import InvocationDataPane from './InvocationDataPane';

const InvocationDetailsSidebar = ({ invocation, onClose, onResize }) => {
  const [activeTab, setActiveTab] = useState("Details");
  const [showTraceView, setShowTraceView] = useState(true);
  const [isClicked, setIsClicked] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(window.innerWidth / 2);

  const handleSidebarClick = () => {
    setIsClicked(!isClicked);
  };

  const handleResize = (newWidth) => {
    setSidebarWidth(newWidth);
    onResize(newWidth);
  };

  const isNarrowForTrace = sidebarWidth < 750;
  const isNarrowForInfo = sidebarWidth < 600;

  const renderTraceView = () => (
    <div className="p-4">
      <h2 className="text-xl font-bold text-white mb-4">TRACE</h2>
      <div className="flex space-x-2 mb-4">
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm">Collapse</button>
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm">Stats</button>
        <button className="bg-gray-800 text-white px-3 py-1 rounded text-sm">Filter</button>
      </div>
      <div className="relative mb-4">
        <select className="bg-gray-800 text-white w-full p-2 rounded appearance-none text-sm">
          <option>Most relevant</option>
        </select>
        <FiChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 text-white" />
      </div>
      <TraceGraph from={invocation} />
      <div className="mt-4 text-gray-400 text-sm flex items-center">
        <span className="mr-1">ℹ️</span>
        Some runs have been hidden. <a href="#" className="text-blue-400 hover:underline ml-1">Show 10 hidden runs</a>
      </div>
    </div>
  );

  return (
    <ResizableSidebar onResize={handleResize}>
      <div className="flex-grow overflow-y-auto hide-scrollbar">
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center space-x-2">
            <FiLink className="text-blue-400" />
            <h2 className="text-xl font-semibold text-blue-400">
              {invocation.lmp.name}
            </h2>
          </div>
          <div className="flex items-center space-x-4">
            <button className="text-gray-400 hover:text-white">
              <FiCopy /> Invocation ID
            </button>
          </div>{" "}
          <button onClick={onClose} className="text-gray-400 hover:text-white">
            ✕
          </button>
        </div>
        <div className="flex border-b border-gray-800">
          <button
            className={`px-4 py-2 ${
              activeTab === "Details"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400"
            }`}
            onClick={() => setActiveTab("Details")}
          >
            {isNarrowForTrace ? "Data" : "Details"}
          </button>
          {isNarrowForTrace && (
            <button
              className={`px-4 py-2 ${
                activeTab === "Trace"
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-gray-400"
              }`}
              onClick={() => setActiveTab("Trace")}
            >
              Trace
            </button>
          )}
          {isNarrowForInfo && (
            <button
              className={`px-4 py-2 ${
                activeTab === "Info"
                  ? "text-blue-400 border-b-2 border-blue-400"
                  : "text-gray-400"
              }`}
              onClick={() => setActiveTab("Info")}
            >
              Info
            </button>
          )}
        </div>
        <div className="flex flex-grow source-code-container">
          {activeTab === "Details" && (
            <>
              {!isNarrowForTrace && (
                <div className="bg-[#0d1117] border-r border-gray-800 w-80 overflow-y-auto hide-scrollbar">
                  {renderTraceView()}
                </div>
              )}
              <InvocationDataPane key="invocation-data-pane" invocation={invocation} />
              {!isNarrowForInfo && <InvocationInfoPane invocation={invocation} isFullWidth={false} />}
            </>
          )}
          {activeTab === "Results" && (
            <InvocationDataPane invocation={invocation} />
          )}
          {isNarrowForTrace && activeTab === "Trace" && (
            <div className="flex-grow overflow-y-auto w-full hide-scrollbar">
              {renderTraceView()}
            </div>
          )}
          {isNarrowForInfo && activeTab === "Info" && <InvocationInfoPane invocation={invocation} isFullWidth={true} />}
        </div>
      </div>
    </ResizableSidebar>
  );
};

export default InvocationDetailsSidebar;