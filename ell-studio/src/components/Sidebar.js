import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiCode, FiActivity } from 'react-icons/fi';

const Sidebar = () => {
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path ? 'bg-[#2a2f3a] text-white' : 'text-gray-400 hover:bg-[#2a2f3a] hover:text-white';
  };

  return (
    <aside className="w-16 bg-[#1c1f26] flex flex-col items-center py-4">
      <Link to="/" className={`p-3 rounded-lg mb-4 ${isActive('/')}`}>
        <FiHome className="w-6 h-6" />
      </Link>
      <Link to="/lmp/:id" className={`p-3 rounded-lg mb-4 ${isActive('/lmp/:id')}`}>
        <FiCode className="w-6 h-6" />
      </Link>
      <Link to="/traces" className={`p-3 rounded-lg mb-4 ${isActive('/traces')}`}>
        <FiActivity className="w-6 h-6" />
      </Link>
    </aside>
  );
};

export default Sidebar;