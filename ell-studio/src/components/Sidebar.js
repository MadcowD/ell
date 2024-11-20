import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { FiZap, FiSettings, FiCode, FiDatabase } from 'react-icons/fi';
import { BiCube } from 'react-icons/bi';
import { motion } from 'framer-motion';
import EvaluationsIcon from './evaluations/EvaluationsIcon';

const Sidebar = () => {
  const [isExpanded, setIsExpanded] = useState(false);

  const SidebarLink = ({ to, icon: Icon, label }) => (
    <NavLink
      to={to}
      className={({ isActive }) => `
        group flex items-center py-3 px-4 rounded-lg transition-all duration-200
        ${isActive ? 'bg-accent text-accent-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'}
      `}
    >
      <Icon className="w-5 h-5" />
      {isExpanded && (
        <span className="ml-3 text-sm font-medium">{label}</span>
      )}
      {!isExpanded && (
        <div className="fixed left-16 ml-2 px-2 py-1 bg-popover text-popover-foreground text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10">
          {label}
        </div>
      )}
    </NavLink>
  );

  return (
    <motion.aside 
      initial={false}
      animate={{ width: isExpanded ? 200 : 64 }}
      className="bg-card border-r border-border h-screen py-6 flex flex-col"
    >
      <div className="flex justify-center items-center mb-8">
        <img src="/gif.gif" alt="ell-studio Logo" className="h-4 invert" />
      </div>
      
      <nav className="flex-grow space-y-1 px-2">
        <SidebarLink to="/" icon={BiCube} label="Models" />
        <SidebarLink to="/invocations" icon={FiZap} label="Invocations" />
        <SidebarLink to="/evaluations" icon={EvaluationsIcon} label="Evaluations" />
        {/* <SidebarLink to="/code" icon={FiCode} label="Code" />
        <SidebarLink to="/data" icon={FiDatabase} label="Data" /> */}
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
