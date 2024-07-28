import React, { useState, useRef, useEffect, useMemo } from "react";
import { FiLink, FiCopy, FiChevronDown, FiClock, FiTag } from "react-icons/fi";
import { lstrCleanStringify } from './lstrCleanStringify';
import { CodeSection } from './CodeSection';
import { TraceGraph } from './TraceGraph';

const InvocationDetailsSidebar = ({ invocation, onClose }) => {
  const [activeTab, setActiveTab] = useState("Details");
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(document.body.clientWidth * 0.75);
  const resizeRef = useRef(null);
  const [showTraceView, setShowTraceView] = useState(true);

  const argsLines = useMemo(() => {
    return invocation.args.length > 0 ? lstrCleanStringify(invocation.args, 1) : null;
  }, [invocation.args]);

  const kwargsLines = useMemo(() => {
    return lstrCleanStringify(invocation.kwargs, 1);
  }, [invocation.kwargs]);

  const hasKwargs = useMemo(() => {
    return Object.keys(invocation.kwargs).length > 0;
  }, [invocation.kwargs]);

  useEffect(() => {
    if ((argsLines && argsLines.split('\n').length > 10) || (hasKwargs && kwargsLines.split('\n').length > 10)) {
      setInputExpanded(false);
    }
  }, [argsLines, kwargsLines, hasKwargs]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (resizeRef.current) {
        const newWidth = document.body.clientWidth - e.clientX;
        setSidebarWidth(Math.max(800, newWidth));
      }
    };

    const handleMouseUp = () => {
      resizeRef.current = null;
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    const handleMouseDown = (e) => {
      resizeRef.current = e.target;
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    };

    const resizer = document.getElementById("sidebar-resizer");
    resizer.addEventListener("mousedown", handleMouseDown);

    return () => {
      resizer.removeEventListener("mousedown", handleMouseDown);
    };
  }, []);



  return (
    <>
      <div id="sidebar-resizer" className="w-1 bg-gray-600 cursor-col-resize" />
      <div
        className="bg-[#0d1117] border-l border-gray-800 overflow-y-auto flex flex-col hide-scrollbar"
        style={{ width: sidebarWidth }}
      >
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
          <button
            className={`px-4 py-2 ${
              activeTab === "Results"
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-400"
            }`}
            onClick={() => setActiveTab("Results")}
          >
            Results
          </button>
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
        </div>
        <div className="flex flex-grow source-code-container">
          <div className="bg-[#0d1117] border-r border-gray-800 w-80 overflow-y-auto hide-scrollbar">
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
          </div>
          <div className="flex-grow p-4 overflow-y-auto w-[400px] hide-scrollbar">
            {argsLines && (
              <CodeSection
                title="Args"
                code={argsLines}
                showCode={inputExpanded}
                setShowCode={setInputExpanded}
                collapsedHeight={'300px'}
                lines={argsLines.split('\n').length}
                language="json"
                showLineNumbers={false}
              />
            )} 

            {hasKwargs && (
              <CodeSection
                title="Kwargs"
                code={kwargsLines}
                showCode={inputExpanded}
                setShowCode={setInputExpanded}
                collapsedHeight={'300px'}
                lines={kwargsLines.split('\n').length}
                language="json"
                showLineNumbers={false}
              />
            )}

            {
              invocation.results.map((result, index) => (
                <CodeSection
                  key={index}
                  title={`Output ${index + 1}`}
                  code={result.content}
                  showCode={outputExpanded}
                  setShowCode={setOutputExpanded}
                  lines={result.content.split('\n').length}
                  language="text"
                  showLineNumbers={false}
                />
              ))
            }
          </div>

          <div className="w-64 bg-[#0d1117] p-4 border-l border-gray-800 text-sm hide-scrollbar">
            <div className="mb-2">
              <p className="text-gray-500">CREATED AT</p>
              <p className="text-gray-300">{new Date(invocation.created_at).toTimeString()}</p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">LATENCY</p>
              {/* <p className="text-gray-300">{formatDuration(invocation.latency_ms)}</p> */}
            </div>
            <div className="mb-2">
              <p className="text-gray-500">PROMPT TOKENS</p>
              <p className="text-gray-300">
                {invocation.prompt_tokens || "N/A"}
              </p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">COMPLETION TOKENS</p>
              <p className="text-gray-300">
                {invocation.completion_tokens || "N/A"}
              </p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">LMP TYPE</p>
              <p className="text-gray-300 bg-blue-900 inline-block px-2 py-0.5 rounded">
                {invocation.lmp.is_lm ? "LM" : "LMP"}
              </p>
            </div>
            <div>
              <p className="text-gray-500">DEPENDENCIES</p>
              <p className="text-gray-300">{invocation.lmp.dependencies}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default InvocationDetailsSidebar;