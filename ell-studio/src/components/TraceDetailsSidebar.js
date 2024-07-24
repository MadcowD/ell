import React, { useState, useRef, useEffect } from 'react';
import { FiLink, FiCopy, FiChevronDown, FiChevronRight } from 'react-icons/fi';

const TraceDetailsSidebar = ({ trace, onClose }) => {
  const [activeTab, setActiveTab] = useState('Run');
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(600);
  const resizeRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (resizeRef.current) {
        const newWidth = document.body.clientWidth - e.clientX;
        setSidebarWidth(Math.max(400, newWidth));
      }
    };

    const handleMouseUp = () => {
      resizeRef.current = null;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    const handleMouseDown = (e) => {
      resizeRef.current = e.target;
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    };

    const resizer = document.getElementById('sidebar-resizer');
    resizer.addEventListener('mousedown', handleMouseDown);

    return () => {
      resizer.removeEventListener('mousedown', handleMouseDown);
    };
  }, []);

  return (
    <>
      <div id="sidebar-resizer" className="w-1 bg-gray-600 cursor-col-resize" />
      <div className="bg-[#0d1117] border-l border-gray-800 overflow-y-auto flex flex-col" style={{ width: sidebarWidth }}>
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center space-x-2">
            <FiLink className="text-blue-400" />
            <h2 className="text-xl font-semibold text-blue-400">{trace.name}</h2>
          </div>
          <div className="flex items-center space-x-4">
            <button className="text-gray-400 hover:text-white">
              <FiCopy /> Run ID
            </button>
            <button className="text-gray-400 hover:text-white">
              <FiCopy /> Trace ID
            </button>
            <button onClick={onClose} className="text-gray-400 hover:text-white">
              ✕
            </button>
          </div>
        </div>
        <div className="flex border-b border-gray-800">
          <button
            className={`px-4 py-2 ${activeTab === 'Run' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400'}`}
            onClick={() => setActiveTab('Run')}
          >
            Run
          </button>
          <button
            className={`px-4 py-2 ${activeTab === 'Feedback' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400'}`}
            onClick={() => setActiveTab('Feedback')}
          >
            Feedback
          </button>
          <button
            className={`px-4 py-2 ${activeTab === 'Metadata' ? 'text-blue-400 border-b-2 border-blue-400' : 'text-gray-400'}`}
            onClick={() => setActiveTab('Metadata')}
          >
            Metadata
          </button>
        </div>
        <div className="flex flex-grow">
          <div className="flex-grow p-4 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <button
                className="flex items-center text-gray-300"
                onClick={() => setInputExpanded(!inputExpanded)}
              >
                <span className="mr-2">Input</span>
                {inputExpanded ? <FiChevronDown /> : <FiChevronRight />}
              </button>
              <span className="text-gray-500">YAML</span>
            </div>
            {inputExpanded && (
              <pre className="bg-[#161b22] p-4 rounded text-sm text-gray-300 mb-4">
                <code>
                  {`input: What is a document loader?
chat_history: []`}
                </code>
              </pre>
            )}
            <div className="flex justify-between items-center mb-4">
              <button
                className="flex items-center text-gray-300"
                onClick={() => setOutputExpanded(!outputExpanded)}
              >
                <span className="mr-2">Output</span>
                {outputExpanded ? <FiChevronDown /> : <FiChevronRight />}
              </button>
            </div>
            {outputExpanded && (
              <pre className="bg-[#161b22] p-4 rounded text-sm text-gray-300">
                <code>
                  {trace.output}
                </code>
              </pre>
            )}
          </div>
          <div className="w-64 bg-[#0d1117] p-4 border-l border-gray-800 text-sm">
            <div className="mb-2">
              <p className="text-gray-500">START TIME</p>
              <p className="text-gray-300">{trace.startTime}</p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">END TIME</p>
              <p className="text-gray-300">{trace.endTime}</p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">TIME TO FIRST TOKEN</p>
              <p className="text-gray-300">{trace.timeToFirstToken}</p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">STATUS</p>
              <p className="text-green-400 flex items-center">
                <span className="mr-1">●</span> Success
              </p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">TOTAL TOKENS</p>
              <p className="text-gray-300">{trace.tokens} tokens</p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">LATENCY</p>
              <p className="text-red-400">{trace.latency}</p>
            </div>
            <div className="mb-2">
              <p className="text-gray-500">TYPE</p>
              <p className="text-gray-300 bg-blue-900 inline-block px-2 py-0.5 rounded">Chain</p>
            </div>
            <div>
              <p className="text-gray-500">TAGS</p>
              <p className="text-gray-300 bg-gray-700 inline-block px-2 py-0.5 rounded">{trace.tags[0]}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default TraceDetailsSidebar;