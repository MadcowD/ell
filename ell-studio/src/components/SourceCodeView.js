import React, { useState, useEffect, useRef } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import '../styles/SourceCodeView.css';

import { CodeSection } from './CodeSection';

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
  // UseEffect for showDependenciesInitial
  useEffect(() => {
    if(showDependenciesInitial) setShowDependencies(showDependenciesInitial);
  }, [showDependenciesInitial]);


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