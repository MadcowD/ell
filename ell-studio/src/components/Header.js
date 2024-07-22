import React from 'react';
import { useTheme } from '../contexts/ThemeContext';

const Header = () => {
  const { darkMode } = useTheme();

  return (
    <header className={`bg-gray-800 shadow-lg ${darkMode ? 'text-white' : 'text-gray-900'}`}>
      <div className="container mx-auto px-6 py-4">
        <h1 className="text-2xl font-bold">LMP Visualization Studio</h1>
      </div>
    </header>
  );
};

export default Header;