import React, { useState, useMemo } from 'react';
import TraceDetailsSidebar from './TraceDetailsSidebar';
import { useNavigate, useLocation } from 'react-router-dom';

const PageWithTracesLayout = ({ children, selectedTrace, setSelectedTrace, showSidebar = false }) => {
  const [sidebarWidth, setSidebarWidth] = useState(window.innerWidth / 2);
  const navigate = useNavigate();
  const location = useLocation();

  const handleSidebarResize = (newWidth) => {
    setSidebarWidth(newWidth);
  };

  const mainContentStyle = useMemo(() => {
    if (showSidebar && selectedTrace) {
      const mainWidth = window.innerWidth - sidebarWidth - 64;
      if (mainWidth < ((window.innerWidth - 64) / 2)) {
        return { width: '50%' };
      }
      return { width: `${mainWidth}px` };
    }
    return {};
  }, [showSidebar, selectedTrace, sidebarWidth]);

  const handleCloseSidebar = () => {
    setSelectedTrace(null);
    navigate(location.pathname);
  };

  return (
    <>
      <div className="flex bg-[#0d1117] text-gray-300 h-screen overflow-hidden" style={mainContentStyle}>
        <div className="flex-grow p-6 overflow-y-auto hide-scrollbar">
          {children}
        </div>
      </div>
      {showSidebar && selectedTrace && (
        <TraceDetailsSidebar
          invocation={selectedTrace}
          onClose={handleCloseSidebar}
          onResize={handleSidebarResize}
        />
      )}
    </>
  );
};

export default PageWithTracesLayout;