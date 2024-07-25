import React from 'react';
import { FiChevronRight } from 'react-icons/fi';

const TracesRunsPane = ({ traces, onSelectTrace }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-xs text-gray-400 border-b border-gray-800">
            <th className="py-2 px-4"></th>
            <th className="py-2 px-4"></th>
            <th className="py-2 px-4">Name</th>
            <th className="py-2 px-4">Input</th>
            <th className="py-2 px-4">Output</th>
            <th className="py-2 px-4">Start Time</th>
            <th className="py-2 px-4">Latency</th>
          </tr>
        </thead>
        <tbody>
          {traces.map((trace, index) => (
            <tr
              key={index}
              className="border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer"
              onClick={() => onSelectTrace(trace)}
            >
              <td className="py-3 px-4">
                <FiChevronRight className="text-gray-400" />
              </td>
              <td className="py-3 px-4">
                <span className="text-green-400 text-lg">●</span>
              </td>
              <td className="py-3 px-4 font-medium">{trace.name}</td>
              <td className="py-3 px-4 text-sm">{trace.input}</td>
              <td className="py-3 px-4 text-sm">{trace.output?.substring(0, 20)}...</td>
              <td className="py-3 px-4 text-sm">{trace.startTime}</td>
              <td className="py-3 px-4 text-sm text-red-400">{trace.latency}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TracesRunsPane;