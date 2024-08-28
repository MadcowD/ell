import React, { useState, useEffect, useMemo } from "react";
import { lstrCleanStringify } from '../../../utils/lstrCleanStringify';
import { CodeSection } from '../../source/CodeSection';
import IORenderer from '../../IORenderer';

const InvocationDataPane = ({ invocation }) => {
  const [inputExpanded, setInputExpanded] = useState(true);
  const [outputExpanded, setOutputExpanded] = useState(true);


  
  const hasKwargs = useMemo(() => {
    return Object.keys(invocation.contents?.params).length > 0;
  }, [invocation.contents?.params]);

  const hasResults = useMemo(() => {
    return Array.isArray(invocation.contents?.results) ? invocation.contents?.results.length > 0 : !!invocation.contents?.results;
  }, [invocation.contents?.results]);



  return (
    <div className="flex-grow p-4 overflow-y-auto w-[fullpx] hide-scrollbar">
      {hasKwargs && (
        <CodeSection
          title="Input"
          raw={JSON.stringify(invocation.contents?.params, null, 2)}
          showCode={inputExpanded}
          setShowCode={setInputExpanded}
          collapsedHeight={'300px'}
          lines={1}
          showLineNumbers={false}
          offset={0}
          enableFormatToggle={false}
          showCopyButton={true}
        >
          <div className="p-4">
            <IORenderer content={invocation.contents?.params} typeMatchLevel={1} inline={false} />
          </div>
        </CodeSection>
      )}

      {hasResults && (
        <CodeSection
          title="Results"
          raw={JSON.stringify(invocation.contents?.results, null, 2)}
          showCode={outputExpanded}
          setShowCode={setOutputExpanded}
          collapsedHeight={'300px'}
          enableFormatToggle={false}
          showCopyButton={true}
          offset={0}
        > 
          <div className="p-4">
            <IORenderer content={invocation.contents?.results} inline={false} />
          </div>
        </CodeSection>
      )}
    </div>
  );
};

export default InvocationDataPane;