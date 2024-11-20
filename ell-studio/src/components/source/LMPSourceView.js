import React, { useState, useEffect, useMemo } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { FiChevronDown, FiChevronRight, FiMaximize2, FiMinimize2, FiCopy, FiRefreshCw } from 'react-icons/fi';
import '../../styles/SourceCodeView.css';
import { OldCard } from "../OldCard";
import { useNavigate } from 'react-router-dom';

import { CodeSection } from './CodeSection';
import { CodeHighlighter } from './CodeHighlighter';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';

const BoundedVariableWrapper = ({ children, selectedInvocation, content, initial_global_vars, initial_free_vars }) => {
  const var_name = content.split('=')[0].trim();
  const invocationVars = selectedInvocation ? selectedInvocation.contents?.global_vars : initial_global_vars;
  const invocationFreeVars = selectedInvocation ? selectedInvocation.contents?.free_vars : initial_free_vars;
  const value = invocationVars?.[var_name] || invocationFreeVars?.[var_name];

  const isGlobal = var_name in invocationVars;
  const isFree = var_name in invocationFreeVars;
  const formattedValue = `${var_name} = ${JSON.stringify(value)?.replace(/"<Object of type ([^>]+)>"/g, '<Object of type $1>')}`;
  
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

const UsedLMPWrapper = ({ uses, children, selectedInvocation, content, }) => {
  const navigate = useNavigate();
  const lmp_name = content.split('(')[0].split(' ')[1];
  const defContent = content.split(lmp_name)[0];
  const signatureContent = content.split(lmp_name)[1];
  const lmp = uses?.find(u => u.name === lmp_name);
  console.log("lmp", lmp, lmp_name);
  console.log("uses", uses);
  if (!lmp) return <>{children}</>;
  return (
    <div className='' style={{ display: 'inline-block', whiteSpace: 'nowrap' }}>
      <OldCard style={{ display: 'inline-block' }} onClick={() => {
        navigate(`/lmp/${lmp.name}/${lmp.lmp_id}`);
      }}>
        <LMPCardTitle 
          lmp={lmp} 
          nameOverride={<CodeHighlighter 
            code={content} 
            showLineNumbers={false} 
            defaultRowPadding='' 
            highlighterStyle={{
              
          padding: '0px 0px 0px 25px',
              backgroundColor: 'transparent',
              border: 'none',
              marginLeft: '5px',
              display: 'inline-block',
                        width: 'unset'
            }} 
          />} 
          displayVersion
          fontSize="md" 
        />
      </OldCard>
    </div>
  );
}


const LMPSourceView = ({ lmp, showDependenciesInitial = false, selectedInvocation = null, previousVersion = null, viewMode }) => {
  const { dependencies : unprocessedDependencies, source, uses, initial_global_vars, initial_free_vars } = lmp;

  const [showDependencies, setShowDependencies] = useState(showDependenciesInitial);
  const [showSource, setShowSource] = useState(true);

  const dependencies = useMemo(() => {
    // Add tags on every single line which begins with def <name> where <name> is the naem of an lmp in iuses
    const procd_deps = unprocessedDependencies.split('\n').map(line => {
      const match = line.match(/^def (\w+)/);
      if (match) {
        // ge tthe lmp name its the function name after the def but before the signature args etc
        const lmp_name = match[1].split('(')[0];
        console.log(lmp_name);
        if (uses.some(u => u.name === lmp_name)) {
          return `# <LMP>\n${line}\n# </LMP>`;
        }
      }
      return line;
    }).join('\n');
    return procd_deps;
  }, [uses, unprocessedDependencies]);

  const trimmedDependencies = dependencies.trim();
  const dependencyLines = trimmedDependencies ? trimmedDependencies.split('\n').length : 0;
  const sourceLines = source.split('\n').length;


  const sourceCodeHooks = useMemo(() => {
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
    startTag: '# <BV>',
    endTag: '# </BV>',
    wrapper: ({children, key, content}) => {
      return <>{children}</>
    }},
    {
      name: 'boundedMutableVariable',
      startTag: '# <BmV>',
      endTag: '# </BmV>',
      wrapper: mutableBVWrapper
    },
    {
      name: 'usedLMP',
      startTag: '# <LMP>',
      endTag: '# </LMP>',
      wrapper: ({children, selectedInvocation, content}) => {
        return <UsedLMPWrapper uses={uses} selectedInvocation={selectedInvocation} content={content}>{children}</UsedLMPWrapper>
      }
    }
  ];
  }, [selectedInvocation, uses]);

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
    <div className="source-code-container text-gray-100">
      {trimmedDependencies && (
        <CodeSection
          title="Dependencies"
          code={trimmedDependencies}
          showCode={showDependencies}
          setShowCode={setShowDependencies}
          lines={dependencyLines}
          isDependent={true}
          customHooks={sourceCodeHooks}
          isDiffView={viewMode === 'Diff'}
          previousCode={previousVersion?.dependencies}
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
        isDiffView={viewMode === 'Diff'}
        previousCode={previousVersion?.source}
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