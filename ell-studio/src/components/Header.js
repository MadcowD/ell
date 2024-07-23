import React from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';

const Header = () => {
  const { darkMode } = useTheme();

  return (
    <header className={`bg-gray-800 shadow-lg ${darkMode ? 'text-white' : 'text-gray-900'}`}>
      <div className=" mx-auto px-6 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold">Ell Studio</h1>
        <nav>
          <ul className="flex space-x-4">
            <li><Link to="/" className="hover:text-gray-300">Language Model Programs</Link></li>
          </ul>
        </nav>
      </div>
    </header>
  );
};

export default Header;