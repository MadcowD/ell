import React, { useState, useEffect, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import '../../styles/SourceCodeView.css';

import { CodeSection } from './CodeSection';
import { CodeHighlighter } from './CodeHighlighter';

const BoundedVariableWrapper = ({ children, selectedInvocation, content }) => {
  const var_name = content.split('=')[0].trim();
  const formattedInvocationValue = selectedInvocation?.global_vars?.[var_name] ? `${var_name} = ${JSON.stringify(selectedInvocation?.global_vars?.[var_name], null, 2)}` : '';
  return (
    <div className="relative rounded border border-gray-500 mt-2 pt-1 px-1 pb-1">
      <span className="absolute -top-2 left-2 bg-gray-800 px-1 text-[0.6rem] text-gray-400">
        bound global {!selectedInvocation ?  'at definition' : `at invocation ${selectedInvocation.id}`}
      </span>
      {!selectedInvocation ? children : <CodeHighlighter code={formattedInvocationValue} showLineNumbers={false} defaultRowPadding='' />}
    </div>
  );
};


const SourceCodeView = ({ dependencies, source, uses, showDependenciesInitial = false, selectedInvocation = null }) => {
  const [showDependencies, setShowDependencies] = useState(showDependenciesInitial);
  const [showSource, setShowSource] = useState(true);

  const trimmedDependencies = dependencies.trim();
  const dependencyLines = trimmedDependencies ? trimmedDependencies.split('\n').length : 0;
  const sourceLines = source.split('\n').length;
  const dependentLMPs = uses.length;

  const boundedVariableHooks = useMemo(() => {
    return [{
    name: 'boundedVariable',
    startTag: '#<BV>',
    endTag: '#</BV>',
    wrapper: ({ children, key, content }) => (  
      <BoundedVariableWrapper key={key} selectedInvocation={selectedInvocation} content={content}>
        {children}
      </BoundedVariableWrapper>
      )
    },
    {
      name: 'boundedMutableVariable',
      startTag: '#<BmV>',
      endTag: '#</BmV>',
      wrapper: ({ children, key, content }) => (  
        <BoundedVariableWrapper key={key} selectedInvocation={selectedInvocation} content={content}>
          {children}
        </BoundedVariableWrapper>
        )
    }
  ];
  }, [selectedInvocation]);

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
          customHooks={boundedVariableHooks}
          highlighterStyle={{
            fontSize: '9pt',
            overflow: 'auto',
          }}
        />
      )}
      <CodeSection
        title="Source"
        code={source}
        showCode={showSource}
        setShowCode={setShowSource}
        lines={sourceLines}
        startingLineNumber={dependencyLines + 1}
        highlighterStyle={{
          fontSize: '9pt',
          overflow: 'auto',
        }}
      />
    </div>
  );
};

export default SourceCodeView;