import React, { useState, useEffect, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2 } from 'react-icons/fi';
import '../../styles/SourceCodeView.css';

import { CodeSection } from './CodeSection';
import { CodeHighlighter } from './CodeHighlighter';

const BoundedVariableWrapper = ({ children, selectedInvocation,  content, merged_initial_bound_vars }) => {
  const var_name = content.split('=')[0].trim();
  const mergedInvocationBoundVars = useMemo(() => selectedInvocation ? { ...selectedInvocation.global_vars, ...selectedInvocation.free_vars } : merged_initial_bound_vars, [selectedInvocation, merged_initial_bound_vars]);
  const value = mergedInvocationBoundVars?.[var_name];
  const formattedValue = `${var_name} = ${JSON.stringify(value)}`;
  return (
    <div className="relative rounded border border-gray-500 mt-2 py-2">
      <span className="absolute -top-2 left-2 bg-gray-800  text-[0.6rem]  text-gray-400">
        bound global {!selectedInvocation ?  'at definition' : `at invocation ${selectedInvocation.id}`}
      </span>
       <div className='ml-5'>
       <CodeHighlighter code={formattedValue} showLineNumbers={false} defaultRowPadding='' highlighterStyle={{
          padding: '0px'
        }} />
       </div>
    </div>
  );
};


const LMPSourceView = ({ lmp, showDependenciesInitial = false, selectedInvocation = null }) => {
  const { dependencies, source, uses, initial_global_vars, initial_free_vars } = lmp;

  console.log(lmp)
  const merged_initial_bound_vars = useMemo(() => {
    return { ...initial_global_vars, ...initial_free_vars };
  }, [initial_global_vars, initial_free_vars]);

  const [showDependencies, setShowDependencies] = useState(showDependenciesInitial);
  const [showSource, setShowSource] = useState(true);

  const trimmedDependencies = dependencies.trim();
  const dependencyLines = trimmedDependencies ? trimmedDependencies.split('\n').length : 0;
  const sourceLines = source.split('\n').length;
  const dependentLMPs = uses.length;

  const boundedVariableHooks = useMemo(() => {
    const wrapper = ({ children, key, content }) => (  
      <BoundedVariableWrapper key={key} selectedInvocation={selectedInvocation} content={content} merged_initial_bound_vars={merged_initial_bound_vars} >
        {children}
      </BoundedVariableWrapper>
      );

    return [{
    name: 'boundedVariable',
    startTag: '#<BV>',
    endTag: '#</BV>',
    wrapper
    },
    {
      name: 'boundedMutableVariable',
      startTag: '#<BmV>',
      endTag: '#</BmV>',
      wrapper
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

export default LMPSourceView;