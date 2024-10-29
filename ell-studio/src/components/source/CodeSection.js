import React, { useState, useEffect, useRef } from 'react';
import { FiChevronDown, FiChevronRight, FiCopy, FiCheck } from 'react-icons/fi';
import { CodeHighlighter } from './CodeHighlighter';
import '../../styles/SourceCodeView.css';
import YAML from 'yaml';

export function CodeSection({ 
  title, 
  showCode, 
  setShowCode, 
  lines : linesOverride, 
  isDependent = false, 
  collapsedHeight = '150px',
  enableFormatToggle = false,
  code,
  children,
  showCopyButton = false,
  raw,
  ...rest // Add rest operator to collect remaining props
}) {
    const [isHovering, setIsHovering] = useState(false);
    const [isYamlFormat, setIsYamlFormat] = useState(true);
    const [isCopied, setIsCopied] = useState(false);
    const codeRef = useRef(null);
    const lines = linesOverride ? linesOverride : (raw || code).split('\n').length;
    useEffect(() => {
      if (codeRef.current) {
        codeRef.current.style.maxHeight = showCode ? 'none' : collapsedHeight;
      }
    }, [showCode, collapsedHeight]);

    const toggleFormat = () => {
      setIsYamlFormat(!isYamlFormat);
    };

    const getFormattedCode = () => {
      if (!enableFormatToggle) return code;
      try {
        const jsonObject = JSON.parse(code);
        return isYamlFormat ? YAML.stringify(jsonObject) : JSON.stringify(jsonObject, null, 2);
      } catch (error) {
        console.error("Error parsing JSON:", error);
        return code; // Return original code if parsing fails
      }
    };

    const copyToClipboard = () => {
      navigator.clipboard.writeText(raw || getFormattedCode())
        .then(() => {
          setIsCopied(true);
          setTimeout(() => setIsCopied(false), 2000); // Reset after 2 seconds
        })
        .catch(err => console.error('Failed to copy code: ', err));
    };

    return (
      <div className="code-section mb-4" onClick={() => setShowCode(!showCode)}>
        <div 
          className="section-header flex items-center justify-between w-full text-sm text-gray-300 
          hover:text-white py-2 px-4 rounded-t-md bg-gray-800 hover:bg-gray-700 transition-colors 
          duration-200 cursor-pointer">
          <button
            onClick={() => setShowCode(!showCode)}
            className="flex items-center hover:text-white transition-colors duration-200"
          >
            {showCode ? <FiChevronDown className="mr-2" /> : <FiChevronRight className="mr-2" />}
            {title}
          </button>
          <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
            {enableFormatToggle && (
              <button
                onClick={toggleFormat}
                className="mr-4 text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded"
              >
                {isYamlFormat ? 'YAML' : 'JSON'}
              </button>
            )}
            {showCopyButton && (
              <button
                onClick={copyToClipboard}
                className="mr-4 text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 flex items-center rounded"
              >
                {isCopied ? <FiCheck className="mr-2 text-green-500" /> : <FiCopy className="mr-2" />}
                {isCopied ? 'Copied!' : 'JSON'}
              </button>
            )}
            <span className="text-xs text-gray-400">
              {lines} lines
            </span>
          </div>
        </div>
        <div
          className={`code-container ${showCode ? 'expanded' : ''}`}
          onMouseEnter={() => setIsHovering(true)}
          onMouseLeave={() => setIsHovering(false)}
          ref={codeRef}
          onClick={() => !showCode && setShowCode(true)}
        >
          {children ? children : (
            <CodeHighlighter
              code={getFormattedCode()}
            {...rest} // Spread the remaining props to CodeHighlighter
              language={enableFormatToggle ? (isYamlFormat ? 'yaml' : 'json') : undefined}
            />
          )}
          {!showCode && (
            <div className="gradient-overlay">
              {isHovering && (
                <button
                  className="show-more-button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowCode(true);
                  }}
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