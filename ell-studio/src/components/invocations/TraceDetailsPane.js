import React from 'react';
import { FiFilter } from 'react-icons/fi';

const TraceDetailsPain = ({ trace }) => {
  return (
    <div className="w-64 bg-[#0d1117] border-l border-gray-800 p-4 text-sm">
      <h2 className="text-lg font-semibold mb-4">TRACE</h2>
      <div className="flex items-center justify-between mb-2">
        <button className="px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">Collapse</button>
        <button className="px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">Stats</button>
        <button className="px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">Filter</button>
        <select className="bg-[#1c2128] text-xs rounded px-2 py-1">
          <option>Most relevant</option>
        </select>
      </div>
      <div className="bg-[#161b22] p-2 rounded mb-2">
        <div className="flex items-center">
          <span className="text-blue-400 mr-2">◢</span>
          <span className="font-medium">{trace.name}</span>
          <span className="text-green-400 ml-auto">●</span>
        </div>
        <div className="flex items-center text-xs mt-1">
          <span className="text-red-400 mr-2">{trace.latency}</span>
          <span className="text-gray-400 mr-2">{trace.tokens} tokens</span>
          <span className="bg-gray-700 px-1 rounded">{trace.tags[0]}</span>
        </div>
      </div>
      {/* Add more trace items here */}
      <p className="text-xs text-gray-500 mt-2">
        Some runs have been hidden. <a href="#" className="text-blue-400">Show 10 hidden runs</a>
      </p>
    </div>
  );
};

export default TraceDetailsPain;