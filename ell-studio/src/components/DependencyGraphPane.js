import React from 'react';
import { FiChevronRight } from 'react-icons/fi';
import { Link } from 'react-router-dom';

const DependencyGraphPane = ({ uses }) => {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="text-left text-xs text-gray-400 border-b border-gray-800">
            <th className="py-2 px-4"></th>
            <th className="py-2 px-4">Dependency Name</th>
            <th className="py-2 px-4">LMP ID</th>
          </tr>
        </thead>
        <tbody>
          {uses.map((use) => (
            <tr key={use.lmp_id} className="border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer">
              <td className="py-3 px-4">
                <FiChevronRight className="text-gray-400" />
              </td>
              <td className="py-3 px-4 font-medium">
                <Link to={`/lmp/${use.lmp_id}`} className="hover:underline">{use.name}()</Link>
              </td>
              <td className="py-3 px-4 text-sm">{use.lmp_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DependencyGraphPane;