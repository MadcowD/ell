import React, { useState, useRef, useEffect, useMemo } from "react";
import { FiLink, FiCopy, FiChevronDown, FiClock, FiTag } from "react-icons/fi";

import ResizableSidebar from '../../ResizableSidebar';
import { InvocationInfoPane } from '../InvocationInfoPane';
import InvocationDataPane from './InvocationDataPane';

const InvocationDetailsPopover = ({ invocation, onClose, onResize }) => {
  const [activeTab, setActiveTab] = useState("Details");
  const [isClicked, setIsClicked] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(window.innerWidth / 2);

  const handleSidebarClick = () => {
    setIsClicked(!isClicked);
  };

  const handleResize = (newWidth) => {
    setSidebarWidth(newWidth);
    onResize(newWidth);
  };

  const isNarrowForInfo = sidebarWidth < 600;
  console.log("invocation", invocation)

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
            Details
          </button>
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
              <div className="flex-grow w-2/3 overflow-y-auto hide-scrollbar">
                <InvocationDataPane key="invocation-data-pane" invocation={invocation} />
              </div>
              {!isNarrowForInfo && (
                <div className="w-1/3 overflow-y-auto hide-scrollbar">
                  <InvocationInfoPane invocation={invocation} isFullWidth={false} />
                </div>
              )}
            </>
          )}
          {isNarrowForInfo && activeTab === "Info" && (
            <div className="flex-grow overflow-y-auto w-full hide-scrollbar">
              <InvocationInfoPane invocation={invocation} isFullWidth={true} />
            </div>
          )}
        </div>
      </div>
    </ResizableSidebar>
  );
};

export default InvocationDetailsPopover;