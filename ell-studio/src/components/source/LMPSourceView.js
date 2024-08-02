import React, { useState, useEffect, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import '../../styles/SourceCodeView.css';

import { CodeSection } from './CodeSection';
import { CodeHighlighter } from './CodeHighlighter';

const BoundedVariableWrapper = ({ children, selectedInvocation, content, initial_global_vars, initial_free_vars }) => {
  const var_name = content.split('=')[0].trim();
  const invocationVars = selectedInvocation ? selectedInvocation.global_vars : initial_global_vars;
  const invocationFreeVars = selectedInvocation ? selectedInvocation.free_vars : initial_free_vars;
  const value = invocationVars?.[var_name] || invocationFreeVars?.[var_name];

  const isGlobal = var_name in invocationVars;
  const isFree = var_name in invocationFreeVars;
  const formattedValue = `${var_name} = ${JSON.stringify(value).replace(/"<Object of type ([^>]+)>"/g, '<Object of type $1>')}`;
  
  return (
    <div className="relative rounded border border-gray-500 mt-2 py-2">
      <span className="absolute -top-2 left-2 bg-gray-800 text-[0.6rem] text-gray-400" style={{'backgroundColor': 'rgb(28, 31, 38)'}}>
        {isGlobal ? 'mutable globalvar' : isFree ? 'freevar' : 'unknown'} {!selectedInvocation ? 'value at lmp definition' : `value at ${selectedInvocation.id}`}
      </span>
      <div className='ml-5'>
        <CodeHighlighter 
          code={formattedValue} 
          showLineNumbers={false} 
          defaultRowPadding='' 
          highlighterStyle={{
            padding: '0px 0px 0px 20px'
          }} 
        />
      </div>
    </div>
  );
};


const LMPSourceView = ({ lmp, showDependenciesInitial = false, selectedInvocation = null }) => {
  const { dependencies, source, uses, initial_global_vars, initial_free_vars } = lmp;

  const [showDependencies, setShowDependencies] = useState(showDependenciesInitial);
  const [showSource, setShowSource] = useState(true);

  const trimmedDependencies = dependencies.trim();
  const dependencyLines = trimmedDependencies ? trimmedDependencies.split('\n').length : 0;
  const sourceLines = source.split('\n').length;
  const dependentLMPs = uses.length;

  const boundedVariableHooks = useMemo(() => {
    const mutableBVWrapper = ({ children, key, content }) => (  
      <BoundedVariableWrapper 
        key={key} 
        selectedInvocation={selectedInvocation} 
        content={content} 
        initial_global_vars={initial_global_vars}
        initial_free_vars={initial_free_vars}
      >
        {children}
      </BoundedVariableWrapper>
    );

    return [{
    name: 'boundedVariable',
    startTag: '#<BV>',
    endTag: '#</BV>',
    wrapper: ({children, key, content}) => {
      return <>{children}</>
    }},
    {
      name: 'boundedMutableVariable',
      startTag: '#<BmV>',
      endTag: '#</BmV>',
      wrapper: mutableBVWrapper
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
          overflow: 'auto',
          textIndent: '-20px',
          paddingLeft: '20px',
        }}
      />
    </div>
  );
};

export default LMPSourceView;