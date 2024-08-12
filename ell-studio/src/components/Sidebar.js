import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { FiZap, FiSettings, FiCode, FiDatabase } from 'react-icons/fi';
import { BiCube } from 'react-icons/bi';
import { motion } from 'framer-motion';

const Sidebar = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  const SidebarLink = ({ to, icon: Icon, label }) => (
    <NavLink
      to={to}
      className={({ isActive }) => `
        group flex items-center py-3 px-4 rounded-lg transition-all duration-200
        ${isActive ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground'}
      `}
    >
      <Icon className="w-5 h-5" />
      {isExpanded && (
        <span className="ml-3 text-sm font-medium">{label}</span>
      )}
      {!isExpanded && (
        <div className="fixed left-16 ml-2 px-2 py-1 bg-background text-foreground text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
          {label}
        </div>
      )}
    </NavLink>
  );

  return (
    <motion.aside 
      initial={false}
      animate={{ width: isExpanded ? 200 : 64 }}
      className="bg-background h-screen py-6 flex flex-col"
    >
      <div className="flex justify-center items-center mb-8">
        <img src="/gif.gif" alt="ell-studio Logo" className="h-4 invert" />
      </div>
      
      <nav className="flex-grow space-y-1 px-2">
        <SidebarLink to="/" icon={BiCube} label="Models" />
        <SidebarLink to="/traces" icon={FiZap} label="Traces" />
        <SidebarLink to="/code" icon={FiCode} label="Code" />
        <SidebarLink to="/data" icon={FiDatabase} label="Data" />
      </nav>
      
      <div className="mt-auto px-2">
        <SidebarLink to="/settings" icon={FiSettings} label="Settings" />
      </div>

      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="mt-4 mx-auto p-2 rounded-full bg-background hover:bg-muted transition-colors duration-200"
      >
        <svg className={`w-4 h-4 text-foreground transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </motion.aside>
  );
};

export default Sidebar;