import React, { useState, useEffect, useRef } from 'react';

const ResizableSidebar = ({ children, onResize, initialWidth = window.innerWidth / 2, minWidth = 400 }) => {
  const [sidebarWidth, setSidebarWidth] = useState(initialWidth);
  const resizeRef = useRef(null);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (resizeRef.current) {
        const newWidth = document.body.clientWidth - e.clientX;
        const newSidebarWidth = Math.max(minWidth, newWidth);
        setSidebarWidth(newSidebarWidth);
        onResize(newSidebarWidth);
      }
    };

    const handleMouseUp = () => {
      resizeRef.current = null;
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };

    const handleMouseDown = (e) => {
      e.preventDefault();
      resizeRef.current = e.target;
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
    };

    const resizer = document.getElementById("sidebar-resizer");
    resizer.addEventListener("mousedown", handleMouseDown);

    const handleWindowResize = () => {
      const newWidth = Math.max(minWidth, sidebarWidth);
      setSidebarWidth(newWidth);
      onResize(newWidth);
    };

    window.addEventListener("resize", handleWindowResize);

    return () => {
      resizer.removeEventListener("mousedown", handleMouseDown);
      window.removeEventListener("resize", handleWindowResize);
    };
  }, [onResize, minWidth, sidebarWidth]);

  return (
    <div 
      className="fixed top-0 right-0 h-full border-l border-gray-800 overflow-hidden flex flex-col shadow-xl z-50 bg-[#0d1117]"
      style={{ width: sidebarWidth }}
    >
      <div id="sidebar-resizer" className="absolute left-0 top-0 bottom-0 w-[1px] bg-gray-600 cursor-col-resize" />
      {children}
    </div>
  );
};

export default ResizableSidebar;