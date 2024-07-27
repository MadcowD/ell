import React, { useState, useEffect, useRef } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import '../styles/SourceCodeView.css';

export function CodeSection({ 
  title, 
  code, 
  showCode, 
  setShowCode, 
  lines, 
  startingLineNumber = 1, 
  isDependent = false, 
  collapsedHeight = '150px',
  showLineNumbers = true // New prop with default value
}) {
    const [isHovering, setIsHovering] = useState(false);
    const codeRef = useRef(null);
  
    useEffect(() => {
      if (codeRef.current) {
        codeRef.current.style.maxHeight = showCode ? 'none' : collapsedHeight;
      }
    }, [showCode, collapsedHeight]);
  
    return (
      <div className="code-section mb-4">
        <button
          onClick={() => setShowCode(!showCode)}
          className="section-header flex items-center justify-between w-full text-sm text-gray-300 hover:text-white py-2 px-4 rounded-t-md bg-gray-800 hover:bg-gray-700 transition-colors duration-200"
        >
          <span className="flex items-center">
            {showCode ? <FiChevronDown className="mr-2" /> : <FiChevronRight className="mr-2" />}
            {title}
          </span>
          <span className="text-xs text-gray-400">
            {lines} lines
          </span>
        </button>
        <div
          className={`code-container ${showCode ? 'expanded' : ''}`}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          ref={codeRef}
          onClick={() => !showCode && setShowCode(true)}
        >
          <SyntaxHighlighter
            language="python"
            style={atomDark}
            showLineNumbers={showLineNumbers}
            startingLineNumber={startingLineNumber}
            customStyle={{
              margin: 0,
              padding: '1em',
              borderRadius: '0 0 6px 6px',
            }}
          >
            {code}
          </SyntaxHighlighter>
          {!showCode && (
            <div className="gradient-overlay">
              {isHovering && (
                <button
                  className="show-more-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowCode(true);
                  } }
                >
                  Show more ({lines} lines)
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }