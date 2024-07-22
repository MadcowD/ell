import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';

const Sidebar = () => {
  const { darkMode, toggleDarkMode } = useTheme();

  return (
    <aside className="w-64 bg-gray-800 p-6">
      <nav className="space-y-4">
        <Link to="/" className="block text-gray-300 hover:text-white">Dashboard</Link>
        <Link to="/models" className="block text-gray-300 hover:text-white">Models</Link>
        <Link to="/datasets" className="block text-gray-300 hover:text-white">Datasets</Link>
        <Link to="/visualizations" className="block text-gray-300 hover:text-white">Visualizations</Link>
      </nav>
      <div className="mt-8">
        <button
          onClick={toggleDarkMode}
          className="px-4 py-2 bg-gray-700 text-gray-300 rounded hover:bg-gray-600"
        >
          {darkMode ? 'Light Mode' : 'Dark Mode'}
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;