import React, { useState, useEffect, useRef } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import '../styles/SourceCodeView.css';

const SourceCodeView = ({ dependencies, source, uses, showDependenciesInitial = false }) => {
  const [showDependencies, setShowDependencies] = useState(showDependenciesInitial);
  const [showSource, setShowSource] = useState(true);

  const trimmedDependencies = dependencies.trim();
  const dependencyLines = trimmedDependencies ? trimmedDependencies.split('\n').length : 0;
  const sourceLines = source.split('\n').length;
  const dependentLMPs = uses.length;

  useEffect(() => {
    if (dependencyLines > 0 && dependencyLines < 6) {
      setShowDependencies(true);
    }
  }, [dependencyLines]);

  const CodeSection = ({ title, code, showCode, setShowCode, lines, startingLineNumber = 1, isDependent = false }) => {
    const [isHovering, setIsHovering] = useState(false);
    const codeRef = useRef(null);

    useEffect(() => {
      if (codeRef.current) {
        codeRef.current.style.maxHeight = showCode ? 'none' : '150px';
      }
    }, [showCode]);

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
            {isDependent && `, ${dependentLMPs} LMPs`}
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
            showLineNumbers={true}
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
  };

  return (
    <div className="source-code-container">
      {trimmedDependencies && (
        <CodeSection
          title="Dependencies"
          code={trimmedDependencies}
          showCode={showDependencies}
          setShowCode={setShowDependencies}
          lines={dependencyLines}
          isDependent={true}
        />
      )}
      <CodeSection
        title="Source"
        code={source}
        showCode={showSource}
        setShowCode={setShowSource}
        lines={sourceLines}
        startingLineNumber={dependencyLines + 1}
      />
    </div>
  );
};

export default SourceCodeView;