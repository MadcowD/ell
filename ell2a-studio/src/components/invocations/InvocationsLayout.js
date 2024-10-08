import React, { useState, useMemo, useEffect, useCallback } from 'react';
import InvocationDetailsSidevar from './details/InvocationDetailsPopover';
import { useNavigate, useLocation } from 'react-router-dom';

const InvocationsLayout = ({ children, selectedTrace, setSelectedTrace, showSidebar = false, containerClass = '' }) => {
  const [sidebarWidth, setSidebarWidth] = useState(window.innerWidth / 2);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const navigate = useNavigate();
  const location = useLocation();

  const handleSidebarResize = useCallback((newWidth) => {
    setSidebarWidth(newWidth);
  }, []);

  useEffect(() => {
    const handleWindowResize = () => {
      setWindowWidth(window.innerWidth);
      setSidebarWidth(prevWidth => Math.min(prevWidth, window.innerWidth / 2));
    };

    window.addEventListener('resize', handleWindowResize);

    return () => {
      window.removeEventListener('resize', handleWindowResize);
    };
  }, []);

  const mainContentStyle = useMemo(() => {
    if (showSidebar && selectedTrace) {
      const mainWidth = windowWidth - sidebarWidth - 64;
      if (mainWidth < ((windowWidth - 64) / 2)) {
        return { width: `${(windowWidth - 64) / 2}px` };
      }
      return { width: `${mainWidth}px` };
    }
    return {};
  }, [showSidebar, selectedTrace, sidebarWidth, windowWidth]);

  const handleCloseSidebar = () => {
    setSelectedTrace(null);
    navigate(location.pathname);
  };

  return (
    <>
      <div className={`flex bg-[#0d1117] text-gray-300 h-screen overflow-hidden ${containerClass}`} style={mainContentStyle}>
        <div className="flex-grow overflow-y-auto hide-scrollbar">
          {children}
        </div>
      </div>
      {showSidebar && selectedTrace && (
        <InvocationDetailsSidevar
          invocation={selectedTrace}
          onClose={handleCloseSidebar}
          onResize={handleSidebarResize}
        />
      )}
    </>
  );
};

export default InvocationsLayout;